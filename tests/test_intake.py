import asyncio,threading,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock
import pytest
from test_api import env,field_session
from server import models
from server.intake import preview_places
from server.scenarios import fact
from server.transport import un64
from server.store import uid
TEXT='There is smoke near City Hall. Two people are outside. I do not know if anyone is still inside. Please send fire support.'
def hnew(h):return dict(h,**{'Idempotency-Key':uid()})
def start(c,h):
 r=c.post('/api/demo/intake',headers=hnew(h),json={});assert r.status_code==200,r.text;return r.json()
def stt(text=TEXT):return {'text':text,'segments':[],'model':'synthetic adapter test','processing_ms':1,'normalized_path':'/nonexistent-test-wav','duration':10}
def audio(c,h,obj,sequence=1,final=False,data=b'actual-test-audio'):
 return c.post('/api/demo/intake/'+obj['id']+'/audio',headers=h,data={'sequence':sequence,'final':str(final).lower()},files={'audio':('live.webm',data,'audio/webm')})
def extraction(text):return models.validate_extraction(text,{'event_type':'smoke','facts':[fact('smoke','Smoke reported','There is smoke near City Hall.','City Hall'),fact('people_inside','Unknown occupancy','I do not know if anyone is still inside.','City Hall',assertion='uncertain')]})

def test_literal_preview_does_not_invent_place_or_event_role():
 assert preview_places('Smoke somewhere')==[]
 assert preview_places('I am near City Hall. Smoke is somewhere else.')[0]['label']=='Los Angeles City Hall'
 assert len(preview_places('City Hall. City Hall.'))==1
 assert any(p['accuracy']=='intersection' for p in preview_places('Main Street is blocked at Temple Street.'))

def test_live_intake_is_operator_only_and_does_not_expose_other_sources(env):
 c,d,h=env;s,fh=field_session(d);obj=start(c,h)
 for path in ['/api/demo/intake/current','/api/demo/intake/'+obj['id']]:assert c.get(path,headers=fh).status_code==403
 assert c.post('/api/demo/intake',headers=fh,json={}).status_code==403
 assert audio(c,fh,obj).status_code==403
 assert c.post('/api/demo/intake/'+obj['id']+'/cancel',headers=fh,json={}).status_code==403
 ordinary=d.manual_draft(s['endpoint_id'],s['id'],'There is smoke somewhere.',[fact('smoke','Smoke','There is smoke somewhere.')])
 assert ordinary['source_id'] not in c.get('/api/demo/intake/current',headers=h).text
 assert c.get('/api/drafts/'+ordinary['id'],headers=h).status_code==403

def test_live_call_reuses_one_demo_session_and_requires_finishing_first(env):
 c,d,h=env;a=start(c,h)
 assert c.post('/api/demo/intake',headers=hnew(h),json={}).status_code==409
 c.post('/api/demo/intake/'+a['id']+'/cancel',headers=hnew(h),json={});b=start(c,h)
 assert a['session_id']==b['session_id'] and len(d.store.list('session'))==1

def test_partial_preview_and_final_review_do_not_dispatch_before_receive(env,monkeypatch):
 c,d,h=env;provider=AsyncMock(return_value=stt());monkeypatch.setattr(models,'transcribe',provider);obj=start(c,h)
 p=audio(c,h,obj);assert p.status_code==200 and p.json()['places'][0]['label']=='Los Angeles City Hall'
 assert not d.store.list('report') and not d.store.list('assignment') and not d.store.list('source')
 assert audio(c,h,obj).status_code==200 and provider.await_count==1
 assert audio(c,h,obj,data=b'different').status_code==409
 final=audio(c,h,obj,2,True).json();job=d.store.get(final['job_id'],'job');source=d.store.get(job['source_id'],'source')
 assert source['text']==TEXT and source['origin_label']=='live demo voice' and provider.await_count==2
 assert c.get('/api/jobs/'+job['id'],headers=h).status_code==403
 assert c.get('/api/source/'+source['id']+'/audio',headers=h).status_code==403
 monkeypatch.setattr(models,'extraction',AsyncMock(side_effect=extraction));assert asyncio.run(d.process_next())
 current=c.get('/api/demo/intake/'+obj['id'],headers=h).json();dr=current['draft']
 assert not d.store.list('assignment')
 body={'version':current['version'],'draft_id':dr['id'],'draft_version':dr['version'],'reviewed':False}
 assert c.post('/api/demo/intake/'+obj['id']+'/send',headers=hnew(h),json=body).status_code==422
 body['reviewed']=True;body['draft_version']=999
 assert c.post('/api/demo/intake/'+obj['id']+'/send',headers=hnew(h),json=body).status_code==409
 body['draft_version']=dr['version'];sent=c.post('/api/demo/intake/'+obj['id']+'/send',headers=hnew(h),json=body);assert sent.status_code==200,sent.text
 assert not d.store.list('report') and not d.store.list('assignment')
 message=d.store.get(sent.json()['message_id'],'message')
 with d.store.transaction():
  for frame in message['frames']:d.transport.receive_frame(un64(frame),message['origin'],message['destination'],time.time())
 assert d.store.get(message['id'],'report')['brief']['location']['label']=='Los Angeles City Hall'
 assert d.store.list('assignment')
 assert c.post('/api/demo/intake/'+obj['id']+'/send',headers=hnew(h),json=body).json()==sent.json()

def test_bad_sequence_size_and_fast_updates_do_not_call_model(env,monkeypatch):
 c,d,h=env;model=AsyncMock(return_value=stt());monkeypatch.setattr(models,'transcribe',model);obj=start(c,h)
 assert audio(c,h,obj,2).status_code==409
 assert audio(c,h,obj,9).status_code==422
 assert audio(c,h,obj,data=b'').status_code==422
 assert model.await_count==0
 assert audio(c,h,obj).status_code==200
 assert audio(c,h,obj,2).status_code==409 and model.await_count==1
 assert audio(c,h,obj,2,True).status_code==200 and model.await_count==2
 assert audio(c,h,obj,3,True).status_code==409

def test_provider_failure_is_explicit_and_never_creates_canned_facts(env,monkeypatch):
 c,d,h=env;monkeypatch.setattr(models,'transcribe',AsyncMock(side_effect=RuntimeError('Synthetic quota failure')));obj=start(c,h);result=audio(c,h,obj,1,True)
 assert result.status_code==200 and result.json()['state']=='failed' and result.json()['error']=='Synthetic quota failure'
 assert not d.store.list('source') and not d.store.list('job') and not d.store.list('report')
 assert Path(d.store.get(obj['id'],'intake')['audio_path']).exists()

def test_cancel_during_transcription_prevents_late_draft_or_pin(env,monkeypatch):
 c,d,h=env;begun=threading.Event()
 async def slow(path):begun.set();await asyncio.sleep(.15);return stt()
 monkeypatch.setattr(models,'transcribe',slow);obj=start(c,h)
 with ThreadPoolExecutor() as pool:
  future=pool.submit(audio,c,h,obj,1,True);assert begun.wait(3)
  assert c.post('/api/demo/intake/'+obj['id']+'/cancel',headers=hnew(h),json={}).status_code==200
  result=future.result(timeout=5)
 assert result.json()['state']=='cancelled' and result.json()['places']==[] and not d.store.list('job')

def test_transcript_revision_preserves_original_and_invalidates_old_review(env,monkeypatch):
 c,d,h=env;monkeypatch.setattr(models,'transcribe',AsyncMock(return_value=stt()));monkeypatch.setattr(models,'extraction',AsyncMock(side_effect=extraction));obj=start(c,h)
 audio(c,h,obj,1,True);asyncio.run(d.process_next());first=c.get('/api/demo/intake/'+obj['id'],headers=h).json();old=first['draft'];source=d.store.get(old['source_id'],'source')
 body={'version':first['version'],'text':TEXT+' Please check the entrance.','reason':'Synthetic correction'}
 changed=c.post('/api/demo/intake/'+obj['id']+'/revise',headers=hnew(h),json=body);assert changed.status_code==200,changed.text
 assert d.store.get(source['id'],'source')['text']==TEXT and d.store.get(old['id'],'draft')['invalidated_by_source']
 assert c.post('/api/demo/intake/'+obj['id']+'/revise',headers=hnew(h),json=body).status_code==409
 assert c.post('/api/demo/intake/'+obj['id']+'/send',headers=hnew(h),json={'version':first['version'],'draft_id':old['id'],'draft_version':old['version'],'reviewed':True}).status_code==409

def test_imperial_distance_units_remain_protected_in_spoken_instructions():
 assert models.instruction_issues('Stay 0.5 miles away.','Stay 0.5 meters away.')
 assert models.instruction_issues('Wait 30 feet from the door.','Wait 30 meters from the door.')
 assert not models.instruction_issues('Stay 0.5 miles away.','Stay 0.5 miles away.')

@pytest.mark.parametrize('held',[False,True])
def test_reviewed_live_event_location_survives_receiver_and_held_location_never_allocates(env,monkeypatch,held):
 c,d,h=env;monkeypatch.setattr(models,'transcribe',AsyncMock(return_value=stt()));monkeypatch.setattr(models,'extraction',AsyncMock(side_effect=extraction));obj=start(c,h)
 audio(c,h,obj,1,True);asyncio.run(d.process_next());current=c.get('/api/demo/intake/'+obj['id'],headers=h).json();dr=current['draft'];source=d.store.get(dr['source_id'],'source')
 body={'version':current['version'],'draft_id':dr['id'],'draft_version':dr['version'],'reviewed':True,'event_location':None if held else d.operations.map.resolve('Union Station')['geo'],'location_unconfirmed':held}
 sent=c.post('/api/demo/intake/'+obj['id']+'/send',headers=hnew(h),json=body);assert sent.status_code==200,sent.text
 assert not d.store.list('assignment') and not d.store.list('report')
 m=d.store.get(sent.json()['message_id'],'message')
 with d.store.transaction():
  for f in m['frames']:d.transport.receive_frame(un64(f),m['origin'],m['destination'],time.time())
 r=d.store.get(m['id'],'report');assert d.store.get(source['id'],'source')['text']==TEXT
 if held:assert r['brief']['location'] is None and not d.store.list('assignment') and d.store.get(r['id'],'plan')['state']=='location_needed'
 else:assert r['brief']['location']['label']=='Union Station' and r['claims'][0]['location']['derivation']=='operator_confirmation' and d.store.list('assignment')

@pytest.mark.parametrize('geo',[{'lon':True,'lat':34.05},{'lon':0,'lat':0},{'lon':-118.24,'lat':'bad'}])
def test_live_location_rejects_invalid_or_out_of_coverage_points(env,monkeypatch,geo):
 c,d,h=env;monkeypatch.setattr(models,'transcribe',AsyncMock(return_value=stt()));monkeypatch.setattr(models,'extraction',AsyncMock(side_effect=extraction));obj=start(c,h);audio(c,h,obj,1,True);asyncio.run(d.process_next());current=c.get('/api/demo/intake/'+obj['id'],headers=h).json();dr=current['draft']
 result=c.post('/api/demo/intake/'+obj['id']+'/send',headers=hnew(h),json={'version':current['version'],'draft_id':dr['id'],'draft_version':dr['version'],'reviewed':True,'event_location':geo})
 assert result.status_code==422 and not d.store.list('report') and not d.store.list('assignment')

def test_already_sent_call_cannot_silently_change_reviewed_event_pin(env,monkeypatch):
 c,d,h=env;monkeypatch.setattr(models,'transcribe',AsyncMock(return_value=stt()));monkeypatch.setattr(models,'extraction',AsyncMock(side_effect=extraction));obj=start(c,h);audio(c,h,obj,1,True);asyncio.run(d.process_next());current=c.get('/api/demo/intake/'+obj['id'],headers=h).json();dr=current['draft'];body={'version':current['version'],'draft_id':dr['id'],'draft_version':dr['version'],'reviewed':True,'event_location':d.operations.map.resolve('City Hall')['geo']}
 assert c.post('/api/demo/intake/'+obj['id']+'/send',headers=hnew(h),json=body).status_code==200
 assert c.post('/api/demo/intake/'+obj['id']+'/send',headers=hnew(h),json={**body,'event_location':d.operations.map.resolve('Union Station')['geo']}).status_code==409
 assert c.post('/api/demo/intake/'+obj['id']+'/send',headers=hnew(h),json={**body,'event_location':['invalid']}).status_code==422

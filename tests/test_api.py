import time,json,hashlib
import pytest
from fastapi.testclient import TestClient
from server.main import create_app
from server.domain import OPERATOR
from server.scenarios import SCENARIOS,fact
from server.store import uid

@pytest.fixture
def env(tmp_path):
 app=create_app(tmp_path,workers=False);d=app.state.domain
 with TestClient(app) as client:
  yield client,d,{'Authorization':'Bearer '+d.secrets['operator_token'],'Idempotency-Key':uid()}

def field_session(d,name='Field A'):
 s=d.create_session(name);return s,{'Authorization':'Bearer '+s['token'],'Idempotency-Key':uid()}

def manual(client,headers,s):
 text='The north gate is blocked.'
 return client.post('/api/drafts/manual',headers=headers,json={'session_id':s['id'],'text':text,'claims':[fact('access','North gate blocked',text,'north gate','access')]}).json()

def test_auth_required(env):
 c,d,h=env;assert c.get('/api/control/snapshot').status_code==403

def test_field_cannot_read_operator(env):
 c,d,h=env;s,fh=field_session(d);assert c.get('/api/control/snapshot',headers=fh).status_code==403

def test_operator_cannot_read_unsent_source(env):
 c,d,h=env;s,fh=field_session(d);dr=manual(c,fh,s)
 assert c.get('/api/drafts/'+dr['id'],headers=h).status_code==403
 assert not c.get('/api/control/snapshot',headers=h).json()['reports']

def test_fields_are_isolated(env):
 c,d,h=env;s,fh=field_session(d);s2,h2=field_session(d,'B');dr=manual(c,fh,s)
 assert c.get('/api/drafts/'+dr['id'],headers=h2).status_code==403
 assert c.post('/api/utterances/text',headers=h2,json={'session_id':s['id'],'text':'hello'}).status_code==403

def test_idempotency_replay_and_conflict(env):
 c,d,h=env;one=c.post('/api/sessions',headers=h,json={'name':'A'});two=c.post('/api/sessions',headers=h,json={'name':'A'})
 assert one.status_code==two.status_code==200 and one.json()['id']==two.json()['id']
 assert c.post('/api/sessions',headers=h,json={'name':'B'}).status_code==409

def test_missing_idempotency(env):
 c,d,h=env;h.pop('Idempotency-Key');assert c.post('/api/sessions',headers=h,json={'name':'A'}).status_code==422

def test_untrusted_origin(env):
 c,d,h=env;h['Origin']='https://untrusted.example';assert c.get('/api/control/snapshot',headers=h).status_code==403

def test_untrusted_host(env):
 c,d,h=env;h['Host']='untrusted.example';assert c.get('/api/health',headers=h).status_code==403

def test_manual_bad_evidence(env):
 c,d,h=env;s,fh=field_session(d)
 assert c.post('/api/drafts/manual',headers=fh,json={'session_id':s['id'],'text':'no smoke','claims':[fact('smoke','smoke','invented')]}).status_code==422

def test_queue_capacity_explicit(env):
 c,d,h=env;s,fh=field_session(d)
 for i in range(50):d.new_job(s['endpoint_id'],s['id'],'inbound',text='hello')
 fh['Idempotency-Key']=uid();r=c.post('/api/utterances/text',headers=fh,json={'session_id':s['id'],'text':'extra'})
 assert r.status_code==429

def test_clip_size_limit(env):
 c,d,h=env;s,fh=field_session(d)
 r=c.post('/api/utterances',headers=fh,data={'session_id':s['id']},files={'audio':('big.wav',b'x'*(10*1024*1024+1),'audio/wav')});assert r.status_code==413

def test_source_correction_invalidates_unsent_draft(env):
 c,d,h=env;s,fh=field_session(d);dr=manual(c,fh,s)
 fh['Idempotency-Key']=uid();r=c.post('/api/sources/'+dr['source_id']+'/text',headers=fh,json={'source_revision':1,'text':'The north gate is clear.','reason':'Corrected misheard word'})
 assert r.status_code==202
 fh['Idempotency-Key']=uid();r=c.post('/api/drafts/'+dr['id']+'/send',headers=fh,json={'version':dr['version']});assert r.status_code==409
 assert d.store.get(dr['source_id'],'source')['text']=='The north gate is blocked.'

def test_same_draft_send_with_distinct_keys_is_same_message(env):
 c,d,h=env;s,fh=field_session(d);dr=manual(c,fh,s);fh['Idempotency-Key']=uid()
 a=c.post('/api/drafts/'+dr['id']+'/send',headers=fh,json={'version':dr['version']});fh['Idempotency-Key']=uid();b=c.post('/api/drafts/'+dr['id']+'/send',headers=fh,json={'version':dr['version']})
 assert a.status_code==b.status_code==200 and a.json()['messages'][0]['id']==b.json()['messages'][0]['id']

def instruction(d,s):
 dr=d.manual_draft(OPERATOR,s['id'],'Do not use the north gate. Is anyone inside?',[],direction='outgoing');dr=d.approve(dr,dr['version']);m=d.send_instruction(dr)[0]
 with d.store.transaction():
  for f in m['frames']:
   from server.transport import un64
   d.transport.receive_frame(un64(f),m['origin'],m['destination'],time.time())
 return dr,m

def test_wrong_destination_cannot_receipt(env):
 c,d,h=env;s,fh=field_session(d);s2,h2=field_session(d,'B');dr,m=instruction(d,s)
 assert c.post('/api/inbox/'+m['id']+'/persisted',headers=h2,json={'body_hash':m['body_hash']}).status_code==403
 assert d.store.get(m['id'],'message')['received_at'] is None

def test_receipt_hash_mismatch(env):
 c,d,h=env;s,fh=field_session(d);dr,m=instruction(d,s)
 assert c.post('/api/inbox/'+m['id']+'/persisted',headers=fh,json={'body_hash':'wrong'}).status_code==409

def test_ack_does_not_answer_question(env):
 c,d,h=env;s,fh=field_session(d);dr,m=instruction(d,s)
 r=c.post('/api/messages/'+m['id']+'/responses',headers=fh,json={'action':'acknowledged'});assert r.status_code==202
 with d.store.transaction():
  from server.transport import un64
  msg=d.store.get(r.json()['id'],'message')
  for f in msg['frames']:d.transport.receive_frame(un64(f),msg['origin'],msg['destination'],time.time())
 assert all(q['state']=='open' for q in d.store.get(m['id'],'inbox')['questions'])

def test_expired_instruction_not_acknowledged(env):
 c,d,h=env;s,fh=field_session(d);dr,m=instruction(d,s)
 with d.store.transaction():m['expires']=time.time()-1;d.store.put('message',m['origin'],m)
 assert c.post('/api/messages/'+m['id']+'/responses',headers=fh,json={'action':'acknowledged'}).status_code==422
 fh['Idempotency-Key']=uid();assert c.post('/api/messages/'+m['id']+'/responses',headers=fh,json={'action':'request_current'}).status_code==202

def test_report_edit_conflict_and_history(env):
 c,d,h=env;s,fh=field_session(d);dr=manual(c,fh,s);m=d.send_report(d.store.get(dr['id'],'draft'))
 with d.store.transaction():
  from server.transport import un64
  for f in m['frames']:d.transport.receive_frame(un64(f),m['origin'],m['destination'],time.time())
 report=d.store.get(m['id'],'report');body={'version':report['version'],'status':'monitoring','reason':'Reviewed source'}
 assert c.patch('/api/reports/'+report['id'],headers=h,json=body).status_code==200
 assert c.patch('/api/reports/'+report['id'],headers=h,json=body).status_code==409
 assert d.store.get(report['id'],'report')['corrections'][0]['reason']=='Reviewed source'

def test_export_excludes_credentials_and_sources(env):
 c,d,h=env;s,fh=field_session(d);dr=manual(c,fh,s);r=c.get('/api/export',headers=h);text=r.text
 assert s['token'] not in text and d.secrets['key'] not in text and dr['source_text'] not in text

def test_reset_requires_exact_phrase(env):
 c,d,h=env;field_session(d)
 assert c.post('/api/demo/reset',headers=h,json={'confirmation':'yes'}).status_code==422
 assert len(d.store.list('session'))==1
 assert c.post('/api/demo/reset',headers=h,json={'confirmation':'RESET SYNTHETIC RUN'}).status_code==200
 assert not d.store.list('session')

@pytest.mark.parametrize('path,body',[('/api/utterances/text',{}),('/api/drafts/manual',[]),('/api/incidents',{}),('/api/drafts/missing/approve',{}),('/api/utterances/text',{'session_id':'x','text':22})])
def test_malformed_request_explicit_422(env,path,body):
 c,d,h=env;assert c.post(path,headers=h,json=body).status_code==422

def test_audio_upload_idempotency(env):
 c,d,h=env;s,fh=field_session(d)
 a=c.post('/api/utterances',headers=fh,data={'session_id':s['id']},files={'audio':('sample.wav',b'synthetic','audio/wav')})
 b=c.post('/api/utterances',headers=fh,data={'session_id':s['id']},files={'audio':('sample.wav',b'synthetic','audio/wav')})
 assert a.status_code==b.status_code==202 and a.json()['id']==b.json()['id']
 assert len(d.store.list('source',s['endpoint_id']))==1

def test_sent_source_correction_carries_target_without_mutating_original(env):
 c,d,h=env;s,fh=field_session(d);dr=manual(c,fh,s);m=d.send_report(d.store.get(dr['id'],'draft'))
 fh['Idempotency-Key']=uid();result=c.post('/api/sources/'+dr['source_id']+'/text',headers=fh,json={'source_revision':1,'text':'The north gate is clear.','reason':'Correction after recheck'})
 assert result.status_code==202
 source=d.store.get(result.json()['source_id'],'source')
 assert source['correction_of']==m['id'] and source['captured_at']==d.store.get(dr['source_id'],'source')['captured_at']
 assert d.store.get(dr['source_id'],'source')['text']=='The north gate is blocked.'

def test_retry_preserves_corrected_source_revision_and_correlation(env):
 c,d,h=env;s,fh=field_session(d);j=d.new_job(s['endpoint_id'],s['id'],'inbound',text='The gate is clear.')
 with d.store.transaction():
  source=d.store.get(j['source_id'],'source');source.update(correction_of=uid(),revision=2);d.store.put('source',s['endpoint_id'],source)
  j.update(state='failed',error='Provider unavailable');d.store.put('job',s['endpoint_id'],j)
 a=c.post('/api/jobs/'+j['id']+'/retry',headers=fh);b=c.post('/api/jobs/'+j['id']+'/retry',headers=fh)
 assert a.status_code==b.status_code==200 and a.json()['id']==b.json()['id']
 assert a.json()['source_id']==source['id'] and len(d.store.list('source'))==1
 assert d.store.get(a.json()['source_id'],'source')['correction_of']==source['correction_of']

from test_api import env,field_session
from server.usc_scenarios import SCENARIOS
from server.transport import un64
from server.usc_atlas import atlas,route
from server.store import uid
import time
import pytest

def received(d,index=0):
 name,text,claims=SCENARIOS[index];s=d.create_session(name);dr=d.manual_draft(s['endpoint_id'],s['id'],text,claims);m=d.send_report(dr)
 with d.store.transaction():
  for f in m['frames']:d.transport.receive_frame(un64(f),m['origin'],m['destination'],time.time())
 return d.store.get(m['id'],'report')
def fresh(h):return {**h,'Idempotency-Key':uid()}
def test_real_campus_geometry_and_resolution_keep_usc_separate(env):
 from server.site import resolve
 c,d,h=env;a=atlas();assert len(a['buildings'])==8 and len(a['edges'])>1000 and len(a['access_points'])>=4
 assert resolve('SGM lab 203')['feature_id']=='usc-sgm';assert resolve('SGM lab 203')['precision']=='building'
 assert resolve('SGM or Kaprielian')['status']=='ambiguous'
 r=received(d);assert r['claims'][0]['location']['feature_id']=='usc-sgm' and not r['claims'][0]['location'].get('geo')
 assert not d.store.list('assignment') and d.store.get(r['id'],'plan')['state']=='campus_facilities'
 assert c.get('/api/usc/operations',headers=h).status_code==200
 _,fh=field_session(d);assert c.get('/api/usc/operations',headers=fh).status_code==403

def test_reported_pressure_history_aggregates_and_escalates_appropriate_team(env):
 c,d,h=env;r=received(d,0);c.get('/api/usc/operations',headers=h);r2=received(d,1);s=c.get('/api/usc/operations',headers=h).json()
 assert len(s['tickets'])==1;t=s['tickets'][0];assert len(t['report_ids'])==2 and t['capability']=='lab_safety' and t['priority']==70
 team=next(u for u in s['teams'] if u['id']==t['team_id']);assert team['capability']=='lab_safety'
 asset=next(a for a in s['assets'] if a['kind']=='pressure');assert [r['value'] for r in asset['readings']]==[145,220] and [r['outside_demo_range'] for r in asset['readings']]==[False,True]
 assert d.store.get(r['id'],'report')['incident_id']==d.store.get(r2['id'],'report')['incident_id']
 assert len(d.store.list('source'))==2 and t['route']['status']=='ready'
 assert c.get('/api/usc/operations',headers=h).json()['tickets'][0]['version']==t['version']

def test_gas_smoke_and_routine_work_use_different_resources_without_false_smoke(env):
 c,d,h=env
 for i in [2,3,4,5]:received(d,i)
 s=c.get('/api/usc/operations',headers=h).json();assert len(s['tickets'])==4
 caps={t['kind']:t['capability'] for t in s['tickets']};assert caps['gas']=='lab_safety' and caps['smoke']=='alarm' and caps['maintenance']=='maintenance'
 t=next(t for t in s['tickets'] if t['kind']=='smoke');r=d.store.get(t['report_ids'][0],'report');assert any(c['assertion']=='negated' and 'cannot see' in c['excerpt'] for c in r['claims'])
 assert next(t for t in s['tickets'] if t['kind']=='gas')['priority']==95

def test_campus_path_block_persists_and_clears_with_versions(env):
 c,d,h=env;received(d,1);s=c.get('/api/usc/operations',headers=h).json();t=s['tickets'][0];edge=t['route']['edge_ids'][len(t['route']['edge_ids'])//2]
 blocked=c.post('/api/usc/closures',headers=fresh(h),json={'edge_id':edge,'state':'blocked','reason':'Synthetic access report: path blocked.'});assert blocked.status_code==200,blocked.text
 s=c.get('/api/usc/operations',headers=h).json();assert edge not in s['tickets'][0]['route']['edge_ids']
 assert c.get('/api/usc/operations',headers=h).json()['closures'][0]['state']=='blocked'
 assert c.post('/api/usc/closures',headers=fresh(h),json={'edge_id':edge,'state':'open','reason':'Walked and confirmed clear.','version':0}).status_code in [409,422]
 clear=c.post('/api/usc/closures',headers=fresh(h),json={'edge_id':edge,'state':'open','reason':'Walked and confirmed clear.','version':blocked.json()['version']});assert clear.status_code==200

def test_facilities_progress_reviewed_access_points_and_manual_report_use_real_transport(env):
 c,d,h=env;received(d,1);s=c.get('/api/usc/operations',headers=h).json();t=s['tickets'][0]
 updated=c.patch('/api/usc/tickets/'+t['id'],headers=fresh(h),json={'version':t['version'],'state':'on_scene','note':'Demo inspection started.'});assert updated.status_code==200,updated.text
 assert c.patch('/api/usc/tickets/'+t['id'],headers=fresh(h),json={'version':t['version'],'state':'resolved','note':'Inspection complete.'}).status_code==409
 done=c.patch('/api/usc/tickets/'+t['id'],headers=fresh(h),json={'version':updated.json()['version'],'state':'resolved','note':'Inspection complete; test valve unchanged.'});assert done.status_code==200
 state=c.get('/api/usc/operations',headers=h).json();assert all(u['status']=='available' for u in state['teams'])
 b=atlas()['buildings'][0];body={'building_id':b['id'],'position':b['center'],'kind':'exit','name':'Synthetic marked exit','source':'Operator knowledge, requires campus verification.'}
 marked=c.post('/api/usc/access-points',headers=fresh(h),json=body);assert marked.status_code==200 and 'not independently verified' in marked.json()['evidence']
 entered=c.post('/api/usc/reports',headers=fresh(h),json={'building_id':'usc-kaprielian','reporter':'Desk','text':'A test light is flickering.'});assert entered.status_code==200 and entered.json()['state']=='queued'
 assert not any(r['reporter_name']=='Desk' for r in d.store.list('report'))
 assert any(m['id']==entered.json()['message_id'] and m['state']=='queued' for m in d.store.list('message'))

@pytest.mark.parametrize("held",[False,True])
def test_live_campus_building_confirmation_allows_delivery_without_city_assignment(env,monkeypatch,held):
 import asyncio
 from unittest.mock import AsyncMock
 from server import models
 from test_intake import start,audio,stt
 c,d,h=env;text=SCENARIOS[1][1]
 monkeypatch.setattr(models,'transcribe',AsyncMock(return_value=stt(text)))
 monkeypatch.setattr(models,'extraction',AsyncMock(side_effect=lambda source:models.validate_extraction(source,{'event_type':'pressure','facts':SCENARIOS[1][2]})))
 call=start(c,h);audio(c,h,call,1,True);assert asyncio.run(d.process_next())
 current=c.get('/api/demo/intake/'+call['id'],headers=h).json();dr=current['draft'];b=atlas()['buildings'][0];geo={'id':b['id'],'label':b['name'],'lon':b['center'][0],'lat':b['center'][1]}
 body={'version':current['version'],'draft_id':dr['id'],'draft_version':dr['version'],'reviewed':True,'event_location':None if held else geo,'location_unconfirmed':held}
 sent=c.post('/api/demo/intake/'+call['id']+'/send',headers=fresh(h),json=body);assert sent.status_code==200,sent.text
 m=d.store.get(sent.json()['message_id'],'message')
 with d.store.transaction():
  for f in m['frames']:d.transport.receive_frame(un64(f),m['origin'],m['destination'],time.time())
 s=c.get('/api/usc/operations',headers=h).json()
 if held:assert not s['tickets'] and not d.store.list('assignment');return
 assert s['tickets'] and s['tickets'][0]['capability']=='lab_safety' and not d.store.list('assignment')
 assert s['tickets'][0]['route']['status']=='ready'

def test_location_hold_never_creates_a_campus_assignment(env):
 c,d,h=env;r=received(d,1)
 # An explicit location hold must override the otherwise recognized campus feature.
 with d.store.transaction():
  r=d.store.get(r['id'],'report')
  for claim in r['claims']:claim['location']['status']='needs_confirmation'
  d.store.put('report','operator',r)
 from server.usc_ops import feature
 assert feature(r) is None

def test_campus_gate_review_persists_and_unknown_pressure_assets_do_not_merge(env):
 c,d,h=env;s=c.get('/api/usc/operations',headers=h).json();g=s['gates'][0]
 assert g['state']=='unreviewed'
 changed=c.patch('/api/usc/gates/'+g['id'],headers=fresh(h),json={'version':g['version'],'state':'blocked','reason':'Synthetic gate inspection: barrier closed.'});assert changed.status_code==200,changed.text
 state=c.get('/api/usc/operations',headers=h).json();assert next(x for x in state['gates'] if x['id']==g['id'])['state']=='blocked';assert state['closures']
 assert c.patch('/api/usc/gates/'+g['id'],headers=fresh(h),json={'version':g['version'],'state':'open','reason':'Stale review.'}).status_code==409
 from server.scenarios import fact
 for tank in ['B12','C14']:
  text='Tank '+tank+' in SGM reads 220 psi.';session=d.create_session('Inspector');draft=d.manual_draft(session['endpoint_id'],session['id'],text,[fact('observation','Reported pressure',text,'SGM')]);m=d.send_report(draft)
  with d.store.transaction():
   for f in m['frames']:d.transport.receive_frame(un64(f),m['origin'],m['destination'],time.time())
 state=c.get('/api/usc/operations',headers=h).json();assert len(state['tickets'])==2 and all(t['asset_id'] is None and t['priority']==25 for t in state['tickets'])

def test_named_campus_path_report_blocks_future_routes_until_a_newer_clearance(env):
 c,d,h=env;received(d,1);c.get('/api/usc/operations',headers=h)
 from server.scenarios import fact
 name=next(e['name'] for e in atlas()['edges'] if e['name']=='Watt Way')
 for word in ['blocked','open and clear']:
  text='At SGM, '+name+' is '+word+'.';session=d.create_session('Access observer');draft=d.manual_draft(session['endpoint_id'],session['id'],text,[fact('access','Access update',text,'SGM','access')]);m=d.send_report(draft)
  with d.store.transaction():
   for f in m['frames']:d.transport.receive_frame(un64(f),m['origin'],m['destination'],time.time())
  state=c.get('/api/usc/operations',headers=h).json();ids={e['id'] for e in atlas()['edges'] if e['name']==name}
  if word=='blocked':
   assert any(cl['edge_id'] in ids and cl['state']=='blocked' for cl in state['closures'])
   assert all(not (set(t['route']['edge_ids'])&ids) for t in state['tickets'] if t['route'])
  else:assert all(cl['state']=='open' for cl in state['closures'] if cl['edge_id'] in ids)

def test_denied_conditions_in_manual_observation_do_not_infer_alarm_or_gas(env):
 c,d,h=env
 from server.scenarios import fact
 text='There is no gas leak and no smoke. A test light is flickering in Kaprielian Hall.';session=d.create_session('Inspector');draft=d.manual_draft(session['endpoint_id'],session['id'],text,[fact('observation','Flickering light',text,'Kaprielian Hall')]);m=d.send_report(draft)
 with d.store.transaction():
  for f in m['frames']:d.transport.receive_frame(un64(f),m['origin'],m['destination'],time.time())
 s=c.get('/api/usc/operations',headers=h).json();assert s['tickets'][0]['kind']=='maintenance' and s['tickets'][0]['priority']==25

def test_explicit_campus_separation_and_relocation_preserve_original_sources(env):
 c,d,h=env;a=received(d,0);b=received(d,1);c.get('/api/usc/operations',headers=h)
 r=d.store.get(b['id'],'report');response=c.post('/api/reports/'+r['id']+'/separate',headers=fresh(h),json={'version':r['version'],'reason':'Separate assets confirmed by inspector.'});assert response.status_code==200,response.text
 state=c.get('/api/usc/operations',headers=h).json();assert len([t for t in state['tickets'] if t['state']!='resolved'])==2
 r=d.store.get(b['id'],'report');claim=next(c for c in r['claims'] if c['kind']=='observation');old_source=d.store.list('source')
 moved=c.patch('/api/reports/'+r['id'],headers=fresh(h),json={'version':r['version'],'claim_id':claim['id'],'feature_id':'usc-kaprielian','reason':'Inspector confirmed the other campus building.'});assert moved.status_code==200,moved.text
 state=c.get('/api/usc/operations',headers=h).json();t=next(t for t in state['tickets'] if b['id'] in t['report_ids']);assert t['building_id']=='usc-kaprielian'
 assert d.store.list('source')==old_source

def test_signed_pressure_reading_is_not_silently_made_positive(env):
 c,d,h=env
 from server.scenarios import fact
 text='The demo nitrogen tank in SGM reads -10 psi.';s=d.create_session('Inspector');dr=d.manual_draft(s['endpoint_id'],s['id'],text,[fact('observation','Pressure reading',text,'SGM')]);m=d.send_report(dr)
 with d.store.transaction():
  for f in m['frames']:d.transport.receive_frame(un64(f),m['origin'],m['destination'],time.time())
 state=c.get('/api/usc/operations',headers=h).json();a=next(a for a in state['assets'] if a['kind']=='pressure');assert a['readings'][-1]['value']==-10 and a['readings'][-1]['outside_demo_range']

def test_seeded_demo_has_nonzero_routes_five_work_items_and_keeps_city_sources(env):
 import copy
 from test_operations import city_report
 c,d,h=env;city=city_report(d);sources=copy.deepcopy(d.store.list('source'))
 seeded=c.post('/api/demo/usc',headers=fresh(h),json={});assert seeded.status_code==200,seeded.text
 for id in seeded.json()['message_ids']:
  m=d.store.get(id,'message')
  with d.store.transaction():
   for f in m['frames']:d.transport.receive_frame(un64(f),m['origin'],m['destination'],time.time())
 state=c.get('/api/usc/operations',headers=h).json();assert len(state['reports'])==6 and len(state['tickets'])==5
 assert all(t['team_id'] and t['route']['status']=='ready' and t['route']['distance_m']>50 and len(t['route']['edge_ids'])>2 for t in state['tickets'])
 assert len({t['team_id'] for t in state['tickets']})==5
 for t in state['tickets']:
  expected={'gas':'safety','smoke':'fire','pressure':'safety','access':'access','maintenance':'service'}[t['kind']]
  assert all(d.store.get(id,'report')['category']==expected for id in t['report_ids'])
 pressure=next(t for t in state['tickets'] if t['kind']=='pressure')
 assert len(pressure['report_ids'])==2 and '220' in pressure['title']
 assert all(d.store.get(s['id'],'source')==s for s in sources)
 assert [r['id'] for r in c.get('/api/control/snapshot?world=city',headers=h).json()['reports']]==[city['id']]
 assert all(u.get('demo_staging',{}).get('note','').startswith('Simulated') for u in state['teams'])
 # Seed is one-shot and does not re-stage or duplicate received cases.
 before=copy.deepcopy(state['teams'])
 assert c.post('/api/demo/usc',headers=fresh(h),json={}).status_code==422
 assert c.get('/api/usc/operations',headers=h).json()['teams']==before

def test_seed_does_not_move_previously_updated_team(env):
 from server.usc_ops import bootstrap
 from server.usc_scenarios import seed_usc
 c,d,h=env;bootstrap(d);u=d.store.list('usc_team')[0]
 u.update(position=[-118.285,34.021],status='unavailable');d.store.put('usc_team','operator',u)
 before=d.store.get(u['id'],'usc_team')
 seed_usc(d)
 assert d.store.get(u['id'],'usc_team')==before

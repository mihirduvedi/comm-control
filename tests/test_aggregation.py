from test_api import env,field_session
from test_operations import city_report
from server.store import uid

def fresh(h):return {**h,'Idempotency-Key':uid()}

def test_matching_fire_reports_share_incident_and_unit_without_erasing_sources(env):
 c,d,h=env;a=city_report(d);b=city_report(d)
 a=d.store.get(a['id'],'report');b=d.store.get(b['id'],'report')
 assert a['incident_id']==b['incident_id'] and len(d.store.list('report'))==2 and len(d.store.list('source'))==2
 incident=d.store.get(a['incident_id'],'incident');assert set(incident['report_ids'])=={a['id'],b['id']}
 assert len(d.store.list('assignment'))==1 and d.store.get(b['id'],'plan')['state']=='assigned'

def test_different_places_and_medical_calls_are_not_automatically_combined(env):
 c,d,h=env;a=city_report(d);b=city_report(d,place='Grand Park');assert a['incident_id']!=b['incident_id']
 m1=city_report(d,1);m2=city_report(d,1);assert not m1['incident_id'] and not m2['incident_id']

def test_separate_is_persistent_and_manual_link_restores_membership(env):
 c,d,h=env;a=city_report(d);b=city_report(d);b=d.store.get(b['id'],'report');incident=d.store.get(b['incident_id'],'incident')
 r=c.post('/api/reports/'+b['id']+'/separate',headers=fresh(h),json={'version':b['version'],'reason':'Different smoke source confirmed.'});assert r.status_code==200,r.text
 assert r.json()['incident_id'] is None and r.json()['aggregation_hold']
 with d.store.transaction():d.operations.on_report(r.json())
 assert d.store.get(b['id'],'report')['incident_id'] is None
 incident=d.store.get(incident['id'],'incident');r=c.post('/api/incidents/'+incident['id']+'/link',headers=fresh(h),json={'version':incident['version'],'report_id':b['id'],'reason':'Caller confirmed same fire.'});assert r.status_code==200,r.text
 assert d.store.get(b['id'],'report')['incident_id']==incident['id']

def test_closing_one_source_retains_shared_response_for_other_open_source(env):
 c,d,h=env;a=city_report(d);b=city_report(d)
 with d.store.transaction():
  a=d.store.get(a['id'],'report');a['status']='resolved';d.store.put('report','operator',a);d.operations.release_report(a['id'])
 active=[x for x in d.store.list('assignment') if x['state']!='released'];assert len(active)==1 and active[0]['report_id']==b['id']

def test_queue_order_is_versioned_operator_only_and_can_return_to_priority(env):
 c,d,h=env;a=city_report(d);b=city_report(d,place='Grand Park');_,fh=field_session(d)
 assert c.get('/api/queue',headers=fh).status_code==403
 assert c.post('/api/queue',headers=fh,json={}).status_code==403
 body={'version':c.get('/api/queue',headers=h).json()['version'],'mode':'manual','order':[b['id'],a['id']]};r=c.post('/api/queue',headers=h,json=body);assert r.status_code==200,r.text
 assert c.get('/api/queue',headers=h).json()['order']==body['order']
 assert c.post('/api/queue',headers=h,json=body).status_code==409
 assert c.post('/api/queue',headers=h,json={'version':r.json()['version'],'mode':'priority','order':[]}).json()['mode']=='priority'

def test_fire_update_with_injury_adds_medical_coverage_to_same_incident(env):
 import time
 from server.scenarios import fact
 from server.transport import un64
 c,d,h=env;first=city_report(d);s=d.create_session('Second observer');text='There is fire at City Hall. One person is injured.';dr=d.manual_draft(s['endpoint_id'],s['id'],text,[fact('fire','Fire reported','There is fire at City Hall.','City Hall'),fact('medical','One injured person','One person is injured.','City Hall',count=1)]);m=d.send_report(dr)
 with d.store.transaction():
  for frame in m['frames']:d.transport.receive_frame(un64(frame),m['origin'],m['destination'],time.time())
 second=d.store.get(m['id'],'report');first=d.store.get(first['id'],'report');assert second['category']=='fire' and second['incident_id']==first['incident_id']
 assert sorted(a['capability'] for a in d.store.list('assignment') if a['state']!='released')==['fire','medical']

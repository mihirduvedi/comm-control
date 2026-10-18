from test_api import env,field_session
from test_operations import city_report
from server.resources import resource_snapshot
from server.store import uid
from server.domain import Domain
from server.scenarios import fact
from server.transport import un64
import time

def fresh(h):return {**h,'Idempotency-Key':uid()}

def test_resources_are_operator_only(env):
 c,d,h=env;_,fh=field_session(d)
 assert c.get('/api/resources',headers=fh).status_code==403
 assert c.post('/api/units',headers=fh,json={}).status_code==403
 assert {k:v for k,v in c.get('/api/resources',headers=h).json()['totals']['fire'].items() if k in ['total','available','allocated','unavailable']}=={'total':2,'available':2,'allocated':0,'unavailable':0}

def test_snapshot_aggregates_actual_allocation_then_releases(env):
 c,d,h=env;r=city_report(d);state=c.get('/api/resources',headers=h).json()
 assert state['totals']['fire']['allocated']==1 and state['totals']['fire']['available']==1
 area=state['areas'][0];assert area['counts']['fire']==1 and area['location']['label']=='Los Angeles City Hall'
 a=state['allocations'][0];assert a['report_id']==r['id'] and a['route']['routes']
 with d.store.transaction():d.operations.release_report(r['id'])
 state=resource_snapshot(d);assert state['allocations']==[] and state['areas']==[] and state['totals']['fire']['available']==2

def test_resource_shortage_means_busy_not_no_route_and_added_unit_serves_waiter(env):
 c,d,h=env
 reports=[city_report(d,place=p) for p in ['City Hall','Grand Park','Japanese American National Museum']]
 state=resource_snapshot(d);assert state['waiting'][0]['shortages']['fire']=='2 fire unit(s) are busy or unavailable.'
 place=d.operations.map.resolve('City Hall')['geo'];body={'name':'Fire Reserve','capability':'fire','place_id':place['id']};headers=fresh(h)
 result=c.post('/api/units',headers=headers,json=body);assert result.status_code==200,result.text
 assert c.post('/api/units',headers=headers,json=body).json()['id']==result.json()['id']
 assert d.store.get(reports[-1]['id'],'plan')['state']=='assigned'
 assert resource_snapshot(d)['totals']['fire']['allocated']==3
 assert c.post('/api/units',headers=fresh(h),json=body).status_code==422
 for invalid in [{**body,'capability':'police'}, {**body,'name':'a'}, {**body,'place_id':'made-up'}]:assert c.post('/api/units',headers=fresh(h),json=invalid).status_code==422

def test_arrival_position_is_operator_marked_not_gps(env):
 c,d,h=env;r=city_report(d);a=d.store.list('assignment')[0];u=d.store.get(a['unit_id'],'unit')
 result=c.patch('/api/units/'+u['id'],headers=h,json={'version':u['version'],'status':'on_scene'});assert result.status_code==200,result.text
 u=result.json();assert u['position_source']=='operator_marked_arrival' and u['position']['lon']==r['brief']['location']['lon']

def received(d,text,kind,value='Concern'):
 s=d.create_session('Synthetic priority');dr=d.manual_draft(s['endpoint_id'],s['id'],text,[fact(kind,value,text,'City Hall')]);m=d.send_report(dr)
 with d.store.transaction():
  for f in m['frames']:d.transport.receive_frame(un64(f),m['origin'],m['destination'],time.time())
 return d.store.get(m['id'],'report')

def test_preemption_audits_unstarted_lower_priority_and_never_diverts_en_route(tmp_path):
 for moving in [False,True]:
  d=Domain(tmp_path/str(moving));prior=received(d,'Someone mentioned a weapon at City Hall.','hazard');a=d.store.list('assignment')[0];assert a['capability']=='safety'
  if moving:
   u=d.store.get(a['unit_id'],'unit')
   with d.store.transaction():d.operations.set_unit(u['id'],{'version':u['version'],'status':'en_route'})
  critical=received(d,'He has a gun and is going to shoot me at City Hall.','violence')
  assert d.store.get(a['id'],'assignment')['state']==('en_route' if moving else 'released')
  assert d.store.get(critical['id'],'plan')['state']==('resource_needed' if moving else 'assigned')
  if not moving:
   plan=d.store.get(prior['id'],'plan');assert plan['state']=='resource_needed' and any(t['kind']=='resource:safety' and t['state']=='open' for t in plan['tasks'])

def test_explicit_operator_priority_survives_automatic_replanning(env):
 c,d,h=env;r=city_report(d,3)
 response=c.patch('/api/reports/'+r['id'],headers=h,json={'version':r['version'],'urgency':'critical','reason':'Operator confirmed an immediate threat by follow-up.'});assert response.status_code==200,response.text
 updated=response.json();assert updated['urgency']=='critical' and updated['triage']['score']==100 and updated['triage']['label']=='Operator priority'
 with d.store.transaction():d.operations.on_report(updated)
 assert d.store.get(r['id'],'report')['urgency']=='critical'

def test_final_policy_migrates_existing_plan_without_duplicate_assignment_or_source_rewrite(env):
 from server.threats import POLICY
 c,d,h=env;r=city_report(d);before=[(s['id'],s['text']) for s in d.store.list('source')];a=d.store.list('assignment')[0]
 with d.store.transaction():
  plan=d.store.get(r['id'],'plan');plan['triage_policy']='old-policy';d.store.put('plan','operator',plan);d.operations.last_tick=0;d.operations.tick()
 assert d.store.get(r['id'],'plan')['triage_policy']==POLICY
 assert len(d.store.list('assignment'))==1 and d.store.list('assignment')[0]['id']==a['id']
 assert [(s['id'],s['text']) for s in d.store.list('source')]==before

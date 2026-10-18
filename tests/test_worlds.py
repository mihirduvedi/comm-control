"""Context isolation through actual received packets, APIs and persistent queues."""
import time,copy
from test_api import env
from test_operations import city_report
from test_usc import received,fresh
from server.scenarios import fact
from server.transport import un64
from server.worlds import report_world

def send(d,world,text,place):
 s=d.create_session('Workspace test',world)
 draft=d.manual_draft(s['endpoint_id'],s['id'],text,[fact('hazard',text,text,place)])
 m=d.send_report(draft)
 with d.store.transaction():
  for frame in m['frames']:d.transport.receive_frame(un64(frame),m['origin'],m['destination'],time.time())
 return d.store.get(m['id'],'report')

def test_scoped_snapshots_exclude_other_world_reports_alerts_and_resources(env):
 c,d,h=env;city=city_report(d);usc=received(d,2);sources=copy.deepcopy(d.store.list('source'))
 for world,expected,other in [('city',city,usc),('usc',usc,city)]:
  state=c.get('/api/control/snapshot?world='+world,headers=h).json()
  assert [r['id'] for r in state['reports']]==[expected['id']]
  assert all(p['report_id']==expected['id'] for p in state['operations']['plans'])
  assert all(a['report_id']==expected['id'] for a in state['operations']['actions'])
  assert other['session_id'] not in [s['id'] for s in state['sessions']]
  if world=='usc':assert state['operations']['units']==[] and state['operations']['closures']==[]
 assert len(c.get('/api/control/snapshot',headers=h).json()['reports'])==2
 assert [r['id'] for r in c.get('/api/usc/operations',headers=h).json()['reports']]==[usc['id']]
 assert c.get('/api/control/snapshot?world=invalid',headers=h).status_code==422
 assert d.store.list('source')==sources

def test_usc_context_with_city_place_or_missing_location_never_allocates_city_units(env):
 c,d,h=env
 r=send(d,'usc','There is smoke at Union Station.','Union Station')
 assert report_world(r)=='usc' and r['world']=='usc'
 assert d.store.get(r['id'],'plan')['state']=='location_needed' and not d.store.list('assignment')
 state=c.get('/api/control/snapshot?world=usc',headers=h).json();assert state['reports'][0]['id']==r['id']
 assert c.get('/api/control/snapshot?world=city',headers=h).json()['reports']==[]
 assert c.get('/api/usc/operations',headers=h).json()['tickets']==[]

def test_city_context_does_not_allocate_campus_team_from_a_foreign_place(env):
 c,d,h=env;r=send(d,'city','A smoke alarm is sounding in Leavey Library.','Leavey Library')
 assert report_world(r)=='city'
 assert c.get('/api/usc/operations',headers=h).json()['tickets']==[]
 assert not d.store.list('assignment')

def test_world_queues_are_independent_versioned_and_reject_cross_world_ids(env):
 c,d,h=env;a=city_report(d);b=received(d)
 for world,report in [('city',a),('usc',b)]:
  q=c.get('/api/queue?world='+world,headers=h).json()
  saved=c.post('/api/queue',headers=fresh(h),json={'world':world,'version':q['version'],'mode':'manual','order':[report['id']]})
  assert saved.status_code==200,saved.text
  assert c.get('/api/queue?world='+world,headers=h).json()['order']==[report['id']]
 q=c.get('/api/queue?world=usc',headers=h).json()
 assert c.post('/api/queue',headers=fresh(h),json={'world':'usc','version':q['version'],'mode':'manual','order':[a['id']]}).status_code==422
 assert c.get('/api/queue?world=city',headers=h).json()['order']==[a['id']]

def test_live_calls_resume_only_in_their_originating_workspace(env):
 c,d,h=env
 city=c.post('/api/demo/intake',headers=fresh(h),json={'world':'city'}).json()
 c.post('/api/demo/intake/'+city['id']+'/cancel',headers=fresh(h),json={})
 usc=c.post('/api/demo/intake',headers=fresh(h),json={'world':'usc'}).json()
 assert usc['session_id']!=city['session_id']
 assert c.get('/api/demo/intake/current?world=city',headers=h).json()['intake'] is None
 assert c.get('/api/demo/intake/current?world=usc',headers=h).json()['intake']['id']==usc['id']
 assert d.session(usc['session_id'])['world']=='usc'

def test_manual_incident_linking_cannot_combine_worlds(env):
 c,d,h=env;a=city_report(d);b=received(d)
 result=c.post('/api/incidents',headers=fresh(h),json={'title':'Mixed worlds','report_ids':[a['id'],b['id']]})
 assert result.status_code==422

def test_explicit_context_survives_source_interpretation_and_session_api(env):
 c,d,h=env
 s=c.post('/api/sessions',headers=fresh(h),json={'name':'Campus technician','world':'usc'}).json()
 assert s['world']=='usc' and d.session(s['id'])['world']=='usc'
 assert s['id'] in [v['id'] for v in c.get('/api/control/snapshot?world=usc',headers=h).json()['sessions']]
 assert s['id'] not in [v['id'] for v in c.get('/api/control/snapshot?world=city',headers=h).json()['sessions']]
 assert c.post('/api/sessions',headers=fresh(h),json={'name':'Invalid','world':'moon'}).status_code==422


def test_scoped_evidence_export_contains_only_the_selected_world(env):
 c,d,h=env;city=city_report(d);usc=received(d)
 for world,expected,excluded in [('city',city,usc),('usc',usc,city)]:
  result=c.get('/api/export?world='+world,headers=h).json()
  assert result['world']==world
  assert [r['id'] for r in result['snapshot']['reports']]==[expected['id']]
  assert all(e['aggregate_id']!=excluded['id'] for e in result['events'])


def test_city_and_campus_session_capacity_are_independent(env):
 c,d,h=env
 for i in range(7):d.create_session('Campus '+str(i),'usc')
 from server.city_scenarios import seed_city
 result=seed_city(d)
 assert len(result['queued'])==4
 assert len([s for s in d.store.list('session') if s.get('world')=='city'])==4
 assert len([s for s in d.store.list('session') if s.get('world')=='usc'])==7


def test_legacy_deep_links_resolve_the_report_context_without_exposing_evidence(env):
 c,d,h=env;r=received(d)
 assert c.get('/api/reports/'+r['id']+'/context').status_code==403
 assert c.get('/api/reports/'+r['id']+'/context',headers=h).json()=={'world':'usc'}
 assert c.get('/api/reports/missing/context',headers=h).status_code==404

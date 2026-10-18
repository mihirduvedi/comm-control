from test_api import env,field_session
from server.scenarios import SCENARIOS
from server.transport import un64
import time

def received(d,index=0):
 name,text,claims=SCENARIOS[index];s=d.create_session(name);dr=d.manual_draft(s['endpoint_id'],s['id'],text,claims);m=d.send_report(dr)
 with d.store.transaction():
  for f in m['frames']:d.transport.receive_frame(un64(f),m['origin'],m['destination'],time.time())
 return d.store.get(m['id'],'report')

def test_campus_graph_resources_avoid_reported_gate_and_remain_separate_from_city(env):
 c,d,h=env;r=received(d);s=c.get('/api/site/operations',headers=h).json()
 assert len(s['units'])==7 and len(d.store.list('unit'))==7 and not d.store.list('assignment')
 assert any(x['feature_id']=='north-gate' and x['state']=='blocked' for x in s['closures'])
 assert s['assignments'] and s['assignments'][0]['unit_name']=='Campus Fire 02'
 assert 'North Gate' not in s['assignments'][0]['route']['steps'] and s['assignments'][0]['route']['distance_plan']>0
 _,fh=field_session(d);assert c.get('/api/site/operations',headers=fh).status_code==403

def test_campus_gate_control_reroutes_and_progress_persists(env):
 c,d,h=env;r=received(d);s=c.get('/api/site/operations',headers=h).json();a=s['assignments'][0];u=next(x for x in s['units'] if x['id']==a['unit_id']);closure=next(x for x in s['closures'] if x['feature_id']=='north-gate')
 result=c.patch('/api/site/gates/north-gate',headers=h,json={'version':closure['version'],'state':'open','reason':'Gate inspected and open.'});assert result.status_code==200,result.text
 assert c.get('/api/site/operations',headers=h).json()['closures'][0]['state']=='open'
 result=c.patch('/api/site/units/'+u['id'],headers=h,json={'version':u['version'],'status':'en_route'});assert result.status_code==200,result.text
 assert c.patch('/api/site/units/'+u['id'],headers=h,json={'version':u['version'],'status':'on_scene'}).status_code==422
 updated=result.json();assert c.patch('/api/site/units/'+u['id'],headers=h,json={'version':updated['version'],'status':'on_scene'}).status_code==200
 s=c.get('/api/site/operations',headers=h).json();arrived=next(x for x in s['units'] if x['id']==u['id']);assert arrived['position']==s['nodes'][a['destination_node']]

def test_campus_automation_pause_and_both_gate_blockages_never_invent_a_path(env):
 c,d,h=env;r=received(d)
 cfg=d.operations.config()
 c.patch('/api/operations/config',headers=h,json={'version':cfg['version'],'auto_assign':False})
 s=c.get('/api/site/operations',headers=h).json();assert not s['assignments'] and any('paused' in w['reason'] for w in s['waiting'])
 cfg=d.operations.config();c.patch('/api/operations/config',headers=h,json={'version':cfg['version'],'auto_assign':True})
 for gate in ['north-gate','south-gate']:
  s=c.get('/api/site/operations',headers=h).json();closure=next(x for x in s['closures'] if x['feature_id']==gate)
  c.patch('/api/site/gates/'+gate,headers=h,json={'version':closure['version'],'state':'blocked','reason':'Both entrances blocked for synthetic test.'})
 s=c.get('/api/site/operations',headers=h).json();assert all(a['route']['status']=='no_route' and not a['route']['coordinates'] for a in s['assignments'])
 u=next(u for u in s['units'] if u['assignment_id']);assert c.patch('/api/site/units/'+u['id'],headers=h,json={'version':u['version'],'status':'en_route'}).status_code==422

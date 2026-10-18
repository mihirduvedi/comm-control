import copy,time
from test_api import env,field_session
from test_operations import city_report
from server.store import uid
from server.transport import un64
from server.dispatch_queue import snapshot,change,queue,advance_all


def headers(h):return {**h,'Idempotency-Key':uid()}
def provider(c,h,world,id):return next(p for p in c.get('/api/dispatch-queues?world='+world,headers=h).json()['providers'] if p['provider_id']==id)
def act(c,h,world,id,action,**body):
 p=provider(c,h,world,id)
 return c.post('/api/dispatch-queues/'+world+'/'+id,headers=headers(h),json={'version':p['version'],'provider_version':p['provider_version'],'action':action,**body})
def city_jobs(d):return [city_report(d,place=x) for x in ['City Hall','Grand Park','Japanese American National Museum']]
def city_unit(d,report):
 a=next(a for a in d.store.list('assignment') if a['report_id']==report['id'] and a['state']!='released')
 return d.store.get(a['unit_id'],'unit')
def campus(d):
 from server.usc_scenarios import seed_usc
 from server.usc_ops import snapshot
 for id in seed_usc(d)['message_ids']:
  m=d.store.get(id,'message')
  with d.store.transaction():
   for f in m['frames']:d.transport.receive_frame(un64(f),m['origin'],m['destination'],time.time())
 with d.store.transaction():return snapshot(d)


def test_queue_endpoint_initializes_a_pristine_campus_without_another_page(env):
 c,d,h=env
 assert d.store.list('usc_team')==[]
 result=c.get('/api/dispatch-queues?world=usc',headers=h)
 assert result.status_code==200 and len(result.json()['providers'])==6
 assert result.json()['targets']==[] and all(p['items']==[] for p in result.json()['providers'])
 assert len(c.get('/api/dispatch-queues?world=city',headers=h).json()['providers'])==7


def test_queues_are_operator_only_and_workspace_scoped(env):
 c,d,h=env;_,fh=field_session(d)
 assert c.get('/api/dispatch-queues',headers=fh).status_code==403
 assert c.get('/api/dispatch-queues?world=elsewhere',headers=h).status_code==422
 u=d.store.list('unit')[0]
 assert c.post('/api/dispatch-queues/usc/'+u['id'],headers=headers(h),json={}).status_code==422
 assert c.post('/api/dispatch-queues/city/'+u['id'],headers=fh,json={}).status_code==403


def test_finish_advances_from_completed_location_and_replay_is_idempotent(env):
 c,d,h=env;jobs=city_jobs(d);u=city_unit(d,jobs[0]);before=copy.deepcopy(d.store.list('source'))
 r=act(c,h,'city',u['id'],'enqueue',target_id=jobs[2]['id']);assert r.status_code==200,r.text
 assert [i['target_id'] for i in r.json()['items']]==[jobs[2]['id']]
 p=provider(c,h,'city',u['id']);body={'version':p['version'],'provider_version':p['provider_version'],'action':'finish','note':'Completed the synthetic fire assessment.'};hs=headers(h)
 r=c.post('/api/dispatch-queues/city/'+u['id'],headers=hs,json=body);assert r.status_code==200,r.text
 assert r.json()['current']['id']==jobs[2]['id'] and not r.json()['items']
 assert c.post('/api/dispatch-queues/city/'+u['id'],headers=hs,json=body).json()==r.json()
 saved=d.store.get(u['id'],'unit');loc=jobs[0]['brief']['location'];assert saved['position']=={'lon':loc['lon'],'lat':loc['lat']} and saved['position_source']=='operator_marked_completion'
 assert d.store.get(jobs[0]['id'],'report')['status']=='open'
 assert d.store.get(jobs[0]['id'],'plan')['state']=='unit_work_finished'
 assert d.store.list('source')==before
 d.operations.last_tick=0
 with d.store.transaction():d.operations.tick()
 assert d.store.get(jobs[0]['id'],'plan')['state']=='unit_work_finished'


def test_manual_reassign_checks_before_detaching_and_supports_added_coverage(env):
 c,d,h=env;jobs=city_jobs(d);u=city_unit(d,jobs[0]);old=u['assignment_id']
 medical=next(p for p in snapshot(d,'city')['providers'] if 'medical' in p['capabilities'])
 assert act(c,h,'city',medical['provider_id'],'reassign',target_id=jobs[1]['id'],target_version=d.store.get(jobs[1]['id'],'report')['version'],note='Wrong capability test.').status_code==422
 result=act(c,h,'city',u['id'],'reassign',target_id=jobs[1]['id'],target_version=d.store.get(jobs[1]['id'],'report')['version'],note='Move a second fire unit to Grand Park.');assert result.status_code==200,result.text
 assert d.store.get(old,'assignment')['state']=='released'
 assert len([a for a in d.store.list('assignment') if a['report_id']==jobs[1]['id'] and a['state']!='released'])==2
 assert d.store.get(jobs[0]['id'],'plan')['assignment_review_required'] is True


def test_new_blockage_holds_next_stop_then_clearance_advances(env):
 c,d,h=env;jobs=city_jobs(d);u=city_unit(d,jobs[0]);assert act(c,h,'city',u['id'],'enqueue',target_id=jobs[2]['id']).status_code==200
 with d.store.transaction():
  d.store.put('closure','operator',{'id':'all-roads','state':'active','edge_ids':list(d.operations.map.edges),'label':'Synthetic all-road closure','coordinates':[],'verification':'test','expires_at':time.time()+1800});d.operations.bump_closures();d.operations.recompute_routes()
 result=act(c,h,'city',u['id'],'finish',note='Work finished; next route is blocked.');assert result.status_code==200,result.text
 assert result.json()['current'] is None and result.json()['hold_reason'] and len(result.json()['items'])==1
 with d.store.transaction():
  closure=d.store.get('all-roads','closure');closure['state']='reopened';d.store.put('closure','operator',closure);d.operations.bump_closures();d.operations.last_tick=0;d.operations.tick()
 assert provider(c,h,'city',u['id'])['current']['id']==jobs[2]['id']
 assignment=d.store.get(d.store.get(u['id'],'unit')['assignment_id'],'assignment');assert assignment['route']['status']=='ready'


def test_paused_queue_waits_and_manual_take_next_works(env):
 c,d,h=env;jobs=city_jobs(d);u=city_unit(d,jobs[0]);act(c,h,'city',u['id'],'enqueue',target_id=jobs[2]['id']);act(c,h,'city',u['id'],'set_enabled',enabled=False)
 result=act(c,h,'city',u['id'],'finish',note='Finished; queue is paused.');assert result.status_code==200 and result.json()['current'] is None
 with d.store.transaction():advance_all(d)
 assert provider(c,h,'city',u['id'])['current'] is None
 result=act(c,h,'city',u['id'],'advance');assert result.status_code==200 and result.json()['current']['id']==jobs[2]['id']


def test_blocked_reassignment_retains_the_original_allocation(env):
 c,d,h=env;jobs=city_jobs(d);u=city_unit(d,jobs[0]);old=u['assignment_id']
 with d.store.transaction():
  d.store.put('closure','operator',{'id':'all-roads','state':'active','edge_ids':list(d.operations.map.edges),'label':'Synthetic closure','coordinates':[],'verification':'test','expires_at':time.time()+1800});d.operations.bump_closures();d.operations.recompute_routes()
 result=act(c,h,'city',u['id'],'reassign',target_id=jobs[2]['id'],target_version=d.store.get(jobs[2]['id'],'report')['version'],note='Try a currently blocked destination.')
 assert result.status_code==422 and d.store.get(u['id'],'unit')['assignment_id']==old and d.store.get(old,'assignment')['state']=='holding'


def test_release_repairs_stale_plan_without_undoing_manual_choice(env):
 c,d,h=env;r=city_report(d);u=city_unit(d,r)
 result=c.patch('/api/units/'+u['id'],headers=h,json={'version':u['version'],'status':'available'});assert result.status_code==200
 plan=d.store.get(r['id'],'plan');assert plan['state']=='resource_needed' and plan['assignment_review_required']
 with d.store.transaction():d.operations.last_tick=0;d.operations.tick()
 assert not [a for a in d.store.list('assignment') if a['state']!='released']
 result=c.post('/api/operations/replan/'+r['id'],headers=headers(h),json={});assert result.status_code==200 and result.json()['state']=='assigned'


def test_saved_queue_survives_new_domain_and_rejects_stale_order(env):
 c,d,h=env;jobs=city_jobs(d);u=city_unit(d,jobs[0]);p=provider(c,h,'city',u['id']);act(c,h,'city',u['id'],'enqueue',target_id=jobs[2]['id'])
 r=c.post('/api/dispatch-queues/city/'+u['id'],headers=headers(h),json={'version':p['version'],'provider_version':p['provider_version'],'action':'remove','target_id':jobs[2]['id']});assert r.status_code==409
 from server.domain import Domain
 reopened=Domain(d.dir);assert queue(reopened,'city',u['id'])['items'][0]['target_id']==jobs[2]['id']


def test_usc_finish_and_reassign_use_same_queue_with_capability_checks(env):
 c,d,h=env;s=campus(d);first=next(t for t in s['tickets'] if t['kind']=='maintenance');team=d.store.get(first['team_id'],'usc_team')
 # Two further real received maintenance reports exhaust capacity and create a waiter.
 from server.usc_ops import snapshot as campus_snapshot
 for building in [b['id'] for b in s['site']['buildings'] if b['code'] in ['ADM','EEB']]:
  created=c.post('/api/usc/reports',headers=headers(h),json={'building_id':building,'reporter':'Queue test','text':'A light is flickering. Please send maintenance.'});assert created.status_code==200,created.text
  m=d.store.get(created.json()['message_id'],'message')
  with d.store.transaction():
   for f in m['frames']:d.transport.receive_frame(un64(f),m['origin'],m['destination'],time.time())
   latest=campus_snapshot(d)
 second=next(t for t in latest['tickets'] if t['kind']=='maintenance' and not t['team_id'])
 r=act(c,h,'usc',team['id'],'enqueue',target_id=second['id']);assert r.status_code==200,r.text
 r=act(c,h,'usc',team['id'],'finish',note='Finished the first campus work item.');assert r.status_code==200,r.text
 assert r.json()['current']['id']==second['id'] and d.store.get(first['id'],'usc_ticket')['state']=='resolved'
 ticket=d.store.get(second['id'],'usc_ticket');assert ticket['route']['status']=='ready'
 gas=next(t for t in s['tickets'] if t['kind']=='gas')
 assert act(c,h,'usc',team['id'],'reassign',target_id=gas['id'],target_version=gas['version'],note='Wrong campus capability.').status_code==422
 assert d.store.get(second['id'],'usc_ticket')['team_id']==team['id']

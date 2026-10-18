import pytest
from test_api import env,field_session
from test_operations import city_report
from server.store import uid

def fresh(h):return dict(h,**{'Idempotency-Key':uid()})

def test_field_cannot_change_dispatch_or_read_routes(env):
 c,d,h=env;s,fh=field_session(d)
 assert c.get('/api/geo',headers=fh).status_code==200
 assert c.post('/api/geo/route',headers=fh,json={}).status_code==403
 assert c.patch('/api/operations/config',headers=fh,json={'version':1,'enabled':False}).status_code==403
 assert c.post('/api/announcements',headers=fh,json={}).status_code==403

def test_new_mutations_require_versions_and_typed_configuration(env):
 c,d,h=env;r=city_report(d);a=d.store.list('announcement')[0]
 assert c.patch('/api/reports/'+r['id']+'/geo',headers=h,json={}).status_code==422
 assert c.post('/api/announcements/'+a['id']+'/publish-demo',headers=h,json={}).status_code==422
 cfg=d.operations.config()
 assert c.patch('/api/operations/config',headers=h,json={'version':cfg['version'],'enabled':'yes'}).status_code==422
 assert c.patch('/api/operations/config',headers=h,json={'version':cfg['version'],'enabled':False}).status_code==200
 assert c.patch('/api/operations/config',headers=h,json={'version':cfg['version'],'enabled':True}).status_code==409

def test_route_rejects_bad_coordinates_and_outside_coverage(env):
 c,d,h=env
 for origin in [{'lon':True,'lat':34},{'lon':181,'lat':34},{'lon':0,'lat':0}]:
  assert c.post('/api/geo/route',headers=h,json={'origin':origin,'destination':{'lon':-118.24,'lat':34.05}}).status_code==422

def test_map_point_keeps_estimated_accuracy_and_rejects_stale_edits(env):
 c,d,h=env;r=city_report(d);body={'version':r['version'],'claim_id':r['claims'][0]['id'],'geo':{'lon':-118.244,'lat':34.053,'accuracy':'operator_estimated'},'reason':'Synthetic approximate point'}
 result=c.patch('/api/reports/'+r['id']+'/geo',headers=h,json=body)
 assert result.status_code==200
 assert result.json()['claims'][0]['location']['geo']['accuracy']=='operator_estimated'
 assert c.patch('/api/reports/'+r['id']+'/geo',headers=h,json=body).status_code==409

def test_closure_and_route_choice_use_current_revision_and_valid_edges(env):
 c,d,h=env;r=city_report(d);a=d.store.list('assignment')[0];body={'version':a['version'],'route_id':a['route']['routes'][0]['id'],'closure_revision':a['route']['closure_revision']}
 assert c.patch('/api/assignments/'+a['id']+'/route',headers=h,json=body).status_code==200
 assert c.post('/api/closures',headers=fresh(h),json={'edge_ids':['invented'],'reason':'Test'}).status_code==422
 edge=a['route']['routes'][0]['edge_ids'][0]
 result=c.post('/api/closures',headers=fresh(h),json={'edge_ids':[edge],'reason':'Synthetic blockage'});assert result.status_code==200
 assert c.patch('/api/assignments/'+a['id']+'/route',headers=h,json=body).status_code==409
 closure=result.json()
 assert c.patch('/api/closures/'+closure['id'],headers=h,json={'version':closure['version'],'state':'reopened','reason':'Synthetic clearance'}).status_code==200
 assert edge not in d.operations.excluded()

def test_advisory_requires_approval_and_publishes_only_local_record(env):
 c,d,h=env;r=city_report(d);a=d.store.list('announcement')[0]
 assert c.post('/api/announcements/'+a['id']+'/publish-demo',headers=fresh(h),json={'version':a['version']}).status_code==409
 approved=c.post('/api/announcements/'+a['id']+'/approve',headers=h,json={'version':a['version'],'text':'Demonstration message.','audience':'Public demo board'});assert approved.status_code==200
 result=c.post('/api/announcements/'+a['id']+'/publish-demo',headers=fresh(h),json={'version':approved.json()['version']});assert result.status_code==200 and result.json()['state']=='published_demo'
 assert not d.store.list('message','external')

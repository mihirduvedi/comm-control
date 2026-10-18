"""Real-map/automation decisions with synthetic incidents; no external dispatch."""
import json,time
import pytest
from server.domain import Domain
from server.geography import atlas,Atlas,point
from server.city_scenarios import CITY_SCENARIOS
from server.scenarios import fact
from server.store import uid
from server.transport import un64
from test_core import configure,deliver

def city_report(d,index=0,place=None):
 name,text,claims=CITY_SCENARIOS[index]
 if place:
  original='City Hall' if index==0 else 'Union Station'
  text=text.replace(original,place);claims=[{**c,'excerpt':c['excerpt'].replace(original,place),'location_text':c['location_text'].replace(original,place)} for c in claims]
 s=d.create_session(name);draft=d.manual_draft(s['endpoint_id'],s['id'],text,claims);m=d.send_report(draft)
 with d.store.transaction():
  for frame in m['frames']:d.transport.receive_frame(un64(frame),m['origin'],m['destination'],time.time())
 return d.store.get(m['id'],'report')

@pytest.fixture
def d(tmp_path):return Domain(tmp_path)

@pytest.mark.parametrize('name',['City Hall','Union Station','Grand Park','Main Street and Temple Street','Japanese American National Museum'])
def test_real_locations_resolve_from_osm(name):
 r=atlas().resolve(name);assert r['geo'] and r['geo']['source']=='OpenStreetMap' and -118.3<r['geo']['lon']<-118.2

def test_vague_location_stays_unlocated():
 assert atlas().resolve('over there')['geo'] is None
 assert atlas().resolve('warehouse')['geo'] is None

def test_route_excludes_closed_segment_and_offers_real_detour():
 a=atlas();origin=[-118.2473,34.0467];dest=point(a.resolve('City Hall')['geo']);base=a.route(origin,dest);assert base['status']=='ready'
 blocked=base['routes'][0]['edge_ids'][len(base['routes'][0]['edge_ids'])//2];detour=a.route(origin,dest,{blocked});assert detour['status']=='ready'
 assert all(blocked not in r['edge_ids'] for r in detour['routes'])
 assert detour['routes'][0]['edge_ids']!=base['routes'][0]['edge_ids']

def test_no_path_never_returns_straight_line_navigation():
 a=atlas();r=a.route([-118.2473,34.0467],point(a.resolve('City Hall')['geo']),set(a.edges));assert r['status']=='no_route' and r['routes']==[]

def test_outside_coverage_explains_limit():
 with pytest.raises(ValueError,match='outside'):atlas().route([0,0],[-118.24,34.05])

def test_reported_blocked_subject_is_main_not_cross_street():
 a=atlas();near=a.resolve('Main Street and Temple Street')['geo'];edges=a.closure_edges('Main Street is blocked at Temple Street.',near)
 assert edges and all('Main Street' in a.edges[k]['name'] for k in edges)
 assert not a.closure_edges('A road is blocked around Main Street and Temple Street.',near)

def test_receive_drives_category_route_assignment_and_review(d):
 r=city_report(d);plan=d.store.get(r['id'],'plan');a=d.store.list('assignment')[0]
 assert r['category']=='fire' and r['brief']['location']['label']=='Los Angeles City Hall'
 assert a['capability']=='fire' and a['route']['status']=='ready'
 assert any(t['kind']=='uncertainty' for t in plan['tasks']) and any(t['kind']=='supervisor' for t in plan['tasks'])
 assert 'inside?' in plan['caller_draft'];assert all(a['state']=='draft' for a in d.store.list('announcement'))

def test_units_not_double_assigned_when_resources_exhausted(d):
 reports=[city_report(d,place=p) for p in ['City Hall','Grand Park','Japanese American National Museum']];assignments=d.store.list('assignment');assert len(assignments)==2 and len({a['unit_id'] for a in assignments})==2
 assert d.store.get(reports[-1]['id'],'plan')['state']=='resource_needed'

def test_duplicate_received_packet_does_not_duplicate_actions(d):
 r=city_report(d);m=d.store.get(r['id'],'message');before=len(d.store.list('action'))
 with d.store.transaction():
  for frame in reversed(m['frames']):d.transport.receive_frame(un64(frame),m['origin'],m['destination'],time.time())
 assert len(d.store.list('assignment'))==1 and len(d.store.list('action'))==before

def test_reported_closure_recomputes_assignment(d):
 r=city_report(d);a=d.store.list('assignment')[0];before=a['route']['routes'][0]['edge_ids'];blocked=before[len(before)//2];edge=d.operations.map.edges[blocked]
 with d.store.transaction():
  d.store.put('closure','operator',{'id':uid(),'state':'active','edge_ids':[blocked],'expires_at':time.time()+1800,'label':edge['name'],'verification':'reported','coordinates':[edge['coordinates']]});d.operations.bump_closures();d.operations.recompute_routes()
 new=d.store.get(a['id'],'assignment');assert all(blocked not in r['edge_ids'] for r in new['route']['routes']);assert new['route']['closure_revision']==1

def test_stale_closure_is_not_silently_reopened(d):
 r=city_report(d,2);c=d.store.list('closure')[0]
 with d.store.transaction():
  c['expires_at']=time.time()-1;d.store.put('closure','operator',c);d.operations.tick()
 assert d.store.get(c['id'],'closure')['state']=='stale'
 assert set(c['edge_ids']).issubset(d.operations.excluded())

def test_demo_advisory_needs_exact_wording_and_audience_approval(d):
 r=city_report(d)
 with d.store.transaction():a=d.operations.advisory(r['id'])
 with pytest.raises(Exception):
  with d.store.transaction():d.operations.publish_advisory(a['id'],a['version'])
 with d.store.transaction():a=d.operations.approve_advisory(a['id'],{'version':a['version'],'text':a['text'],'audience':a['audience']})
 with d.store.transaction():done=d.operations.publish_advisory(a['id'],a['version'])
 assert done['state']=='published_demo';assert not d.store.list('message', 'external')
 assert d.operations.publish_advisory(a['id'],done['version'])['id']==a['id']

def test_caller_position_does_not_locate_event(d):
 s=d.create_session('Remote caller');text='I am at City Hall. There is smoke somewhere.';draft=d.manual_draft(s['endpoint_id'],s['id'],text,[fact('reporter_location','At City Hall','I am at City Hall.','City Hall','reporter'),fact('smoke','Smoke somewhere','There is smoke somewhere.')]);m=d.send_report(draft)
 with d.store.transaction():
  for f in m['frames']:d.transport.receive_frame(un64(f),m['origin'],m['destination'],time.time())
 r=d.store.get(m['id'],'report');assert r['brief']['location'] is None and not d.store.list('assignment')

def test_real_place_changes_block_instruction_approval():
 from server.models import instruction_issues
 assert instruction_issues('At City Hall, wait for a reply.','At Union Station, wait for a reply.')
 assert not instruction_issues('At City Hall, stay outside. Do not use Main Street.','At City Hall, stay outside. Do not use Main Street.')

def test_released_unit_is_automatically_reconsidered_for_waiting_case(d):
 reports=[city_report(d,place=p) for p in ['City Hall','Grand Park','Japanese American National Museum']];unit=d.store.list('unit')[1]
 unit=next(u for u in d.store.list('unit') if u['status']=='assigned' and 'fire' in u['capabilities'])
 with d.store.transaction():d.operations.set_unit(unit['id'],{'version':unit['version'],'status':'available'});d.operations.tick()
 waiting=d.store.get(reports[-1]['id'],'plan');assert waiting['state']=='assigned'
 assert all(t['state']!='open' for t in waiting['tasks'] if t['kind'].startswith('resource:'))

def test_changed_incident_invalidates_advisory_approval(d):
 r=city_report(d)
 with d.store.transaction():
  a=d.operations.advisory(r['id']);a=d.operations.approve_advisory(a['id'],{'version':a['version'],'text':a['text'],'audience':a['audience']})
  r['claims'][0]['value']='Changed report';d.store.put('report','operator',r)
 with pytest.raises(Exception,match='Incident details changed'):
  with d.store.transaction():d.operations.publish_advisory(a['id'],a['version'])

def test_no_route_holds_unit_and_blocks_marking_en_route(d):
 r=city_report(d);a=d.store.list('assignment')[0]
 with d.store.transaction():
  d.store.put('closure','operator',{'id':uid(),'state':'active','edge_ids':list(d.operations.map.edges),'label':'Test all roads','verification':'synthetic','expires_at':time.time()+1800});d.operations.bump_closures();d.operations.recompute_routes()
 u=d.store.get(a['unit_id'],'unit');assert u['status']=='holding' and d.store.get(a['id'],'assignment')['route']['status']=='no_route'
 with pytest.raises(ValueError,match='No supported route'):
  with d.store.transaction():d.operations.set_unit(u['id'],{'version':u['version'],'status':'en_route'})

def tiny_atlas(restriction=None,oneway='no'):
 elements=[{'type':'node','id':i,'lon':x,'lat':y} for i,x,y in [(1,0,0),(2,.001,0),(3,.002,0),(4,.001,.001),(5,.002,.001)]]
 elements += [{'type':'way','id':10,'nodes':[1,2,3],'tags':{'name':'Main Street','highway':'residential','oneway':oneway}},{'type':'way','id':20,'nodes':[2,4,5,3],'tags':{'name':'Side Street','highway':'residential'}}]
 if restriction:elements.append({'type':'relation','id':30,'members':[{'role':'from','type':'way','ref':10},{'role':'to','type':'way','ref':10 if restriction=='no_u_turn' else 20},{'role':'via','type':'node','ref':2}],'tags':{'type':'restriction','restriction':restriction}})
 return Atlas({'elements':elements})

def test_one_way_and_turn_restrictions_are_applied():
 a=tiny_atlas(oneway='yes');assert a.route([.002,0],[0,0])['status']=='no_route'
 a=tiny_atlas('no_left_turn');blocked='10:2:3';assert a.route([0,0],[.002,0],{blocked})['status']=='no_route'
 a=tiny_atlas('no_u_turn');r=a.route([0,0],[.002,0]);assert r['status']=='ready' and r['routes'][0]['edge_ids']==['10:1:2','10:2:3']

def test_negated_hazard_does_not_create_an_unrequested_assignment(d):
 s=d.create_session('Verification');text='There is no fire at City Hall.';draft=d.manual_draft(s['endpoint_id'],s['id'],text,[fact('fire','No fire',text,'City Hall',assertion='negated')]);m=d.send_report(draft)
 with d.store.transaction():
  for f in m['frames']:d.transport.receive_frame(un64(f),m['origin'],m['destination'],time.time())
 assert d.store.get(m['id'],'plan')['state']=='information_only' and not d.store.list('assignment')

def road_report(d,text,assertion='asserted',place='Main Street and Temple Street'):
 s=d.create_session('Road verification');dr=d.manual_draft(s['endpoint_id'],s['id'],text,[fact('access',text,text,place,'access',assertion=assertion)]);m=d.send_report(dr)
 with d.store.transaction():
  for f in m['frames']:d.transport.receive_frame(un64(f),m['origin'],m['destination'],time.time())
 return d.store.get(m['id'],'report')

def test_future_incident_avoids_prior_blockage_until_explicit_clearance(d):
 blocked=road_report(d,'Main Street is blocked at Temple Street.');closure=d.store.list('closure')[0];keys=set(closure['edge_ids']);assert keys
 future=city_report(d);a=next(a for a in d.store.list('assignment') if a['report_id']==future['id']);assert all(not keys.intersection(r['edge_ids']) for r in a['route']['routes'])
 with d.store.transaction():
  closure['expires_at']=time.time()-1;d.store.put('closure','operator',closure);d.operations.last_tick=0;d.operations.tick()
 assert keys<=d.operations.excluded() # Expiry prompts review, never clears the road.
 road_report(d,'Main Street is clear at Temple Street.','hearsay');assert keys<=d.operations.excluded()
 road_report(d,'Temple Street is clear at Main Street.');assert keys<=d.operations.excluded() # Crossing street is different.
 road_report(d,'Main Street is clear at Temple Street.')
 closed=d.store.get(closure['id'],'closure');assert closed['state']=='reopened' and closed['cleared_by_report'] and not keys.intersection(d.operations.excluded())
 assert d.store.get(a['id'],'assignment')['route']['closure_revision']>a['route']['closure_revision']

def test_old_clearance_does_not_reopen_newer_blockage(d):
 r=road_report(d,'Main Street is blocked at Temple Street.');closure=d.store.list('closure')[0]
 # An explicit earlier observation cannot override a newer closure.
 with d.store.transaction():
  r['observed_at']=time.time()+30;d.store.put('report','operator',r)
 road_report(d,'Main Street is clear at Temple Street.')
 assert d.store.get(closure['id'],'closure')['state']=='active'

def test_reopening_restores_route_but_does_not_silently_move_a_held_unit(d):
 r=city_report(d);a=d.store.list('assignment')[0]
 with d.store.transaction():
  c=d.store.put('closure','operator',{'id':uid(),'state':'active','edge_ids':list(d.operations.map.edges),'label':'Synthetic all-roads closure','verification':'synthetic','expires_at':time.time()+1800});d.operations.bump_closures();d.operations.recompute_routes()
  c['state']='reopened';d.store.put('closure','operator',c);d.operations.bump_closures();d.operations.recompute_routes()
 assert d.store.get(a['id'],'assignment')['route']['status']=='ready'
 assert d.store.get(a['unit_id'],'unit')['status']=='holding'
 plan=d.store.get(r['id'],'plan');assert plan['state']=='assigned' and any(t['kind']=='route_restored' and t['state']=='open' for t in plan['tasks'])

def test_clearance_wording_and_hearsay_guard(d):
 r=road_report(d,'Main Street is blocked at Temple Street.');c=d.store.list('closure')[0]
 road_report(d,'I heard Main Street is clear at Temple Street.')
 assert d.store.get(c['id'],'closure')['state']=='active'
 road_report(d,'Main Street has been cleared at Temple Street.')
 assert d.store.get(c['id'],'closure')['state']=='reopened'

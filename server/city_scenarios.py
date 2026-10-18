"""Manual synthetic incident inputs at real public OSM landmarks. No live incident claims."""
from .scenarios import fact
CITY_SCENARIOS=[
 ('Alex Rivera',"There is smoke near City Hall. Two people are outside. I don't know if anyone is still inside. Please send fire support.",[
  fact('smoke','Smoke reported near City Hall','There is smoke near City Hall.','City Hall'),fact('people_outside','Two people outside','Two people are outside.','City Hall',count=2),fact('people_inside','Occupancy inside unknown',"I don't know if anyone is still inside.",'City Hall',assertion='uncertain'),fact('request','Fire support requested','Please send fire support.','City Hall')]),
 ('Jamie Chen','One person is injured at Union Station. We need medical help now.',[
  fact('observation','One injured person','One person is injured at Union Station.','Union Station',count=1),fact('request','Medical help requested','We need medical help now.','Union Station'),fact('event_time','Now','now','Union Station')]),
 ('Sam Okafor','Main Street is blocked at Temple Street. A truck is obstructing the intersection.',[
  fact('access','Main Street blocked at Temple Street','Main Street is blocked at Temple Street.','Main Street and Temple Street','access'),fact('observation','Truck obstructing intersection','A truck is obstructing the intersection.','Main Street and Temple Street')]),
 ('Taylor Brooks','Please send maintenance to the Japanese American National Museum. The loading door will not close.',[
  fact('request','Maintenance requested','Please send maintenance to the Japanese American National Museum.','Japanese American National Museum'),fact('observation','Loading door will not close','The loading door will not close.','Japanese American National Museum')])]
def seed_city(d):
 prior=d.store.get('city-demo','scenario')
 if prior:return prior
 from .worlds import session_world
 if sum(session_world(d,s)=='city' for s in d.store.list('session'))+len(CITY_SCENARIOS)>100:raise ValueError('Four city session slots are needed. Use an existing city run or start a new test.')
 queued=[]
 for name,text,claims in CITY_SCENARIOS:
  s=d.create_session(name,'city');draft=d.manual_draft(s['endpoint_id'],s['id'],text,claims)
  with d.store.transaction():draft['origin_label']='annotated city demo';draft=d.store.put('draft',s['endpoint_id'],draft)
  m=d.send_report(draft);queued.append({'session_id':s['id'],'message_id':m['id']})
 with d.store.transaction():return d.store.put('scenario','operator',{'id':'city-demo','queued':queued,'label':'Synthetic incidents at real public places. AI was not run. Demo units and road reports are fictional.'},event='city_demo_queued')

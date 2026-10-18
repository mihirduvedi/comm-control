"""Live projection of persisted demo resources and allocations. No real GPS or dispatch."""
from .store import uid,now
from .threats import assess_report
from .operations import CATEGORIES
CAPABILITIES=['medical','fire','safety','traffic','general']

def resource_snapshot(d):
 from .worlds import report_world
 op=d.operations.snapshot();reports={r['id']:r for r in d.store.list('report','operator') if report_world(r)=='city'};units={u['id']:u for u in op['units']};allocations=[];areas={}
 for a in op['assignments']:
  if a['state']=='released':continue
  report=reports.get(a['report_id']);unit=units.get(a['unit_id'])
  if not report or not unit:continue
  location=report.get('brief',{}).get('location')
  row={**a,'unit_name':unit['name'],'report_summary':report['summary'],'urgency':report['urgency'],'priority':assess_report(report)['score'],'destination':location,'position':unit['position'],'position_source':unit.get('position_source','simulated_base')};allocations.append(row)
  if location:
   key=location.get('id') or location['label'];area=areas.setdefault(key,{'id':key,'location':location,'counts':{cap:0 for cap in CAPABILITIES},'assignment_ids':[],'report_ids':[]});area['counts'][a['capability']]+=1;area['assignment_ids'].append(a['id'])
   from .aggregation import members
  for member in members(d,report):
   if member['id'] not in area['report_ids']:area['report_ids'].append(member['id'])
 totals={cap:{'total':sum(cap in u['capabilities'] for u in units.values()),'available':sum(cap in u['capabilities'] and u['status']=='available' for u in units.values()),'allocated':sum(a['capability']==cap for a in allocations),'unavailable':sum(cap in u['capabilities'] and u['status']=='unavailable' for u in units.values())} for cap in CAPABILITIES}
 waiting=[]
 for plan in op['plans']:
  report=reports.get(plan['report_id'])
  if report and report['status'] not in ['resolved','superseded'] and plan['state'] in ['resource_needed','location_needed','route_blocked','automation_paused']:
   waiting.append({'report_id':report['id'],'summary':report['summary'],'priority':assess_report(report)['score'],'state':plan['state'],'location':report.get('brief',{}).get('location'),'shortages':plan.get('shortages',{}),'capability':CATEGORIES[report.get('category','service')]['capability'],'reason':next((t['reason'] for t in plan['tasks'] if t['state']=='open'),'Review response plan')})
 for cap,total in totals.items():
  total['states']={state:sum(cap in u['capabilities'] and u['status']==state for u in units.values()) for state in ['assigned','en_route','on_scene','holding']}
  total['waiting']=sum(cap in w['shortages'] or w['state']=='resource_needed' and w['capability']==cap for w in waiting)
 summary={'total':len(units),'available':sum(u['status']=='available' for u in units.values()),'allocated':len(allocations),'en_route':sum(u['status']=='en_route' for u in units.values()),'on_scene':sum(u['status']=='on_scene' for u in units.values()),'holding':sum(u['status']=='holding' for u in units.values()),'unavailable':sum(u['status']=='unavailable' for u in units.values()),'location_needed':sum(w['state']=='location_needed' for w in waiting),'resource_needed':sum(w['state'] in ['resource_needed','route_blocked'] for w in waiting),'blocked_roads':sum(c['state'] in ['active','stale'] for c in op['closures'])}
 activity=sorted([a for a in op['actions'] if a.get('report_id') in reports and a['kind'].startswith(('assigned:','reprioritized:','rerouted','route_restored','cleared:'))],key=lambda a:a['at'],reverse=True)[:8]
 return {'at':now(),'summary':summary,'activity':activity,'mode':'Live demo allocation state; no real vehicle telemetry','totals':totals,'units':list(units.values()),'allocations':allocations,'areas':list(areas.values()),'waiting':sorted(waiting,key=lambda r:-r['priority']),'closures':op['closures'],'atlas':op['atlas'],'tile_url':op['config']['tile_url'],'automation':op['config']}

def register_resources(app,d,operator,json_body,idem):
 from fastapi import Depends,Request
 @app.get('/api/resources')
 def resources(a=Depends(operator)):return resource_snapshot(d)
 @app.post('/api/units')
 async def add_unit(request:Request,a=Depends(operator)):
  body=await json_body(request);name=body.get('name','');cap=body.get('capability');place=body.get('place_id','')
  if not isinstance(name,str) or not 2<=len(name.strip())<=40:raise ValueError('Enter a unit name between 2 and 40 characters.')
  if cap not in CAPABILITIES:raise ValueError('Choose a supported demo capability.')
  location=next((p for p in d.operations.map.places if p['id']==place),None)
  if not location:raise ValueError('Choose a known Downtown LA base location.')
  def create():
   with d.store.transaction():
    if len(d.store.list('unit'))>=40:raise ValueError('The demo roster is limited to 40 units.')
    if any(u['name'].casefold()==name.strip().casefold() for u in d.store.list('unit')):raise ValueError('That unit name is already in use.')
    unit=d.store.put('unit','operator',{'id':uid(),'name':name.strip(),'capabilities':[cap],'status':'available','position':{'lon':location['lon'],'lat':location['lat']},'position_source':'simulated_base','assignment_id':None,'demo':True},event='demo_unit_added');d.operations.last_tick=0;d.operations.tick();return d.store.get(unit['id'],'unit')
  return idem(request,a,body,create)

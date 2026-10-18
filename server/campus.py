"""Authored fictional campus graph and separate demo responders. No real coordinates/ETA."""
import hashlib,json,math,heapq
from .store import uid,now
from .operations import stable,CATEGORIES
from .site import sitepack,BY_ID
from .threats import assess_report
NODES={'north-out':[515,65],'north-in':[515,130],'center-top':[515,175],'west-top':[150,175],'east-top':[850,175],'west-mid':[150,480],'east-mid':[850,380],'west-bottom':[150,550],'center-bottom':[515,550],'east-bottom':[850,550],'south-in':[515,610],'south-out':[515,665],'outer-top':[900,65],'outer-bottom':[900,665],'east-door':[700,380],'west-door':[300,480],'office-door':[380,175],'yard-door':[600,550]}
LINKS=[('north-out','north-in','North Gate','north-gate'),('north-in','center-top','Central service road',None),('center-top','center-bottom','Central service road',None),('center-bottom','south-in','Central service road',None),('south-in','south-out','South Gate','south-gate'),('center-top','west-top','North service road',None),('center-top','east-top','North service road',None),('west-top','west-mid','West service road',None),('west-mid','west-bottom','West service road',None),('west-bottom','center-bottom','South service road',None),('center-bottom','east-bottom','South service road',None),('east-top','east-mid','East service road',None),('east-mid','east-bottom','East service road',None),('east-mid','east-door','East loading approach',None),('west-mid','west-door','West loading approach',None),('center-top','office-door','Office approach',None),('center-bottom','yard-door','Yard approach',None),('north-out','outer-top','Perimeter road',None),('outer-top','outer-bottom','Perimeter road',None),('outer-bottom','south-out','Perimeter road',None)]
DEST={'east-warehouse':'east-door','east-loading':'east-door','west-warehouse':'west-door','west-loading':'west-door','operations':'office-door','yard':'yard-door','north-gate':'north-in','south-gate':'south-in'}
ROSTER=[('Campus Fire 01','fire','north-out'),('Campus Fire 02','fire','south-out'),('Campus Medic 01','medical','south-out'),('Campus Medic 02','medical','north-out'),('Campus Access 01','traffic','south-out'),('Campus Safety 01','safety','south-out'),('Campus Support 01','general','south-out')]

def route(origin,destination,blocked):
 queue=[(0,origin,[])];seen=set()
 while queue:
  distance,node,path=heapq.heappop(queue)
  if node in seen:continue
  seen.add(node)
  if node==destination:return {'status':'ready','coordinates':[NODES[n] for n in [origin]+[e[1] for e in path]],'steps':[e[2] for e in path],'distance_plan':round(distance),'note':'Authored site-plan route. Drawing units are not meters; no travel time or live traffic.'}
  for a,b,name,gate in LINKS:
   if gate in blocked:continue
   other=b if node==a else a if node==b else None
   if other and other not in seen:heapq.heappush(queue,(distance+math.dist(NODES[node],NODES[other]),other,path+[(node,other,name)]))
 return {'status':'no_route','coordinates':[],'steps':[],'distance_plan':0,'note':'No open path on the fictional campus. Review the blocked gates.'}

def event_feature(report):
 return next((c['location']['feature_id'] for c in report['claims'] if c['location']['role']!='reporter' and c['location'].get('status')!='needs_confirmation' and c['location'].get('feature_id') in DEST and c['assertion'] not in ['negated','hypothetical']),None)

def snapshot(d):
 for name,cap,base in ROSTER:
  id=stable('campus:'+name)
  if not d.store.get(id,'site_unit'):d.store.put('site_unit','operator',{'id':id,'name':name,'capability':cap,'node':base,'base':base,'status':'available','assignment_id':None},event='campus_unit_created')
 for gate in ['north-gate','south-gate']:
  if not d.store.get(stable('campus-closure:'+gate),'site_closure'):d.store.put('site_closure','operator',{'id':stable('campus-closure:'+gate),'feature_id':gate,'state':'open','at':'','reason':'No blockage reported.'})
 reports=d.store.list('report','operator');byid={r['id']:r for r in reports}
 closures={c['feature_id']:c for c in d.store.list('site_closure')}
 for r in sorted(reports,key=lambda r:r['received_at']):
  for c in r['claims']:
   f=c['location'].get('feature_id');text=c['excerpt'].lower()
   if c['kind']!='access' or c['assertion']!='asserted' or f not in ['north-gate','south-gate']:continue
   old=closures.get(f)
   if old and old.get('reviewed_after',old['at'])>=r['received_at']:continue
   state='blocked' if any(x in text for x in ['blocked','closed','obstructed','impassable']) and 'not blocked' not in text else 'open' if any(x in text for x in ['open','clear','reopened']) else None
   if state:closures[f]=d.store.put('site_closure','operator',{'id':stable('campus-closure:'+f),'feature_id':f,'state':state,'at':r['received_at'],'report_id':r['id'],'reason':c['excerpt']},event='campus_gate_reported')
 blocked={f for f,c in closures.items() if c['state']=='blocked'}
 active=[r for r in reports if r['status'] not in ['resolved','superseded'] and event_feature(r)]
 activeids={r['id'] for r in active}
 for a in d.store.list('site_assignment'):
  if a['state']=='released':continue
  u=d.store.get(a['unit_id'],'site_unit')
  if a['report_id'] not in activeids:
   a['state']='released';d.store.put('site_assignment','operator',a);u.update(status='available',assignment_id=None);d.store.put('site_unit','operator',u);continue
  newroute=route(u['node'],a['destination_node'],blocked)
  if newroute!=a['route']:
   a['route']=newroute
   if newroute['status']!='ready':a['state']='holding';u['status']='holding';d.store.put('site_unit','operator',u)
   d.store.put('site_assignment','operator',a,event='campus_route_updated')
 waiting=[{'report_id':r['id'],'summary':r['summary'],'feature_id':None,'capability':None,'reason':'Confirm the campus event feature before assigning a responder.'} for r in reports if r['status'] not in ['resolved','superseded'] and not event_feature(r) and any(c['location'].get('candidate_ids') for c in r['claims'])]
 for r in sorted(active,key=lambda r:-assess_report(r)['score']):
  if not r.get('brief',{}).get('response_required'):continue
  cap=CATEGORIES[r['category']]['capability'];feature=event_feature(r);plan=d.store.get(r['id'],'site_plan')
  ids={x['id'] for x in active if x['id']==r['id'] or r.get('incident_id') and x.get('incident_id')==r['incident_id']}
  existing=next((a for a in d.store.list('site_assignment') if a['report_id'] in ids and a['state']!='released' and a['capability']==cap),None)
  if existing:continue
  if not d.operations.config()['enabled'] or not d.operations.config()['auto_assign']:
   waiting.append({'report_id':r['id'],'summary':r['summary'],'feature_id':feature,'capability':cap,'reason':'Automatic assignment is paused in Setup.'});continue
  if plan and plan.get('paused'):waiting.append({'report_id':r['id'],'summary':r['summary'],'feature_id':feature,'capability':cap,'reason':'Unit released by operator. Recheck when ready.'});continue
  options=[]
  for u in d.store.list('site_unit'):
   if u['status']!='available' or u['capability']!=cap:continue
   path=route(u['node'],DEST[feature],blocked)
   if path['status']=='ready':options.append((path['distance_plan'],u,path))
  if options:
   _,u,path=min(options,key=lambda x:x[0]);a=d.store.put('site_assignment','operator',{'id':uid(),'report_id':r['id'],'unit_id':u['id'],'capability':cap,'feature_id':feature,'destination_node':DEST[feature],'state':'assigned','route':path,'at':now()},event='campus_unit_assigned');u.update(status='assigned',assignment_id=a['id']);d.store.put('site_unit','operator',u)
  else:waiting.append({'report_id':r['id'],'summary':r['summary'],'feature_id':feature,'capability':cap,'reason':'No available '+str(cap)+' campus unit has an open path. Check unit states and gates.'})
 allocations=[]
 for a in d.store.list('site_assignment'):
  if a['state']=='released':continue
  r=byid.get(a['report_id']);u=d.store.get(a['unit_id'],'site_unit')
  if r and u:allocations.append({**a,'unit_name':u['name'],'summary':r['summary'],'urgency':r['urgency'],'destination':BY_ID[a['feature_id']]['name']})
 units=[{**u,'position':NODES[u['node']]} for u in d.store.list('site_unit')]
 return {'site':sitepack(),'nodes':NODES,'roads':[{'id':str(i),'coordinates':[NODES[a],NODES[b]],'name':name,'gate':gate,'blocked':gate in blocked} for i,(a,b,name,gate) in enumerate(LINKS)],'units':units,'assignments':allocations,'closures':list(closures.values()),'waiting':waiting,'reports':active,'mode':'Fictional campus only; separate demo responders and authored site paths.'}

def register_campus(app,d,operator,json_body):
 from fastapi import Depends,Request
 @app.get('/api/site/operations')
 def campus(a=Depends(operator)):
  with d.store.transaction():return snapshot(d)
 @app.patch('/api/site/units/{id}')
 async def update(id,request:Request,a=Depends(operator)):
  body=await json_body(request)
  with d.store.transaction():
   u=d.store.get(id,'site_unit');state=body.get('status')
   if not u or state not in ['available','assigned','en_route','on_scene','holding']:raise ValueError('Choose a valid campus unit state.')
   if u['version']!=body.get('version'):raise ValueError('Campus unit changed. Refresh before updating.')
   assignment=d.store.get(u.get('assignment_id',''),'site_assignment')
   if state!='available' and not assignment:raise ValueError('The campus unit needs an assignment first.')
   if state=='en_route' and assignment['route']['status']!='ready':raise ValueError('No open site path is available.')
   if assignment:
    assignment['state']='released' if state=='available' else state;d.store.put('site_assignment','operator',assignment,event='campus_unit_progress')
    if state=='on_scene':u['node']=assignment['destination_node']
    if state=='available':d.store.put('site_plan','operator',{'id':assignment['report_id'],'paused':True});u['assignment_id']=None
   u['status']=state;return d.store.put('site_unit','operator',u,event='campus_unit_updated')
 @app.post('/api/site/replan/{id}')
 async def replan(id,request:Request,a=Depends(operator)):
  with d.store.transaction():d.store.put('site_plan','operator',{'id':id,'paused':False});return snapshot(d)
 @app.patch('/api/site/gates/{id}')
 async def gate(id,request:Request,a=Depends(operator)):
  body=await json_body(request)
  if id not in ['north-gate','south-gate'] or body.get('state') not in ['open','blocked'] or not str(body.get('reason','')).strip():raise ValueError('Choose a gate state and give a reason.')
  with d.store.transaction():
   old=d.store.get(stable('campus-closure:'+id),'site_closure')
   if body.get('version',0)!=(old['version'] if old else 0):raise ValueError('Gate state changed. Refresh before updating.')
   d.store.put('site_closure','operator',{'id':stable('campus-closure:'+id),'feature_id':id,'state':body['state'],'at':now(),'reviewed_after':now(),'reason':str(body['reason'])[:500]},event='campus_gate_reviewed');return snapshot(d)

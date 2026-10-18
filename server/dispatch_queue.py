"""Operator-owned next-stop queues for simulated city units and campus teams."""
from .store import now,Conflict
from .operations import stable


def provider(d,world,id):
 if world not in ['city','usc']:raise ValueError('Choose City or USC.')
 p=d.store.get(id,'unit' if world=='city' else 'usc_team')
 if not p:raise ValueError('Resource does not belong to this workspace.')
 return p


def queue(d,world,id):
 key=stable('dispatch-queue:'+world+':'+id)
 with d.store.lock:
  old=d.store.get(key,'unit_queue')
  if old:return old
  return d.store.put('unit_queue','operator',{'id':key,'world':world,'provider_id':id,'enabled':True,'items':[],'history':[]},event='provider_queue_initialized')


def save(d,q,event='dispatch_queue_updated'):
 q['updated_at']=now();q['history']=q.get('history',[])[-40:]
 return d.store.put('unit_queue','operator',q,event=event)


def reserved(d,world,id):
 return bool(queue(d,world,id)['items'])


def targets(d,world):
 if world=='usc':
  from .usc_atlas import atlas
  buildings={b['id']:b for b in atlas()['buildings']}
  return [{'id':t['id'],'title':t['title'],'location':buildings[t['building_id']]['name'],'point':buildings[t['building_id']]['center'],'capabilities':[t['capability']],'state':t['state'],'version':t['version'],'report_id':t['report_ids'][-1],'related':[t['id']],'assigned_provider':t.get('team_id')} for t in d.store.list('usc_ticket') if t['state']!='resolved' and t['report_ids']]
 from .worlds import report_world
 from .aggregation import members
 result=[];seen=set()
 for r in d.store.list('report','operator'):
  if report_world(r)!='city' or r['status'] in ['resolved','superseded'] or r.get('superseded_by'):continue
  key=r.get('incident_id') or r['id']
  if key in seen:continue
  seen.add(key);related=members(d,r);caps=set();geo=None
  for member in related:
   brief=member.get('brief') or {}
   if brief.get('response_required'):caps.update(d.operations.required_capabilities(member,brief))
   geo=geo or brief.get('location')
  if not caps:continue
  result.append({'id':r['id'],'title':r['summary'],'location':geo['label'] if geo else None,'point':[geo['lon'],geo['lat']] if geo else None,'geo':geo,'capabilities':sorted(caps),'state':r['status'],'version':r['version'],'report_id':r['id'],'incident_id':r.get('incident_id'),'related':[m['id'] for m in related]})
 return result


def target(d,world,id):
 available=targets(d,world);direct=next((t for t in available if id in t['related']),None)
 if direct or world=='usc':return direct
 original=d.store.get(id,'report')
 return next((t for t in available if original and original.get('incident_id') and t.get('incident_id')==original['incident_id']),None)


def current(d,world,p):
 if world=='usc':
  t=d.store.get(p.get('ticket_id',''),'usc_ticket')
  return t if t and t['state']!='resolved' and t.get('team_id')==p['id'] else None
 a=d.store.get(p.get('assignment_id',''),'assignment')
 return a if a and a['state']!='released' and a['unit_id']==p['id'] else None


def check_route(d,world,p,t):
 caps=p['capabilities'] if world=='city' else [p['capability']]
 if not set(caps)&set(t['capabilities']):raise ValueError('This resource does not have the required capability.')
 if not t['point']:raise ValueError('Confirm the event location before assigning this resource.')
 if p['status']=='unavailable':raise ValueError('This resource is unavailable. Mark it available first.')
 if world=='usc':
  if t.get('assigned_provider') and t['assigned_provider']!=p['id']:raise ValueError('Another team already owns this work item.')
  from .usc_atlas import route
  path=route(p['position'],t['point'],[c['edge_id'] for c in d.store.list('usc_closure') if c['state']=='blocked'])
 else:path=d.operations.route_for(p,t['geo'])
 if path['status']!='ready':raise ValueError(path.get('reason') or 'No open supported route. The queued stop is held for access review.')
 return path


def sync_city(d,t,completed=None,released=False):
 active=[a for a in d.store.list('assignment','operator') if a['report_id'] in t['related'] and a['state']!='released'];covered={a['capability'] for a in active}
 for id in t['related']:
  plan=d.store.get(id,'plan');r=d.store.get(id,'report')
  if not plan or not r or r['status'] in ['resolved','superseded']:continue
  done=set(plan.get('completed_capabilities',[]))
  if completed:done.add(completed)
  plan['completed_capabilities']=sorted(done);needed=set(d.operations.required_capabilities(r,plan['brief']));missing=needed-covered-done
  plan['assignment_ids']=list(dict.fromkeys(plan.get('assignment_ids',[])+[a['id'] for a in active]))
  if missing:
   plan['state']='resource_needed'
   if released:plan['assignment_review_required']=True
   for cap in missing:
    reason=cap.capitalize()+' unit was released. Check available units to assign a replacement.'
    plan.setdefault('shortages',{})[cap]=reason;d.operations.task(plan,'resource:'+cap,'Review '+cap+' coverage',reason,'urgent')['state']='open'
  else:
   plan['state']='assigned' if active else 'unit_work_finished';plan.pop('assignment_review_required',None)
  for cap in covered|done:
   plan.setdefault('shortages',{}).pop(cap,None)
   for task in plan['tasks']:
    if task['kind']=='resource:'+cap and task['state']=='open':task.update(state='auto_resolved',operator_reason='Resource assigned or its work marked complete by the operator.')
  plan.update(resource_signature=d.operations.resource_signature(),updated_at=now());d.store.put('plan','operator',plan,event='dispatch_plan_synchronized')


def detach(d,world,p,note,finished=False):
 old=current(d,world,p)
 if not old:return
 t=target(d,world,old['report_id'] if world=='city' else old['id'])
 if world=='city':
  old.update(state='released',updated_at=now(),release_reason=note,completed=finished);d.store.put('assignment','operator',old,event='unit_work_finished' if finished else 'assignment_reassigned')
  if finished and t and t['point']:p.update(position={'lon':t['point'][0],'lat':t['point'][1]},position_source='operator_marked_completion')
  p.update(status='available',assignment_id=None);d.store.put('unit','operator',p,event='queued_unit_freed')
  if t:sync_city(d,t,old['capability'] if finished else None,released=not finished)
 else:
  old.update(team_id=None,route=None,state='resolved' if finished else 'open',assignment_paused=not finished,resolution_cause='operator' if finished else None,updated_at=now());old['history'].append({'at':now(),'action':'work_finished' if finished else 'team_reassigned','note':note});d.store.put('usc_ticket','operator',old,event='usc_work_finished' if finished else 'usc_team_reassigned')
  if finished and t:p.update(position=t['point'],position_source='operator_marked_completion')
  p.update(status='available',ticket_id=None);d.store.put('usc_team','operator',p,event='queued_team_freed')
 if t:d.operations.log(t['report_id'],'unit-finished' if finished else 'unit-reassigned',p['name']+(' finished its assignment' if finished else ' reassigned'),note,key='provider:'+p['id']+':'+now())


def assign_to(d,world,p,t,path,note):
 if world=='city':
  cap=next(c for c in p['capabilities'] if c in t['capabilities']);id=stable('provider-assignment:'+p['id']+':'+t['id'])
  a={'id':id,'report_id':t['id'],'unit_id':p['id'],'capability':cap,'state':'assigned','route':path,'selected_route':'recommended','created_at':now(),'updated_at':now(),'mode':'demo','reason':note}
  d.store.put('assignment','operator',a,event='queued_unit_assigned');p.update(status='assigned',assignment_id=id);d.store.put('unit','operator',p,event='queued_unit_reserved');sync_city(d,t)
 else:
  item=d.store.get(t['id'],'usc_ticket');item.update(team_id=p['id'],state='assigned',route=path,assignment_paused=False,updated_at=now());item['history'].append({'at':now(),'action':'queued_team_assigned','note':p['name']+': '+note});d.store.put('usc_ticket','operator',item,event='queued_team_assigned');p.update(status='assigned',ticket_id=t['id']);d.store.put('usc_team','operator',p,event='queued_team_reserved')
 d.operations.log(t['report_id'],'assigned:queue',p['name']+' assigned from its queue',note,key='queue:'+p['id']+':'+now())


def advance(d,world,id,automatic=True):
 q=queue(d,world,id);p=provider(d,world,id)
 if current(d,world,p) or p['status']!='available' or not q['items']:return
 if automatic and (not q['enabled'] or not d.operations.config()['enabled'] or not d.operations.config()['auto_assign']):return
 while q['items']:
  t=target(d,world,q['items'][0]['target_id'])
  if t:break
  removed=q['items'].pop(0);q['history'].append({'at':now(),'action':'closed_stop_skipped','target_id':removed['target_id']});q=save(d,q)
 if not q['items']:return
 try:path=check_route(d,world,p,t)
 except ValueError as e:
  if q.get('hold_reason')!=str(e):q['hold_reason']=str(e);save(d,q,'dispatch_queue_held')
  return
 assign_to(d,world,p,t,path,'Next saved stop; route checked against current reported blockages.')
 q['items'].pop(0);q.pop('hold_reason',None);q['history'].append({'at':now(),'action':'advanced','target_id':t['id']});save(d,q,'dispatch_queue_advanced')


def advance_all(d):
 for q in d.store.list('unit_queue','operator'):
  if q['items']:advance(d,q['world'],q['provider_id'])


def snapshot(d,world):
 if world not in ['city','usc']:raise ValueError('Choose City or USC.')
 if world=='usc':
  from .usc_ops import bootstrap
  bootstrap(d)
 rows=[];available=targets(d,world)
 for p in d.store.list('unit' if world=='city' else 'usc_team','operator'):
  q=queue(d,world,p['id']);job=current(d,world,p)
  cur=target(d,world,job['report_id'] if world=='city' else job['id']) if job else None
  items=[]
  for item in q['items']:
   t=target(d,world,item['target_id'])
   items.append({**item,'title':t['title'] if t else 'Closed or replaced report','location':t['location'] if t else None,'state':t['state'] if t else 'closed','report_id':t['report_id'] if t else None})
  rows.append({**q,'name':p['name'],'status':p['status'],'capabilities':p['capabilities'] if world=='city' else [p['capability']],'provider_version':p['version'],'current':{k:cur[k] for k in ['id','title','location','report_id']} if cur else None,'items':items})
 return {'world':world,'providers':rows,'targets':[{k:v for k,v in t.items() if k not in ['geo','point','related']} for t in available],'automatic':d.operations.config()['enabled'] and d.operations.config()['auto_assign']}


def change(d,world,id,body):
 p=provider(d,world,id);q=queue(d,world,id)
 if type(body.get('version')) is not int or q['version']!=body['version'] or type(body.get('provider_version')) is not int or p['version']!=body['provider_version']:raise Conflict('This resource or its queue changed. Refresh before updating.')
 action=body.get('action');note=str(body.get('note','')).strip()
 if action in ['finish','reassign'] and not 3<=len(note)<=1000:raise ValueError('Describe why this assignment is changing.')
 if action in ['enqueue','reassign']:
  t=target(d,world,body.get('target_id'))
  if not t:raise ValueError('Choose an active incident in this workspace.')
  caps=p['capabilities'] if world=='city' else [p['capability']]
  if not set(caps)&set(t['capabilities']):raise ValueError('This resource does not have the required capability.')
  cur=current(d,world,p)
  if cur and ((world=='usc' and cur['id']==t['id']) or (world=='city' and cur['report_id'] in t['related'])):raise ValueError('This resource is already assigned there.')
 if action=='enqueue':
  if len(q['items'])>=30:raise ValueError('A resource queue can contain up to 30 stops.')
  if any(i['target_id'] in t['related'] for i in q['items']):raise ValueError('This incident is already in this queue.')
  q['items'].append({'target_id':t['id'],'queued_at':now()})
 elif action=='remove':q['items']=[i for i in q['items'] if i['target_id']!=body.get('target_id')]
 elif action=='reorder':
  order=body.get('order');old=[i['target_id'] for i in q['items']]
  if not isinstance(order,list) or not all(isinstance(x,str) for x in order) or len(order)!=len(old) or len(set(order))!=len(order) or set(order)!=set(old):raise ValueError('Include every queued stop once.')
  q['items']=sorted(q['items'],key=lambda i:order.index(i['target_id']))
 elif action=='set_enabled':
  if type(body.get('enabled')) is not bool:raise ValueError('Choose whether to advance automatically.')
  q['enabled']=body['enabled']
 elif action=='reassign':
  if t['version']!=body.get('target_version'):raise Conflict('The destination changed. Review the current incident.')
  path=check_route(d,world,p,t)  # Validate before releasing the current work.
  detach(d,world,p,note);p=provider(d,world,id);assign_to(d,world,p,t,path,note);q['items']=[i for i in q['items'] if i['target_id'] not in t['related']]
 elif action=='finish':
  if not current(d,world,p):raise Conflict('This resource has no current assignment.')
  detach(d,world,p,note,finished=True)
 elif action!='advance':raise ValueError('Choose a supported queue action.')
 q.pop('hold_reason',None);q['history'].append({'at':now(),'action':action,'target_id':body.get('target_id'),'note':note});save(d,q)
 if action=='advance':advance(d,world,id,automatic=False)
 else:advance(d,world,id)
 return next(p for p in snapshot(d,world)['providers'] if p['provider_id']==id)


def register(app,d,operator,json_body,idem):
 from fastapi import Depends,Request
 @app.get('/api/dispatch-queues')
 def get(world:str='city',a=Depends(operator)):
  with d.store.transaction():return snapshot(d,world)
 @app.post('/api/dispatch-queues/{world}/{id}')
 async def update(world:str,id:str,request:Request,a=Depends(operator)):
  body=await json_body(request)
  def apply():
   with d.store.transaction():return change(d,world,id,body)
  return idem(request,a,body,apply)

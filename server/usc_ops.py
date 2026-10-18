"""Source-linked campus facilities demo. No real USC equipment or teams are connected."""
import re,copy
from datetime import datetime,timezone
from .store import uid,now,Conflict
from .operations import stable
from .usc_atlas import atlas,public,route,resolve,nearest

def feature(report):
 from .worlds import report_world
 if report_world(report)!='usc':return None
 locations=[c['location'] for c in report['claims'] if c['location']['role']!='reporter' and c['location'].get('status')!='needs_confirmation' and str(c['location'].get('feature_id','')).startswith('usc-') and c['assertion'] not in ['negated','hypothetical']]
 confirmed={loc['feature_id'] for loc in locations if loc['status']=='operator_confirmed'}
 choices=confirmed or {loc['feature_id'] for loc in locations}
 return next(iter(choices)) if len(choices)==1 else None

def bootstrap(d):
 for name,cap,building in [('Facilities 01','maintenance','usc-tutor'),('Facilities 02','maintenance','usc-kaprielian'),('Lab Safety 01','lab_safety','usc-michelson'),('Lab Safety 02','lab_safety','usc-seaver'),('Alarm Technician 01','alarm','usc-leavey'),('Access Team 01','access','usc-bovard')]:
  id=stable('usc-team:'+name)
  if not d.store.get(id,'usc_team'):
   b=next(b for b in atlas()['buildings'] if b['id']==building);d.store.put('usc_team','operator',{'id':id,'name':name,'capability':cap,'status':'available','position':b['center'],'ticket_id':None,'demo':True})
 for gate in atlas()['access_points']:
  if gate['kind']!='campus_access':continue
  id=stable(gate['id'])
  if not d.store.get(id,'usc_gate'):d.store.put('usc_gate','operator',{'id':id,'access_id':gate['id'],'name':gate['name'],'position':gate['position'],'state':'unreviewed','reason':'Current access has not been checked in this demo.','at':'','edge_ids':[e[2] for e in atlas()['graph'][nearest(gate['position'])]]})
 for name,b,kind,unit,low,high in [('SGM demo nitrogen tank','usc-sgm','pressure','psi',60,180),('MCB demo gas monitor','usc-michelson','gas','reported state',None,None),('Leavey demo smoke alarm','usc-leavey','smoke','reported state',None,None),('TCC demo service door','usc-tutor','access','reported state',None,None)]:
  id=stable('usc-asset:'+name)
  if not d.store.get(id,'usc_asset'):d.store.put('usc_asset','operator',{'id':id,'name':name,'building_id':b,'kind':kind,'unit':unit,'low':low,'high':high,'limit_basis':'Demo range set for this test; not a manufacturer or USC limit.','readings':[],'demo':True})
def details(d,r):
 fid=feature(r)
 if not fid:return None
 claims=[c for c in r['claims'] if c['assertion'] not in ['negated','hypothetical'] and c['location']['role']!='reporter'];text=' '.join(c['excerpt'] for c in claims)
 match=re.search(r'(?<![\w.+-])([+-]?\d+(?:\.\d+)?)\s*(?:psi|pounds per square inch)\b',text,re.I)
 clauses=re.split(r'[.!?;\n]|\bbut\b',text,flags=re.I)
 gas=any(re.search(r'\b(gas leak|gas odor|smell.{0,12}gas|gas detector|gas monitor)\b',cl,re.I) and not re.search(r'\b(?:no|without) (?:a |any )?(?:gas|smell)|\bnot (?:a )?gas leak|(?:do not|don.t|cannot|can.t) smell',cl,re.I) for cl in clauses)
 smoke=any(re.search(r'\b(smoke|fire alarm)\b',cl,re.I) and not re.search(r'\b(?:no|without) (?:visible |any )?smoke|(?:cannot|can.t|do not|don.t) see (?:any )?smoke|\b(?:test|not sounding|false alarm)\b',cl,re.I) for cl in clauses)
 kind='pressure' if match else 'gas' if gas else 'smoke' if smoke else 'access' if re.search(r'\b(door|gate|entrance|exit|blocked)\b',text,re.I) else 'maintenance'
 asset=next((a for a in d.store.list('usc_asset') if a['building_id']==fid and a['kind']==kind and (kind!='pressure' or re.search(r'\bdemo (?:nitrogen )?tank\b',text,re.I))),None)
 identity=re.search(r'\b(?:tank|cylinder)\s*(?:#|id\s+)?([A-Z]*\d[\w-]*)',text,re.I)
 asset_key=asset['id'] if asset else identity[1].lower() if identity else r['id'] if kind=='pressure' else kind
 value=float(match[1]) if match else None;outside=bool(value is not None and asset and ((asset['low'] is not None and value<asset['low']) or (asset['high'] is not None and value>asset['high'])))
 priority=95 if kind=='gas' else 90 if kind=='smoke' else 70 if outside else 45 if kind=='access' else 25
 cap='lab_safety' if kind=='gas' or outside else 'alarm' if kind=='smoke' else 'access' if kind=='access' else 'maintenance'
 return {'building_id':fid,'kind':kind,'asset_id':asset['id'] if asset else None,'asset_key':r['id'] if r.get('aggregation_hold') else asset_key,'value':value,'unit':'psi' if match else None,'outside_demo_range':outside,'priority':priority,'capability':cap,'evidence':text[:3000]}
def import_access(d,r):
 observed=r.get('observed_at');at=datetime.fromtimestamp(observed,timezone.utc).isoformat() if isinstance(observed,(int,float)) else r['received_at']
 for c in r['claims']:
  if c['kind']!='access' or c['assertion']!='asserted':continue
  text=c['excerpt'].lower();blocked=bool(re.search(r'\b(blocked|closed|obstructed|impassable)\b',text)) and not re.search(r'\b(not blocked|not closed|unblocked)\b',text)
  clear=bool(re.search(r'\b(open|reopened|clear|unblocked)\b',text)) and not re.search(r'\b(not|isn.t) (?:open|clear)\b',text)
  if not blocked and not clear:continue
  for gate in d.store.list('usc_gate'):
   if gate['name'].lower() not in text or gate['at']>=at:continue
   gate.update(state='blocked' if blocked else 'open',reason=c['excerpt'],at=at);d.store.put('usc_gate','operator',gate,event='usc_gate_report_received')
   for eid in gate['edge_ids']:
    edge=next(e for e in atlas()['edges'] if e['id']==eid);d.store.put('usc_closure','operator',{'id':stable('usc-closure:'+eid),'edge_id':eid,'state':gate['state'],'reason':c['excerpt'],'coordinates':edge['coordinates'],'at':at,'report_id':r['id'],'gate_id':gate['id']},event='usc_gate_report_path_updated')
  for edge in atlas()['edges']:
   if edge['name'] in ['Mapped campus path','Steps'] or edge['name'].lower() not in text:continue
   old=d.store.get(stable('usc-closure:'+edge['id']),'usc_closure')
   if old and old.get('at','')>=at:continue
   d.store.put('usc_closure','operator',{'id':stable('usc-closure:'+edge['id']),'edge_id':edge['id'],'state':'blocked' if blocked else 'open','reason':c['excerpt'],'coordinates':edge['coordinates'],'at':at,'report_id':r['id']},event='usc_access_report_received')

def on_report(d,r):
 from .worlds import report_world
 if report_world(r)!='usc':return
 if not feature(r):
  import_access(d,r);return
 bootstrap(d);import_access(d,r);info=details(d,r)
 if not info or r['status'] in ['resolved','superseded']:return
 category={'gas':'safety','smoke':'fire','pressure':'safety','access':'access','maintenance':'service'}[info['kind']]
 if r.get('category')!=category:
  r['category']=category;d.store.put('report','operator',r,event='usc_condition_categorized')
 # Surface facilities urgency in the main review queue without treating a reading as verified telemetry.
 if not r.get('priority_override') and info['priority']>r.get('triage',{}).get('score',0):
  r['triage'].update(score=info['priority'],label='Reported gas concern' if info['kind']=='gas' else 'Alarm review' if info['kind']=='smoke' else 'Outside demo range' if info['outside_demo_range'] else 'Facilities review',urgency='critical' if info['priority']>=90 else 'elevated' if info['priority']>=65 else 'routine',needs_review=info['priority']>=65,reasons=[info['evidence']]);r.update(urgency=r['triage']['urgency'],needs_urgent_review=info['priority']>=65);d.store.put('report','operator',r,event='usc_review_priority')

 ticket=next((t for t in d.store.list('usc_ticket') if r['id'] in t['report_ids']),None)
 if ticket and (ticket['building_id']!=info['building_id'] or ticket.get('asset_key')!=info['asset_key']):
  ticket['report_ids']=[id for id in ticket['report_ids'] if id!=r['id']];ticket['history'].append({'at':now(),'action':'source_relocated_or_separated','report_id':r['id'],'note':'Operator interpretation or grouping changed; source retained.'});d.store.put('usc_ticket','operator',ticket,event='usc_source_reassociated')
  old=d.store.get(ticket.get('incident_id',''),'incident')
  if old:old['report_ids']=[id for id in old['report_ids'] if id!=r['id']];d.store.put('incident','operator',old)
  r['incident_id']=None;ticket=None
 if ticket:return
 ticket=next((t for t in d.store.list('usc_ticket') if t['state']!='resolved' and t['building_id']==info['building_id'] and t['kind']==info['kind'] and t.get('asset_key')==info['asset_key']),None)
 if not ticket:ticket={'id':uid(),'report_ids':[],'state':'open','created_at':now(),'team_id':None,'route':None,'history':[],'title':r['summary'],**info}
 ticket.setdefault('incident_id',r.get('incident_id') or uid())
 incident=d.store.get(ticket['incident_id'],'incident') or {'id':ticket['incident_id'],'title':r['summary'],'report_ids':[],'status':'open','owner':None,'created_at':now(),'automatic':True,'grouping_rule':'Same campus building, asset and facilities issue; original sources retained.'}
 incident['report_ids']=list(dict.fromkeys(ticket['report_ids']+[r['id']]));d.store.put('incident','operator',incident,event='usc_sources_grouped')
 r['incident_id']=incident['id'];d.store.put('report','operator',r,event='usc_incident_associated')
 if info['priority']>ticket['priority']:ticket.update(title=r['summary'],capability=info['capability'])
 ticket['report_ids'].append(r['id']);ticket['priority']=max(ticket['priority'],info['priority']);ticket['updated_at']=now();ticket['history'].append({'at':now(),'action':'report_linked','report_id':r['id'],'note':r['reporter_name']+' · '+r['summary']})
 # A later abnormal reading escalates an existing maintenance work item.
 if info['outside_demo_range']:ticket['capability']='lab_safety'
 d.store.put('usc_ticket','operator',ticket,event='usc_received_report_linked')
 if info['asset_id'] and info['value'] is not None:
  a=d.store.get(info['asset_id'],'usc_asset');a['readings'].append({'at':r['received_at'],'value':info['value'],'unit':info['unit'],'report_id':r['id'],'outside_demo_range':info['outside_demo_range']});d.store.put('usc_asset','operator',a,event='usc_reported_reading')

def snapshot(d):
 bootstrap(d)
 for r in d.store.list('report','operator'):on_report(d,r)
 buildings={b['id']:b for b in atlas()['buildings']};blocked=[c['edge_id'] for c in d.store.list('usc_closure') if c['state']=='blocked']
 for t in sorted(d.store.list('usc_ticket'),key=lambda t:-t['priority']):
  original=copy.deepcopy(t)
  active=[d.store.get(id,'report') for id in t['report_ids']];active=[r for r in active if r and r['status'] not in ['resolved','superseded']];team=d.store.get(t.get('team_id',''),'usc_team')
  if not active and t['state']!='resolved':t['state']='resolved';t['resolution_cause']='source_cases_closed';t['history'].append({'at':now(),'action':'source_cases_closed','note':'No linked source remains active on this work item.'})
  if t['state']=='resolved' and active and t.get('resolution_cause')=='source_cases_closed':t.update(state='open',team_id=None,route=None,resolution_cause=None);team=None
  if t['state']=='resolved':
   if team and team.get('ticket_id')==t['id']:team.update(status='available',ticket_id=None);d.store.put('usc_team','operator',team,event='usc_team_released')
   t.update(team_id=None,route=None)
   if t!=original:d.store.put('usc_ticket','operator',t)
   continue
  if team and team['capability']!=t['capability'] and team['status']=='assigned':team.update(status='available',ticket_id=None);d.store.put('usc_team','operator',team);team=None;t['team_id']=None
  if not team and not t.get('assignment_paused') and d.operations.config()['enabled'] and d.operations.config()['auto_assign']:
   options=[]
   for u in d.store.list('usc_team'):
    from .dispatch_queue import reserved
    if u['status']!='available' or u['capability']!=t['capability'] or reserved(d,'usc',u['id']):continue
    path=route(u['position'],buildings[t['building_id']]['center'],blocked)
    if path['status']=='ready':options.append((path['distance_m'],u,path))
   if options:
    _,team,path=min(options,key=lambda x:x[0]);team.update(status='assigned',ticket_id=t['id']);t['state']='assigned';d.store.put('usc_team','operator',team,event='usc_team_assigned');t.update(team_id=team['id'],route=path);t['history'].append({'at':now(),'action':'team_assigned','note':team['name']+' assigned in this demo.'})
  if team:
   t['route']=route(team['position'],buildings[t['building_id']]['center'],blocked)
   if t['route']['status']!='ready' and team['status'] not in ['on_scene','holding']:team['status']='holding';d.store.put('usc_team','operator',team,event='usc_path_hold')
  if t!=original:d.store.put('usc_ticket','operator',t)
 from .dispatch_queue import advance_all
 advance_all(d)
 from .worlds import report_world
 return {'site':public(),'teams':d.store.list('usc_team'),'tickets':sorted(d.store.list('usc_ticket'),key=lambda t:(t['state']=='resolved',-t['priority'])),'assets':d.store.list('usc_asset'),'closures':d.store.list('usc_closure'),'reports':[r for r in d.store.list('report','operator') if report_world(r)=='usc'],'access_points':d.store.list('usc_access'),'gates':d.store.list('usc_gate'),'limits_note':'Reported values and operator-set demo ranges. No real sensor connection or automatic valve control.'}

def register_usc(app,d,operator,json_body,idem):
 from fastapi import Depends,Request
 @app.get('/api/usc/operations')
 def get(a=Depends(operator)):
  with d.store.transaction():return snapshot(d)
 @app.patch('/api/usc/tickets/{id}')
 async def ticket(id,request:Request,a=Depends(operator)):
  body=await json_body(request)
  def change():
   with d.store.transaction():
    t=d.store.get(id,'usc_ticket')
    if not t or t['version']!=body.get('version'):raise Conflict('Work item changed. Refresh before updating.')
    state=body.get('state');note=str(body.get('note','')).strip()
    if state not in ['open','assigned','en_route','on_scene','monitoring','resolved'] or len(note)<3:raise ValueError('Choose a state and describe what changed.')
    u=d.store.get(t.get('team_id',''),'usc_team')
    if state in ['assigned','en_route','on_scene'] and not u:raise ValueError('A team is needed first.')
    if state=='en_route' and (not t['route'] or t['route']['status']!='ready'):raise ValueError('No open mapped path. Review access first.')
    t.update(state=state,updated_at=now(),resolution_cause='operator' if state=='resolved' else None);t['history'].append({'at':now(),'action':state,'note':note})
    if u:
     if state=='resolved':u.update(status='available',ticket_id=None);t.update(team_id=None,route=None)
     elif state in ['assigned','en_route','on_scene']:u['status']=state
     if state=='on_scene':u['position']=next(b['center'] for b in atlas()['buildings'] if b['id']==t['building_id'])
     d.store.put('usc_team','operator',u,event='usc_team_progress')
    saved=d.store.put('usc_ticket','operator',t,event='usc_work_item_updated')
    if u and state=='resolved':
     from .dispatch_queue import advance
     advance(d,'usc',u['id'])
    return saved
  return idem(request,a,body,change)
 @app.patch('/api/usc/assets/{id}')
 async def asset(id,request:Request,a=Depends(operator)):
  body=await json_body(request)
  with d.store.transaction():
   x=d.store.get(id,'usc_asset');low=body.get('low');high=body.get('high')
   if not x or x['version']!=body.get('version'):raise Conflict('Asset changed. Refresh before updating.')
   if x['kind']!='pressure' or not isinstance(low,(float,int)) or not isinstance(high,(float,int)) or not 0<=low<high<=10000 or len(str(body.get('reason','')).strip())<3:raise ValueError('Set a valid demo range and explain its source.')
   x.update(low=low,high=high,limit_basis=body['reason']);return d.store.put('usc_asset','operator',x,event='usc_demo_limits_updated')
 @app.patch('/api/usc/gates/{id}')
 async def gate(id,request:Request,a=Depends(operator)):
  body=await json_body(request)
  with d.store.transaction():
   g=d.store.get(id,'usc_gate')
   if not g or g['version']!=body.get('version'):raise Conflict('Gate review changed. Refresh before updating.')
   if body.get('state') not in ['open','blocked'] or len(str(body.get('reason','')).strip())<3:raise ValueError('Choose a gate state and describe what was checked.')
   g.update(state=body['state'],reason=body['reason'],at=now());d.store.put('usc_gate','operator',g,event='usc_gate_reviewed')
   for eid in g['edge_ids']:
    edge=next(e for e in atlas()['edges'] if e['id']==eid);d.store.put('usc_closure','operator',{'id':stable('usc-closure:'+eid),'edge_id':eid,'state':body['state'],'reason':g['name']+': '+body['reason'],'coordinates':edge['coordinates'],'at':g['at'],'gate_id':id},event='usc_gate_path_updated')
   return g
 @app.post('/api/usc/closures')
 async def closure(request:Request,a=Depends(operator)):
  body=await json_body(request);edge=next((e for e in atlas()['edges'] if e['id']==body.get('edge_id')),None)
  if not edge or body.get('state') not in ['blocked','open'] or len(str(body.get('reason','')).strip())<3:raise ValueError('Choose a mapped path and describe the access update.')
  def save():
   with d.store.transaction():
    id=stable('usc-closure:'+edge['id']);old=d.store.get(id,'usc_closure')
    if old and old['version']!=body.get('version'):raise Conflict('Path changed. Refresh before updating.')
    x=d.store.put('usc_closure','operator',{'id':id,'edge_id':edge['id'],'state':body['state'],'reason':body['reason'],'coordinates':edge['coordinates'],'at':now()},event='usc_path_reviewed');return x
  return idem(request,a,body,save)
 @app.post('/api/usc/access-points')
 async def access(request:Request,a=Depends(operator)):
  body=await json_body(request);b=next((b for b in atlas()['buildings'] if b['id']==body.get('building_id')),None);pos=body.get('position',[])
  if not b or body.get('kind') not in ['entrance','exit'] or len(str(body.get('name','')).strip())<3 or len(str(body.get('source','')).strip())<5 or not isinstance(pos,list) or len(pos)!=2 or any(not isinstance(x,(int,float)) for x in pos) or not -118.292<=pos[0]<=-118.278 or not 34.015<=pos[1]<=34.026:raise ValueError('Choose a campus point, building, type, name and source.')
  def save():
   with d.store.transaction():return d.store.put('usc_access','operator',{'id':uid(),'name':body['name'],'kind':body['kind'],'position':pos,'building_id':b['id'],'source':body['source'],'evidence':'Operator-supplied point; not independently verified','at':now()},event='usc_access_point_added')
  return idem(request,a,body,save)
 @app.post('/api/usc/reports')
 async def entered(request:Request,a=Depends(operator)):
  body=await json_body(request);b=next((b for b in atlas()['buildings'] if b['id']==body.get('building_id')),None);text=str(body.get('text','')).strip();name=str(body.get('reporter','Facilities desk')).strip()
  if not b or not 3<=len(text)<=4000 or not 1<=len(name)<=100:raise ValueError('Choose a campus building, reporter and a report of 3–4,000 characters.')
  def create():
   from .scenarios import fact
   session=d.create_session(name,'usc');source='Reported location: '+b['name']+'.\n'+text
   draft=d.manual_draft(session['endpoint_id'],session['id'],source,[fact('access' if re.search(r'\b(blocked|reopened|path is open|path is clear)\b',text,re.I) else 'observation',text[:180],text,b['name'])]);message=d.send_report(draft);return {'message_id':message['id'],'state':'queued','label':'Operator-entered report queued for delivery.'}
  return idem(request,a,body,create)
 @app.post('/api/demo/usc')
 async def seed(request:Request,a=Depends(operator)):
  body=await json_body(request)
  def create():
   from .usc_scenarios import seed_usc
   return seed_usc(d)
  return idem(request,a,body,create)

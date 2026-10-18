"""Auditable local dispatch automation. Units and destinations are demo-only.

Policies make routine local decisions; no telephony, SMS, agency CAD or public
alert service is connected. Outbound caller text still uses the approval flow.
"""
import hashlib,json,time,re
from uuid import uuid5,NAMESPACE_URL
from .store import uid,now,Conflict
from .geography import atlas,point,distance,norm
from .threats import assess,assess_report,rank_claims,claim_priority,POLICY

def stable(key):return str(uuid5(NAMESPACE_URL,'comm-control-v3:'+key))
CATEGORIES={
 'fire':{'label':'Fire & smoke','capability':'fire','color':'coral'},
 'medical':{'label':'Medical','capability':'medical','color':'blue'},
 'access':{'label':'Road & access','capability':'traffic','color':'amber'},
 'safety':{'label':'Safety','capability':'safety','color':'violet'},
 'service':{'label':'Assistance','capability':'general','color':'teal'},
 'information':{'label':'Information update','capability':None,'color':'gray'}}
UNITS=[('Fire 01','fire',[-118.2463,34.0606]),('Fire 02','fire',[-118.2473,34.0467]),('Medic 01','medical',[-118.2553,34.0478]),('Medic 02','medical',[-118.2427,34.0651]),('Access 01','traffic',[-118.2355,34.0550]),('Safety 01','safety',[-118.2560,34.0531]),('Support 01','general',[-118.2501,34.0521])]

def classify(report):
 claims=rank_claims(report['claims']);active=[c for c in claims if c['assertion'] not in ['negated','hypothetical']]
 kinds={c['kind'] for c in active};text=' '.join(c['excerpt'] for c in active).lower()
 if any(claim_priority(c)[2]=='safety' and claim_priority(c)[0]>=85 for c in active):category='safety'
 elif kinds&{'smoke','fire'}:category='fire'
 elif kinds&{'medical','self_harm'}:category='medical'
 elif re.search(r'\b(injured|unconscious|bleeding|medical|ambulance|not breathing)\b',text):category='medical'
 elif re.search(r'\b(weapon|violence|threat|assault)\b',text):category='safety'
 elif 'access' in kinds:category='access'
 else:category='service'
 response_required=bool(kinds&{'violence','self_harm','medical','basic_need','smoke','fire','hazard','request','question'} or re.search(r'\b(injured|unconscious|bleeding|not breathing|blocked|obstructed|impassable|broken|stuck)\b|will not close',text))
 if not response_required:category='information'
 needs=[]
 for c in active:
  if c['kind'] in ['request','question']:needs.append(c['value'])
 for c in active:
  if c['kind'] in ['violence','self_harm','medical'] and c['value'] not in needs:needs.insert(0,c['value'])
 if not needs:needs=[{'fire':'Fire response assessment','medical':'Medical response assessment','safety':'Safety response assessment','access':'Access check and road support','service':'General assistance','information':'No new help requested'}[category]]
 # Evidence phrases drive the brief; do not fabricate affected populations or times.
 concerns=[c['value'] for c in active if c['assertion'] in ['uncertain','hearsay']]
 loc=next((c['location'] for c in active if c['location']['role']!='reporter' and c['location'].get('geo')),None)
 if not loc:
  loc=next((c['location'] for c in active if c['location']['role']=='reporter' and c['location'].get('geo')),None)
  origin_only=bool(loc)
 else:origin_only=False
 geo=loc.get('geo') if loc else None
 if origin_only:geo=None # Caller position does not silently locate an event.
 return {'response_required':response_required,'category':category,'category_label':CATEGORIES[category]['label'],'needs':needs[:4],'concerns':concerns[:4],'location':geo,'location_status':'needs_confirmation' if origin_only else loc['status'] if loc else 'unlocated','observation_time':report.get('observed_at'),'observation_time_status':report.get('observation_time_status','unknown'),'received_at':report['received_at'],'summary':report['summary']}

class Operations:
 def __init__(self,domain):self.d=domain;self.store=domain.store;self.map=atlas();self.last_tick=0;self.bootstrap()
 def bootstrap(self):
  if not self.store.get('operations','config'):
   self.store.put('config','operator',{'id':'operations','enabled':True,'auto_assign':True,'auto_escalate':True,'mode':'demo','policy_version':'dispatch-demo-1','closure_revision':0,'tile_url':'https://tile.openstreetmap.org/{z}/{x}/{y}.png'},event='automation_initialized')
  for label,cap,coords in UNITS:
   id=stable('unit:'+label)
   if not self.store.get(id,'unit'):self.store.put('unit','operator',{'id':id,'name':label,'capabilities':[cap],'status':'available','position':{'lon':coords[0],'lat':coords[1]},'assignment_id':None,'demo':True},event='demo_unit_created')
 def config(self):return self.store.get('operations','config')
 def log(self,report_id,kind,title,detail='',key=None):
  id=stable(report_id+':'+(key or kind))
  if self.store.get(id,'action'):return
  self.store.put('action','operator',{'id':id,'report_id':report_id,'kind':kind,'title':title,'detail':detail,'at':now(),'mode':'demo'},event='automatic_action')
 def task(self,plan,kind,title,reason,priority='review'):
  id=stable(plan['report_id']+':task:'+kind);old=next((t for t in plan.get('tasks',[]) if t['id']==id),None)
  task={'id':id,'kind':kind,'title':title,'reason':reason,'priority':priority,'state':old['state'] if old else 'open','created_at':old['created_at'] if old else now()}
  if old:
   old.update(title=title,reason=reason,priority=priority);return old
  plan.setdefault('tasks',[]).append(task);return task
 def active_closures(self):return [c for c in self.store.list('closure','operator') if c['state'] in ['active','stale']]
 def excluded(self):return set(k for c in self.active_closures() for k in c['edge_ids'])
 def on_report(self,report):
  # Caller owns a transaction (receiver application is atomic).
  triage=assess_report(report);report['claims']=rank_claims(report['claims']);report.update(triage=triage,urgency=triage['urgency'],urgency_reasons=triage['reasons'],needs_urgent_review=triage['needs_review'])
  brief=classify(report);report.update(category=brief['category'],brief=brief);self.store.put('report','operator',report,event='incident_categorized')
  from .aggregation import group_report
  report=group_report(self.d,report)
  plan=self.store.get(report['id'],'plan') or {'id':report['id'],'report_id':report['id'],'session_id':report['session_id'],'created_at':now(),'assignment_ids':[],'tasks':[],'mode':'demo'}
  plan.pop('assignment_review_required',None);plan.pop('completed_capabilities',None)
  plan.update(brief=brief,updated_at=now(),policy_version=self.config()['policy_version'],triage_policy=POLICY)
  if report.get('superseded_by') or report['status'] in ['resolved','superseded']:
   self.release_report(report['id']);plan['state']='closed';self.store.put('plan','operator',plan,event='plan_closed');return
  self.log(report['id'],'categorized','Categorized as '+brief['category_label'],'Based on received source claims')
  from .worlds import report_world
  campus=report_world(report)=='usc'
  if not campus:self.import_closures(report,brief)
  from .usc_ops import feature as usc_feature,on_report as usc_report
  usc=usc_feature(report)
  if usc:usc_report(self.d,report)
  geo=brief['location']
  if campus and not usc:
   geo=None;brief['location']=None;brief['response_required']=True;report['brief']=brief;self.store.put('report','operator',report,event='campus_location_review_required')
  if not campus and any(str(c['location'].get('feature_id','')).startswith('usc-') for c in report['claims']):
   geo=None;brief['location']=None;brief['response_required']=True;report['brief']=brief;self.store.put('report','operator',report,event='city_location_review_required')
  if usc:
   plan['state']='campus_facilities';self.release_report(report['id'])
  elif not brief['response_required']:
   plan['state']='information_only';self.release_report(report['id'])
  elif not geo:
   plan['state']='location_needed';self.task(plan,'location','Confirm event location','Confirm where the incident happened. The caller’s position or a fictional site name can’t be used as its real address.');self.release_report(report['id'])
  else:
   self.log(report['id'],'located','Located '+geo['label'],'OpenStreetMap '+geo['accuracy']+' match; source location still needs review if uncertain')
   if not self.config()['enabled'] or not self.config()['auto_assign']:
    plan['state']='automation_paused';self.task(plan,'assignment','Review resource assignment','Automatic unit assignment is paused.')
   else:self.assign(report,plan)
  for c in report['claims']:
   if c['assertion'] in ['uncertain','hearsay'] and re.search(r'inside|trapped|injured|danger',c['excerpt'],re.I):self.task(plan,'uncertainty','Confirm '+('occupancy' if 'inside' in c['excerpt'].lower() else 'critical detail'),c['excerpt'],'urgent')
  if report.get('needs_urgent_review') or report['urgency']=='critical':
   if self.config()['enabled'] and self.config()['auto_escalate']:
    self.task(plan,'supervisor','Supervisor review opened','Urgent or uncertain details need a supervisor’s review. This task stays in the demo.','urgent');self.log(report['id'],'escalated','Opened supervisor review','No external agency or emergency line was contacted.')
  plan['caller_draft']=self.caller_draft(report,plan)
  if geo:
   for task in plan['tasks']:
    if task['kind']=='location' and task['state']=='open':task.update(state='auto_resolved',operator_reason='A real-world event location is now associated with the report.')
  if self.config()['enabled']:
   audiences=[]
   if report['urgency']=='critical' or report.get('needs_urgent_review'):audiences.append('Operations demo desk')
   if geo and brief['category'] in ['fire','access','safety']:audiences.append('Public demo board')
   plan['prepared_advisory_ids']=[]
   for audience in audiences:
    advisory=self.advisory(report['id'],audience,plan_override=plan,automatic=True);plan['prepared_advisory_ids'].append(advisory['id']);self.log(report['id'],'prepared:'+audience,'Prepared '+('a supervisor contact note' if audience=='Operations demo desk' else 'a public advisory'),'Exact wording and audience require review. Local demo channel only.')
  if brief['category'] in ['fire','access','safety']:
   optional=self.task(plan,'announcement','Review a public advisory draft','Audience, verified location and exact wording need approval. Local demo board only.','optional')
   if optional['state']=='open':optional['state']='optional'
  self.store.put('plan','operator',plan,event='response_plan_updated')
 def import_closures(self,report,brief):
  changed=False
  for claim in report['claims']:
   if claim['kind']!='access' or claim['assertion']!='asserted' or not re.search(r'\b(blocked|closed|obstructed|impassable)\b',claim['excerpt'],re.I) or re.search(r'\b(not blocked|not closed|unblocked)\b',claim['excerpt'],re.I):continue
   id=stable('closure:'+report['id']+':'+claim['id'])
   if self.store.get(id,'closure'):continue
   near=claim['location'].get('geo') or brief['location'];keys=self.map.closure_edges(claim['excerpt']+' '+claim['location']['raw_text'],near)
   if not keys:continue # Location review remains in the incident plan; don't close an arbitrary road.
   self.store.put('closure','operator',{'id':id,'report_id':report['id'],'claim_id':claim['id'],'label':self.map.edges[keys[0]]['name'],'edge_ids':keys,'coordinates':[self.map.edges[k]['coordinates'] for k in keys],'state':'active','reported':True,'verification':'reported, unverified','reason':claim['excerpt'],'created_at':now(),'expires_at':time.time()+1800},event='reported_road_closed');changed=True
   self.log(report['id'],'closure','Avoiding reported road blockage',claim['excerpt'])
  # A later, asserted clearance must name the same road and mapped segment.
  for claim in report['claims']:
   if claim['location']['role']=='reporter' or claim['assertion']!='asserted' or not re.search(r'\b(?:is|has been|is now) (?:clear|cleared|open|reopened|passable)\b',claim['excerpt'],re.I) or re.search(r'\b(?:not|maybe|might|seems|looks|if|until|heard|told|think|believe)\b',claim['excerpt'],re.I):continue
   near=claim['location'].get('geo') or brief['location'];keys=set(self.map.closure_edges(claim['excerpt']+' '+claim['location']['raw_text'],near))
   if not keys:continue
   for closure in self.active_closures():
    if closure.get('report_id')==report['id'] or not keys.intersection(closure['edge_ids']):continue
    previous=self.store.get(closure.get('report_id',''),'report')
    old_time=previous.get('observed_at') or previous.get('captured_at') if previous else None
    new_time=report.get('observed_at') or report.get('captured_at')
    if old_time and new_time and new_time<old_time:continue
    closure.update(state='reopened',verification='Cleared by later reviewed report',cleared_by_report=report['id'],clearance_excerpt=claim['excerpt'],cleared_at=now());self.store.put('closure','operator',closure,event='road_cleared_by_report');changed=True
    self.log(report['id'],'cleared:'+closure['id'],'Reopened '+closure['label'],claim['excerpt'],key='cleared:'+closure['id'])
  if changed:self.bump_closures();self.recompute_routes()
 def bump_closures(self):
  cfg=self.config();cfg['closure_revision']+=1;self.store.put('config','operator',cfg,event='closure_revision_changed')
 def route_for(self,unit,destination):
  try:r=self.map.route(unit['position'],destination,self.excluded())
  except ValueError as e:return {'status':'outside_coverage','reason':str(e),'routes':[]}
  r['closure_revision']=self.config()['closure_revision'];r['avoided_closures']=[{'id':c['id'],'label':c['label'],'verification':c['verification']} for c in self.active_closures()];return r
 def resource_signature(self):return hashlib.sha256(json.dumps([(u['id'],u['status'],u.get('assignment_id')) for u in self.store.list('unit')]+[self.config()['closure_revision'],sorted(q['provider_id'] for q in self.store.list('unit_queue','operator') if q['world']=='city' and q['items'])],sort_keys=True).encode()).hexdigest()
 def required_capabilities(self,report,brief):
  needed=[CATEGORIES[brief['category']]['capability']]
  if any(c['assertion'] not in ['negated','hypothetical'] and c['kind']=='self_harm' for c in report['claims']) and 'medical' not in needed:needed.append('medical')
  if needed[0]=='fire' and any(c['assertion']=='asserted' and re.search(r'\binjured|unconscious|not breathing\b',c['excerpt'],re.I) for c in report['claims']):needed.append('medical')
  return [cap for cap in needed if cap]
 def reconcile_released_plans(self):
  # A manual unit release must not leave a phantom assignment or be silently undone.
  from .aggregation import members
  from .worlds import report_world
  for plan in self.store.list('plan','operator'):
   if plan['state'] not in ['assigned','route_blocked']:continue
   report=self.store.get(plan['report_id'],'report')
   if not report or report['status'] in ['resolved','superseded'] or report_world(report)!='city':continue
   related={r['id'] for r in members(self.d,report)}
   active=[a for a in self.store.list('assignment','operator') if a['report_id'] in related and a['state']!='released']
   missing=set(self.required_capabilities(report,plan['brief']))-{a['capability'] for a in active}-set(plan.get('completed_capabilities',[]))
   if not missing:continue
   plan.update(state='resource_needed',assignment_review_required=True,updated_at=now(),resource_signature=self.resource_signature())
   for cap in sorted(missing):
    reason=cap.capitalize()+' unit was released. Check available units to assign a replacement.'
    plan.setdefault('shortages',{})[cap]=reason
    self.task(plan,'resource:'+cap,'Review '+cap+' coverage',reason,'urgent')['state']='open'
   self.store.put('plan','operator',plan,event='released_assignment_review_required')
 def assign(self,report,plan):
  from .dispatch_queue import reserved
  plan['state']='planning'
  needed=self.required_capabilities(report,plan['brief'])
  from .aggregation import members
  related={r['id'] for r in members(self.d,report)}
  existing=[a for a in self.store.list('assignment','operator') if a['report_id'] in related and a['state']!='released']
  plan['assignment_ids']=list(dict.fromkeys(plan['assignment_ids']+[a['id'] for a in existing]))
  for cap in needed:
   if any(cap in self.store.get(a['unit_id'],'unit')['capabilities'] for a in existing):continue
   options=[];candidates=[u for u in self.store.list('unit','operator') if cap in u['capabilities']];available=[u for u in candidates if u['status']=='available' and not reserved(self.d,'city',u['id'])]
   if not available and report.get('triage',{}).get('score',0)>=90:
    transferable=[]
    for candidate in candidates:
     current=self.store.get(candidate.get('assignment_id',''),'assignment')
     previous=self.store.get(current['report_id'],'report') if current else None
     if current and current['state']=='assigned' and previous and assess_report(previous)['score']+30<report['triage']['score']:transferable.append((assess_report(previous)['score'],candidate,current,previous))
    if transferable:
     _,unit,old,prior=min(transferable,key=lambda x:x[0]);old.update(state='released',updated_at=now(),release_reason='Unstarted demo assignment reprioritized for an immediate threat.');self.store.put('assignment','operator',old,event='assignment_reprioritized');unit.update(status='available',assignment_id=None);self.store.put('unit','operator',unit,event='unit_reprioritized');prior_plan=self.store.get(prior['id'],'plan')
     if prior_plan:
      prior_plan['state']='resource_needed';self.task(prior_plan,'resource:'+cap,'Waiting for '+cap+' coverage','An unstarted demo unit was reassigned to a higher-priority threat.','urgent')['state']='open';prior_plan.setdefault('shortages',{})[cap]='An unstarted demo unit was reassigned to a higher-priority threat.';self.store.put('plan','operator',prior_plan,event='lower_priority_waiting')
     self.log(report['id'],'reprioritized:'+cap,'Reassigned an unstarted demo unit',unit['name']+' moved from a lower-priority case. En route and on-scene units are never automatically diverted.',key='reprioritized:'+old['id'])
   for unit in self.store.list('unit','operator'):
    if unit['status']!='available' or cap not in unit['capabilities'] or reserved(self.d,'city',unit['id']):continue
    route=self.route_for(unit,plan['brief']['location'])
    if route['status']=='ready':options.append((route['routes'][0]['travel_seconds'],unit,route))
   if not options:
    all_units=[u for u in self.store.list('unit','operator') if cap in u['capabilities']];free=[u for u in all_units if u['status']=='available'];reason=('No '+cap+' unit is in the demo roster.' if not all_units else str(len(all_units))+' '+cap+' unit(s) are busy or unavailable.' if not free else 'Available '+cap+' units are reserved for queued work.' if all(reserved(self.d,'city',u['id']) for u in free) else 'Available '+cap+' units have no supported route to this location.');self.task(plan,'resource:'+cap,'Review '+cap+' coverage',reason,'urgent')['state']='open';plan['state']='resource_needed';plan.setdefault('shortages',{})[cap]=reason;continue
   plan.setdefault('shortages',{}).pop(cap,None)
   _,unit,route=min(options,key=lambda x:x[0]);id=stable('assignment:'+report['id']+':'+cap)
   assignment={'id':id,'report_id':report['id'],'unit_id':unit['id'],'capability':cap,'state':'assigned','route':route,'selected_route':'recommended','created_at':now(),'updated_at':now(),'mode':'demo','reason':'Closest available demo unit with the right capability and a route around reported blockages.'}
   self.store.put('assignment','operator',assignment,event='unit_autoassigned');unit.update(status='assigned',assignment_id=id);self.store.put('unit','operator',unit,event='unit_reserved');plan['assignment_ids']=list(dict.fromkeys(plan['assignment_ids']+[id]));existing.append(assignment);self.log(report['id'],'assigned:'+cap,'Autoassigned '+unit['name'],assignment['reason'])
  if all(any(cap in self.store.get(a['unit_id'],'unit')['capabilities'] for a in existing) for cap in needed):
   plan['state']='assigned' if all(a['route']['status']=='ready' for a in existing) else 'route_blocked'
   for task in plan['tasks']:
    if task['kind'].startswith('resource:') and task['state']=='open':task.update(state='auto_resolved',operator_reason='A suitable demo unit is now assigned.')
  plan['resource_signature']=self.resource_signature()
 def caller_draft(self,report,plan):
  place=plan['brief']['location'];text='We received your report'+(' at '+place['label'] if place else '')+'.'
  if not place:text+=' Please confirm the event address or nearest intersection.'
  if any(c['kind']=='people_inside' and c['assertion']=='uncertain' for c in report['claims']):text+=' Can you confirm whether anyone is still inside?'
  elif any(t['kind']=='uncertainty' for t in plan['tasks']):text+=' What can you confirm from your current location?'
  return text
 def release_report(self,report_id):
  for a in self.store.list('assignment','operator'):
   if a['report_id']!=report_id or a['state']=='released':continue
   from .aggregation import members
   source=self.store.get(report_id,'report');others=[r for r in members(self.d,source) if r['id']!=report_id] if source else []
   if others:
    a.update(report_id=max(others,key=lambda r:r.get('triage',{}).get('score',0))['id'],updated_at=now());self.store.put('assignment','operator',a,event='assignment_retained_for_linked_reports');continue
   a.update(state='released',updated_at=now());self.store.put('assignment','operator',a,event='assignment_released');u=self.store.get(a['unit_id'],'unit')
   if u and u.get('assignment_id')==a['id']:u.update(status='available',assignment_id=None);self.store.put('unit','operator',u,event='unit_released')
   if u:
    from .dispatch_queue import advance
    advance(self.d,'city',u['id'])
 def supersede_report(self,report_id):
  self.release_report(report_id);plan=self.store.get(report_id,'plan')
  if plan:plan['state']='closed';self.store.put('plan','operator',plan,event='plan_superseded')
  changed=False
  for c in self.store.list('closure','operator'):
   if c.get('report_id')==report_id and c['state'] in ['active','stale']:
    c['state']='superseded';self.store.put('closure','operator',c,event='closure_source_corrected');changed=True
  if changed:self.bump_closures();self.recompute_routes()
 def recompute_routes(self):
  for a in self.store.list('assignment','operator'):
   if a['state']=='released':continue
   report=self.store.get(a['report_id'],'report');destination=report.get('brief',{}).get('location') if report else None
   if not destination:continue
   unit=self.store.get(a['unit_id'],'unit');old=a['route'];r=self.route_for(unit,destination);a.update(route=r,selected_route='recommended',updated_at=now());self.store.put('assignment','operator',a,event='route_recomputed')
   if old.get('routes') and r.get('routes') and old['routes'][0]['edge_ids']!=r['routes'][0]['edge_ids']:self.log(a['report_id'],'rerouted','Rerouted around reported closures','Road preview recalculated against closure revision '+str(r['closure_revision']),key='reroute:'+str(r['closure_revision'])+':'+a['id'])
   if r['status']=='ready' and old.get('status')!='ready':
    plan=self.store.get(a['report_id'],'plan')
    if plan:
     plan['state']='assigned';task=self.task(plan,'route_restored','Route available again','A supported route is now available. Review it before moving this unit.');task['state']='open'
     for prior in plan['tasks']:
      if prior['kind']=='route_blocked' and prior['state']=='open':prior.update(state='auto_resolved',operator_reason='Supported route restored after the road update.')
     self.store.put('plan','operator',plan,event='route_available_again')
    self.log(a['report_id'],'route_restored','Route available again','The unit stays on hold until the operator marks it en route.',key='restored:'+str(r['closure_revision'])+':'+a['id'])
   if r['status']!='ready':
    if unit['status'] in ['assigned','en_route']:
     unit['status']='holding';self.store.put('unit','operator',unit,event='demo_unit_route_hold');a['state']='holding';self.store.put('assignment','operator',a,event='assignment_route_hold')
    plan=self.store.get(a['report_id'],'plan')
    if plan:self.task(plan,'route_blocked','Review route access',r['reason'],'urgent');plan['state']='route_blocked';self.store.put('plan','operator',plan,event='route_review_needed')
 def tick(self):
  if time.time()-self.last_tick<3:return
  self.last_tick=time.time();self.bootstrap();changed=False
  for c in self.store.list('closure','operator'):
   if c['state']=='active' and c['expires_at']<=time.time():c['state']='stale';c['verification']='stale report, reconfirm';self.store.put('closure','operator',c,event='road_report_stale');changed=True
   if c['state']=='stale' and c.get('report_id'):
    plan=self.store.get(c['report_id'],'plan')
    if plan and not any(t['kind']=='closure_stale:'+c['id'] for t in plan['tasks']):
     self.task(plan,'closure_stale:'+c['id'],'Reconfirm road closure','This road report is over 30 minutes old. Routes will avoid it until you check it.');self.store.put('plan','operator',plan,event='closure_reconfirmation_needed')
  if changed:self.bump_closures();self.recompute_routes()
  self.reconcile_released_plans()
  from .dispatch_queue import advance_all
  advance_all(self.d)
  for report in sorted(self.store.list('report','operator'),key=lambda r:-assess_report(r)['score']):
   plan=self.store.get(report['id'],'plan')
   if not plan or plan.get('triage_policy')!=POLICY:self.on_report(report)
   elif plan['state'] in ['resource_needed','automation_paused'] and not plan.get('assignment_review_required') and self.config()['enabled'] and self.config()['auto_assign'] and plan.get('resource_signature')!=self.resource_signature():self.on_report(report)
  if self.config()['enabled'] and self.config()['auto_escalate']:
   for m in self.store.list('message'):
    if m['kind']!='instruction' or m.get('superseded_by') or time.time()-m['issued']<120:continue
    inbox=self.store.get(m['id'],'inbox');qs=inbox.get('questions',[]) if inbox else []
    if not qs or not any(q['state']=='open' for q in qs):continue
    report=next((r for r in reversed(self.store.list('report','operator')) if r['session_id']==m['session_id'] and r['status'] not in ['resolved','superseded']),None)
    plan=self.store.get(report['id'],'plan') if report else None
    if plan and not any(t['kind']=='followup:'+m['id'] for t in plan['tasks']):self.task(plan,'followup:'+m['id'],'Follow up on an unanswered question','The question has been open for two minutes. Acknowledging the message doesn’t answer it.');self.store.put('plan','operator',plan,event='followup_flagged')
 def snapshot(self):
  return {'mode':'demo','config':self.config(),'atlas':self.map.public(),'units':self.store.list('unit','operator'),'plans':self.store.list('plan','operator'),'assignments':self.store.list('assignment','operator'),'closures':self.store.list('closure','operator'),'actions':self.store.list('action','operator')[-100:],'announcements':self.store.list('announcement','operator')}
 def set_unit(self,id,body):
  u=self.store.get(id,'unit')
  if not u:raise ValueError('Demo unit not found')
  if body['version']!=u['version']:raise Conflict('Unit changed. Refresh before updating it.')
  status=body.get('status',u['status'])
  if status not in ['available','assigned','en_route','on_scene','holding','unavailable']:raise ValueError('Unknown demo unit status')
  if status in ['assigned','en_route','on_scene','holding'] and not u.get('assignment_id'):raise ValueError('Assign a report first')
  if status=='en_route' and u.get('assignment_id') and self.store.get(u['assignment_id'],'assignment')['route']['status']!='ready':raise ValueError('No supported route is available. Review access before marking en route.')
  if status in ['available','unavailable'] and u.get('assignment_id'):
   a=self.store.get(u['assignment_id'],'assignment');a['state']='released';self.store.put('assignment','operator',a,event='assignment_released');u['assignment_id']=None
  elif u.get('assignment_id'):
   a=self.store.get(u['assignment_id'],'assignment');a['state']=status;self.store.put('assignment','operator',a,event='demo_unit_progress')
  if status=='on_scene' and u.get('assignment_id'):
   assignment=self.store.get(u['assignment_id'],'assignment');report=self.store.get(assignment['report_id'],'report');location=report.get('brief',{}).get('location')
   if location:u['position']={'lon':location['lon'],'lat':location['lat']};u['position_source']='operator_marked_arrival'
  u['status']=status;u=self.store.put('unit','operator',u,expected=body['version'],event='demo_unit_changed')
  self.reconcile_released_plans()
  if status=='available':
   from .dispatch_queue import advance
   advance(self.d,'city',id)
  return self.store.get(id,'unit')
 def signature(self,report):return hashlib.sha256(json.dumps({'claims':report['claims'],'observed_at':report.get('observed_at')},sort_keys=True).encode()).hexdigest()
 def advisory(self,report_id,audience='Public demo board',plan_override=None,automatic=False):
  report=self.store.get(report_id,'report');plan=plan_override or self.store.get(report_id,'plan')
  if not report or not plan:raise ValueError('Received incident not found')
  signature=self.signature(report);id=stable('advisory:'+report_id+':'+audience+':'+signature) if automatic else uid()
  old=self.store.get(id,'announcement')
  if old:return old
  location=plan['brief']['location'];name=location['label'] if location else 'an unconfirmed location'
  text='A '+plan['brief']['category_label'].lower()+' report near '+name+' is being reviewed.'
  if plan['brief']['category']=='access':text+=' Reported road access may be restricted. Verify an alternative route before traveling.'
  text+=' This is a demo message, not an official public alert.'
  obj={'id':id,'source_signature':signature,'automatic':automatic,'report_id':report_id,'audience':audience,'text':text,'state':'draft','created_at':now(),'mode':'demo','approval':None};return self.store.put('announcement','operator',obj,event='advisory_prepared')
 def approve_advisory(self,id,body):
  obj=self.store.get(id,'announcement')
  if not obj:raise ValueError('Draft not found')
  if obj['state']=='published_demo':return obj
  if obj['version']!=body['version']:raise Conflict('Draft changed. Review the current words.')
  if obj.get('source_signature')!=self.signature(self.store.get(obj['report_id'],'report')):raise Conflict('Incident details changed. Review a newly prepared advisory.')
  text=body.get('text','').strip();audience=body.get('audience','').strip()
  if not text or len(text)>2000 or not audience or len(audience)>120:raise ValueError('Enter audience and 1–2,000 characters of exact text.')
  obj.update(text=text,audience=audience,state='approved',approval={'hash':hashlib.sha256(json.dumps([text,audience],ensure_ascii=False).encode()).hexdigest(),'at':now()})
  return self.store.put('announcement','operator',obj,expected=body['version'],event='advisory_approved')
 def publish_advisory(self,id,version):
  obj=self.store.get(id,'announcement')
  if not obj:raise ValueError('Draft not found')
  if obj['state']=='published_demo':return obj
  if obj['version']!=version or obj['state']!='approved' or not obj.get('approval'):raise Conflict('Approve the current wording and audience first.')
  if obj.get('source_signature')!=self.signature(self.store.get(obj['report_id'],'report')):raise Conflict('Incident details changed after approval. Review a fresh advisory.')
  if obj['approval']['hash']!=hashlib.sha256(json.dumps([obj['text'],obj['audience']],ensure_ascii=False).encode()).hexdigest():raise Conflict('Approval no longer matches.')
  obj.update(state='published_demo',published_at=now());self.log(obj['report_id'],'advisory_published','Published to '+obj['audience'],'Local demonstration board only.',key='advisory:'+id)
  return self.store.put('announcement','operator',obj,expected=version,event='demo_advisory_published')

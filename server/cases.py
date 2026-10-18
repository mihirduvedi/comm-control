"""Operator-owned closeout and handover. Sources and delivery state stay unchanged."""
from .store import Conflict, now, uid


def case_snapshot(d, id):
 r=d.store.get(id,'report')
 if not r:raise ValueError('Received incident not found')
 plan=d.store.get(id,'plan')
 messages=[m for m in d.operator_snapshot()['messages'] if m['session_id']==r['session_id']]
 checks=[{'kind':'review','label':t['title']} for t in (plan or {}).get('tasks',[]) if t['state']=='open']
 for m in messages:
  if m.get('superseded_by'):continue
  if m['state'] not in ['received','expired','failed']:checks.append({'kind':'delivery','label':'An instruction is still '+m['state']})
  for q in m.get('question_states',[]):
   if q['state'] not in ['operator_reviewed','closed_unanswered']:checks.append({'kind':'question','label':q['text']})
 closures=[c for c in d.operations.active_closures() if c.get('report_id')==id]
 incident=d.store.get(r.get('incident_id',''),'incident')
 linked=[d.store.get(i,'report') for i in incident['report_ids']] if incident else [r]
 return {'report':r,'plan':plan,'checks':checks,'closures':closures,'messages':messages,
  'incident_reports':[x for x in linked if x],
  'assignments':[a for a in d.store.list('assignment','operator') if a['report_id']==id],
  'actions':[a for a in d.store.list('action','operator') if a['report_id']==id],
  'entries':[e for e in d.store.list('case_entry','operator') if e['report_id']==id],
  'related_reports':[x for x in d.store.list('report','operator') if x['session_id']==r['session_id'] and x['id']!=id],
  'mode':'Local demo case record. Closure does not prove safety or caller comprehension.'}


def update_case(d,id,body):
 if body.get('action') in ['archive','restore']:return archive_case(d,id,body)
 with d.store.transaction():
  current=case_snapshot(d,id);r=current['report']
  if type(body.get('version')) is not int or body['version']!=r['version']:raise Conflict('Incident changed. Reload and review it before saving.')
  if r.get('superseded_by') or r['status']=='superseded':raise ValueError('Use the replacement report for new case updates.')
  if r.get('archived_at') and body.get('action') in ['close','reopen','monitor']:raise ValueError('Restore this incident before reopening or changing its response.')
  action=body.get('action');note=body.get('note','');owner=body.get('owner',r.get('owner') or '')
  if not isinstance(note,str) or not 3<=len(note.strip())<=2000:raise ValueError('Add a note between 3 and 2,000 characters.')
  if not isinstance(owner,str) or len(owner)>100:raise ValueError('Owner must be a name of at most 100 characters.')
  if action not in ['note','monitor','close','reopen']:raise ValueError('Choose a case action.')
  if action=='close':
   if r['status']=='resolved':raise Conflict('This incident is already closed.')
   if current['checks'] and body.get('acknowledge_open_items') is not True:raise ValueError('Review and explicitly acknowledge the outstanding items before closing.')
   r.update(status='resolved',closeout={'at':now(),'note':note.strip(),'owner':owner.strip(),'outstanding_items':current['checks'],'retained_closure_ids':[c['id'] for c in current['closures']]})
  elif action=='reopen':
   if r['status']!='resolved':raise ValueError('Only a closed incident can be reopened.')
   r['status']='open'
  elif action=='monitor':
   if r['status']=='resolved':raise ValueError('Reopen this incident before monitoring it.')
   r['status']='monitoring'
  r['owner']=owner.strip() or None
  saved=d.store.put('report','operator',r,expected=body['version'],event='case_'+action)
  d.store.put('case_entry','operator',{'id':uid(),'report_id':id,'action':action,'note':note.strip(),'owner':r['owner'],'at':now(),'actor':'operator','outstanding_items':current['checks'] if action=='close' else []},event='case_entry_added')
  if action in ['close','monitor','reopen']:d.operations.on_report(saved)
  return case_snapshot(d,id)


def archive_case(d,id,body):
 with d.store.transaction():
  current=case_snapshot(d,id);r=current['report'];action=body['action'];note=body.get('note','')
  if type(body.get('version')) is not int or body['version']!=r['version']:raise Conflict('Incident changed. Reload before removing or restoring it.')
  if not isinstance(note,str) or not 3<=len(note.strip())<=2000:raise ValueError('Add a reason between 3 and 2,000 characters.')
  reports=current['incident_reports'];versions=body.get('report_versions',{})
  if len(reports)>1 and any(versions.get(x['id'])!=x['version'] for x in reports):raise Conflict('A linked report changed. Review the incident again.')
  checks={x['id']:case_snapshot(d,x['id'])['checks'] for x in reports}
  if action=='archive' and any(checks[x['id']] for x in reports if x['status']!='resolved') and body.get('acknowledge_open_items') is not True:raise ValueError('Review the outstanding items before removing this incident.')
  if action=='restore' and not any(x.get('archived_at') for x in reports):raise ValueError('This incident is not in the archive.')
  for item in reports:
   if action=='archive':
    if item.get('archived_at'):continue
    if item['status']!='resolved':item.update(status='resolved',closeout={'at':now(),'note':note.strip(),'owner':item.get('owner'),'outstanding_items':checks[item['id']],'retained_closure_ids':[c['id'] for c in d.operations.active_closures() if c.get('report_id')==item['id']]})
    item.update(archived_at=now(),archive_reason=note.strip())
   else:
    item.pop('archived_at',None);item.pop('archive_reason',None)
   saved=d.store.put('report','operator',item,event='case_'+action)
   d.store.put('case_entry','operator',{'id':uid(),'report_id':item['id'],'action':action,'note':note.strip(),'owner':item.get('owner'),'at':now(),'actor':'operator','outstanding_items':checks[item['id']] if action=='archive' else []},event='case_entry_added')
   if action=='archive':d.operations.on_report(saved)
  return case_snapshot(d,id)


def register_cases(app,d,operator,json_body,idem):
 from fastapi import Depends,Request
 @app.get('/api/reports/{id}/case')
 def read_case(id,a=Depends(operator)):return case_snapshot(d,id)
 @app.post('/api/reports/{id}/case')
 async def mutate_case(id,request:Request,a=Depends(operator)):
  body=await json_body(request)
  return idem(request,a,body,lambda:update_case(d,id,body))

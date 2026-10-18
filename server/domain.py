"""Comm Control domain: origins, approvals, received projections and human obligations."""
import asyncio
import hashlib
import json
import secrets
import time
from pathlib import Path
from uuid import UUID,uuid5,NAMESPACE_URL
from .store import Store,Conflict,uid,now,dump
from .site import SITE_ID,BY_ID,resolve,urgency,sitepack
from .transport import Transport,decode,un64
from . import models
from .observation_time import observation_time,epoch
from .operations import Operations
from .speakers import caller_voice,OPERATOR_VOICE
from .threats import rank_claims,assess

OPERATOR='10d375bf-40e9-494b-adc3-3795984fde64'
MAX_SESSIONS_PER_WORLD=100

class Domain:
 def __init__(self,data_dir):
  self.dir=Path(data_dir);self.dir.mkdir(parents=True,exist_ok=True);self.dir.chmod(0o700)
  self.store=Store(self.dir/'comm-control.sqlite3')
  secretfile=self.dir/'run.json'
  if secretfile.exists():self.secrets=json.loads(secretfile.read_text())
  else:
   self.secrets={'operator_token':secrets.token_urlsafe(32),'facilitator_token':secrets.token_urlsafe(32),'key':secrets.token_hex(32)}
   secretfile.write_text(json.dumps(self.secrets));secretfile.chmod(0o600)
  self.transport=Transport(self.store,bytes.fromhex(self.secrets['key']),self.receive)
  self.workers=[];self.outgoing_streak=0
  with self.store.transaction():
   for r in self.store.list('report','operator'):
    if 'observation_time_status' not in r:
     r.update(issued_at=r.get('observed_at'),observed_at=None,observation_time_status='unknown',observation_time_raw='');self.store.put('report','operator',r,event='time_semantics_migrated')
  with self.store.transaction():
   for j in self.store.list('job'):
    if j['state'] in ['transcribing','extracting']:
     j.update(state='failed',error='Processing interrupted by restart. Your source is retained; retry to continue.');self.store.put('job',j['origin'],j,event='job_interrupted')

  with self.store.transaction():
   for session in self.store.list('session'):
    if not session.get('demo_voice'):
     session['demo_voice']=caller_voice(session['display_name']);self.store.put('session','operator',session,event='demo_speaker_assigned')
  self.operations=Operations(self)

 def actor(self,token):
  if secrets.compare_digest(token or '',self.secrets['operator_token']):return {'id':OPERATOR,'role':'operator'}
  if secrets.compare_digest(token or '',self.secrets['facilitator_token']):return {'id':OPERATOR,'role':'facilitator'}
  for session in self.store.list('session'):
   if secrets.compare_digest(token or '',session['token']):return {'id':session['endpoint_id'],'session_id':session['id'],'role':'field'}
  raise PermissionError('Open the authorized launch link for this local demo.')

 def create_session(self,name,world=None):
  from .worlds import validate
  validate(world)
  from .worlds import session_world
  if sum(session_world(self,s)==(world or 'city') for s in self.store.list('session'))>=MAX_SESSIONS_PER_WORLD:raise ValueError('This workspace supports 100 reporting sessions. Reuse an existing reporter or start a saved new test.')
  id=uid();obj={'id':id,'site_id':SITE_ID,'endpoint_id':uid(),'display_name':name.strip()[:60] or 'Field reporter','preferred_language':'en','created_at':now(),'token':secrets.token_urlsafe(32)}
  obj['demo_voice']=caller_voice(obj['display_name'])
  if world:obj['world']=world
  with self.store.transaction():return self.store.put('session','operator',obj,event='session_created')

 def session(self,id):
  s=self.store.get(id,'session')
  if not s:raise ValueError('Reporting session not found')
  return s

 def visible_session(self,s):return {k:v for k,v in s.items() if k!='token'}

 def source_authority(self,actor,session_id,direction):
  session=self.session(session_id)
  if direction=='outgoing':
   if actor['role']!='operator':raise PermissionError('Only the operator can compose instructions.')
   return OPERATOR
  if actor['role']!='field' or actor['session_id']!=session_id:raise PermissionError('Only this reporting endpoint can access its unsent source.')
  return session['endpoint_id']

 def new_job(self,origin,session_id,direction,text=None,audio_path=None,reply_to=None,response_action='replied'):
  if len([j for j in self.store.list('job') if j['state'] in ['queued','transcribing','extracting']])>=50:raise OverflowError('Processing queue is full. Your local draft is retained; try again later.')
  if text is not None and (not text.strip() or len(text)>6000):raise ValueError('Enter between 1 and 6,000 characters.')
  source={'id':uid(),'session_id':session_id,'origin':origin,'direction':direction,'captured_at':now(),'audio_path':str(audio_path) if audio_path else None,'origin_label':'voice' if audio_path else 'typed','text':text,'revision':1,'reply_to':reply_to,'response_action':response_action}
  job={'id':uid(),'source_id':source['id'],'origin':origin,'session_id':session_id,'direction':direction,'state':'queued','created_at':now(),'error':None,'draft_id':None,'attempts':0}
  from .demo_budget import visitor
  if visitor.get():job['public_visitor']=visitor.get()
  with self.store.transaction():
   self.store.put('source',origin,source,event='source_captured');return self.store.put('job',origin,job,event='job_queued')

 async def process_next(self):
  jobs=[j for j in self.store.list('job') if j['state']=='queued']
  if not jobs:return False
  out=[j for j in jobs if j['direction']=='outgoing'];inbound=[j for j in jobs if j['direction']!='outgoing']
  job=(out if out and (self.outgoing_streak<2 or not inbound) else inbound or out)[0]
  self.outgoing_streak=self.outgoing_streak+1 if job['direction']=='outgoing' else 0
  source=self.store.get(job['source_id']);start=time.monotonic()
  from .demo_budget import visitor
  visitor_token=visitor.set(job.get('public_visitor'))
  try:
   if source['audio_path'] and not source.get('stt_model'):
    with self.store.transaction():job.update(state='transcribing',attempts=job['attempts']+1);job=self.store.put('job',job['origin'],job,event='job_running')
    result=await models.transcribe(Path(source['audio_path']))
    source.update(text=result['text'],segments=result['segments'],stt_model=result['model'],stt_ms=result['processing_ms'])
    with self.store.transaction():source=self.store.put('source',source['origin'],source,event='transcript_created')
   with self.store.transaction():job['state']='extracting';job=self.store.put('job',job['origin'],job,event='job_running')
   result=await (models.outgoing(source['text']) if job['direction']=='outgoing' else models.extraction(source['text']))
   draft={'id':uid(),'source_id':source['id'],'source_revision':source['revision'],'origin':source['origin'],'session_id':source['session_id'],'direction':source['direction'],'source_text':source['text'],'origin_label':source['origin_label'],'captured_at':epoch(source['captured_at']),'correction_of':source.get('correction_of'),'correction_reason':source.get('correction_reason',''),'created_at':now(),'source_hash':hashlib.sha256(source['text'].encode()).hexdigest(),'review_state':'unreviewed','approval':None,'recipient_ids':[source['session_id']],'expires_at':time.time()+300,'reply_to':source.get('reply_to'),'response_action':source.get('response_action','replied'),**result}
   with self.store.transaction():
    draft=self.store.put('draft',source['origin'],draft,event='draft_ready');job.update(state='ready',draft_id=draft['id'],processing_ms=round((time.monotonic()-start)*1000));self.store.put('job',job['origin'],job,event='job_ready')
  except Exception as e:
   with self.store.transaction():job.update(state='failed',error=str(e)[:350]);self.store.put('job',job['origin'],job,event='job_failed')
  finally:visitor.reset(visitor_token)
  return True

 def manual_draft(self,origin,session_id,text,claims,direction='inbound',reply_to=None,response_action='replied'):
  # Deliberately manual path, never an invisible AI fallback.
  source={'id':uid(),'session_id':session_id,'origin':origin,'direction':direction,'captured_at':now(),'text':text,'revision':1,'audio_path':None,'origin_label':'manual','reply_to':reply_to}
  if direction=='outgoing':result={'text':text,'questions':[x.strip()+'?' for x in text.split('?')[:-1]],'critical_fields':models.critical_fields(text),'issues':[]}
  else:result=models.validate_extraction(text,{'event_type':'manual report','facts':claims})
  draft={'id':uid(),'source_id':source['id'],'source_revision':1,'origin':origin,'session_id':session_id,'direction':direction,'source_text':text,'source_hash':hashlib.sha256(text.encode()).hexdigest(),'origin_label':'manual','captured_at':epoch(source['captured_at']),'created_at':now(),'review_state':'unreviewed','approval':None,'recipient_ids':[session_id],'expires_at':time.time()+300,'reply_to':reply_to,'response_action':response_action,**result}
  with self.store.transaction():
   self.store.put('source',origin,source,event='manual_source');return self.store.put('draft',origin,draft,event='manual_draft_ready')

 def send_report(self,draft,reviewed=True):
  if draft.get('invalidated_by_source'):raise Conflict('Source transcript changed. Review the new interpretation before sending.')
  if draft['direction']=='outgoing':raise ValueError('Outgoing messages require approval.')
  if draft.get('sent_message_id'):return self.store.get(draft['sent_message_id'])
  payload={'source_id':draft['source_id'],'source_revision':draft['source_revision'],'source_hash':draft['source_hash'],'origin_label':draft['origin_label']+(' reviewed' if reviewed else ' unreviewed'),'claims':draft['claims'],'captured_at':draft.get('captured_at'),'correction_of':draft.get('correction_of'),'correction_reason':draft.get('correction_reason',''),'reply_to':draft.get('reply_to'),'response_action':draft.get('response_action','replied')}
  with self.store.transaction():
   m=self.transport.enqueue('correction' if draft.get('correction_of') else 'report',draft['session_id'],draft['origin'],OPERATOR,payload)
   draft.update(sent_message_id=m['id'],review_state='sender_reviewed' if reviewed else 'unreviewed');self.store.put('draft',draft['origin'],draft,event='report_sent')
  return m

 def approve(self,draft,expected):
  if draft['direction']!='outgoing':raise ValueError('This is not an instruction draft.')
  if draft['version']!=expected:raise Conflict('Instruction changed. Review the current version.')
  if not draft['text'].strip():raise ValueError('Instruction cannot be empty.')
  issues=models.instruction_issues(draft['source_text'],draft['text'])
  if issues:raise ValueError('Critical source details changed. Correct the text before approval: '+', '.join(x['value'] for x in issues))
  if not draft['recipient_ids']:raise ValueError('Choose at least one recipient.')
  if not 30<=draft['expires_at']-time.time()<=86400:raise ValueError('Expiry must be between 30 seconds and 24 hours from now.')
  for sid in draft['recipient_ids']:self.session(sid)
  if draft.get('replaces_message_id'):
   old=self.store.get(draft['replaces_message_id'],'message')
   if not old or old['kind']!='instruction' or any(sid!=old['session_id'] for sid in draft['recipient_ids']):raise ValueError('A replacement must target an instruction for the same recipient.')
  canonical={'replaces_message_id':draft.get('replaces_message_id'),'text':draft['text'],'recipients':sorted(draft['recipient_ids']),'expiry':draft['expires_at'],'source_revision':draft['source_revision'],'source_hash':draft['source_hash']}
  approval={'hash':hashlib.sha256(dump(canonical).encode()).hexdigest(),'canonical':canonical,'actor':OPERATOR,'at':now(),'draft_version':expected}
  with self.store.transaction():
   draft['approval']=approval;return self.store.put('draft',OPERATOR,draft,expected=expected,event='instruction_approved')

 def send_instruction(self,draft):
  if draft.get('sent_ids'):return [self.store.get(x) for x in draft['sent_ids']]
  a=draft.get('approval')
  if not a:raise Conflict('Review and approve this revision before sending.')
  current={'replaces_message_id':draft.get('replaces_message_id'),'text':draft['text'],'recipients':sorted(draft['recipient_ids']),'expiry':draft['expires_at'],'source_revision':draft['source_revision'],'source_hash':draft['source_hash']}
  if hashlib.sha256(dump(current).encode()).hexdigest()!=a['hash']:raise Conflict('Approval is stale. Review this revision again.')
  if draft['expires_at']<=time.time():raise ValueError('Instruction expired before send. Set a new expiry and review again.')
  with self.store.transaction():
   messages=[]
   for sid in draft['recipient_ids']:
    endpoint=self.session(sid)['endpoint_id']
    payload={'text':draft['text'],'questions':draft.get('questions',[]),'approval_hash':a['hash'],'source_hash':draft['source_hash'],'source_id':draft['source_id'],'language':'en','replaces_message_id':draft.get('replaces_message_id')}
    messages.append(self.transport.enqueue('instruction',sid,OPERATOR,endpoint,payload,expires=draft['expires_at']))
   draft['sent_ids']=[m['id'] for m in messages];self.store.put('draft',OPERATOR,draft,event='instruction_sent')
  return messages

 def receive(self,id,revision,d,body_hash,stamp):
  # Called within the transport's transaction only; received content is the sole operator projection input.
  kind=d['kind'];p=d['payload'];old=self.store.get('received:'+d['destination']+':'+id)
  if old and old['body_hash']!=body_hash:raise ValueError('Conflicting message revision hash')
  if kind=='receipt':
   original=self.store.get(p['message_id'],'message')
   if not original or original['destination']!=d['origin'] or original['origin']!=d['destination'] or original['body_hash']!=p['body_hash']:raise ValueError('Receipt mismatch')
   original.update(state='received',received_at=now(),expired_on_receipt=bool(p.get('expired')))
   self.store.put('message',original['origin'],original,event='device_receipt');return
  if old:
   if kind!='instruction' or self.store.get(id,'inbox').get('persisted'):
    self.transport.acknowledge(id,d['destination'],stamp,d['expires']<stamp)
   return
  if kind=='correction':
   target=self.store.get(p.get('correction_of',''),'report')
   if not target:
    if len(self.store.list('pending_correction'))>=32 and not self.store.get(id,'pending_correction'):raise ValueError('Pending correction capacity reached')
    if d['destination']!=OPERATOR or self.session(d['session_id'])['endpoint_id']!=d['origin']:raise ValueError('Wrong correction route')
    self.store.put('pending_correction','operator',{'id':id,'revision':revision,'packet':d,'body_hash':body_hash,'stamp':stamp,'state':'waiting_for_original'},event='correction_waiting')
    self.transport.acknowledge(id,OPERATOR,stamp,d['expires']<stamp);return
   if target['session_id']!=d['session_id']:raise ValueError('Correction cannot change another reporting session')
   if target.get('superseded_by') and target['superseded_by']!=id:raise ValueError('Original already corrected; correct the current revision')
  self.store.put('received',d['destination'],{'id':'received:'+d['destination']+':'+id,'message_id':id,'body_hash':body_hash,'at':now()})
  if kind in ['report','correction','urgent_attention']:
   if d['destination']!=OPERATOR:raise ValueError('Reports must arrive at the operator')
   if sum(not r.get('archived_at') for r in self.store.list('report','operator'))>=100:raise ValueError('Active report capacity reached. Remove an incident from the queue or start a saved new test.')
   session=self.session(d['session_id'])
   if session['endpoint_id']!=d['origin']:raise ValueError('Session/origin mismatch')
   if kind=='urgent_attention':
    claims=[{'id':uid(),'kind':'request','value':'Immediate assistance requested','count':None,'assertion':'asserted','excerpt':'Reporter requests immediate assistance','start':0,'end':len('Reporter requests immediate assistance'),'location_text':'','location_role':'none','review_state':'sender_reviewed'}]
   else:claims=p['claims']
   context=' '.join(c['excerpt'] for c in claims)
   for c in claims:
    if c['end']-c['start']!=len(c['excerpt']) or c['start']<0:raise ValueError('Invalid evidence offsets')
    c['location']=resolve(c.pop('location_text',''),context,c.pop('location_role','event'))
    c['evidence_label']='Sender-supplied excerpt'
   claims=rank_claims(claims)
   priority,reasons,urgent_review=urgency(claims,kind=='urgent_attention')
   main=next((c for c in claims if c['kind'] not in ['reporter_location','event_time','event_location']),claims[0])
   report={'id':id,'message_id':id,'session_id':d['session_id'],'site_id':SITE_ID,'reporter_name':session['display_name'],'received_at':now(),'captured_at':p.get('captured_at'),'issued_at':d['issued'],**observation_time(claims,p.get('captured_at') or d['issued']),'late':d['expires']<stamp,'claims':claims,'summary':main['value'],'event_type':main['kind'],'urgency':priority,'urgency_reasons':reasons,'needs_urgent_review':urgent_review,'urgent_attention':kind=='urgent_attention','triage':assess(claims,kind=='urgent_attention'),'status':'open','owner':None,'incident_id':None,'conflicts':[],'review_state':'unreviewed','source_id':p.get('source_id'),'source_hash':p.get('source_hash'),'origin_label':p.get('origin_label','typed urgent action'),'corrections':[],'reply_to':p.get('reply_to'),'correction_of':p.get('correction_of'),'correction_reason':p.get('correction_reason','')}
   self.store.put('report','operator',report,event='report_received')
   if kind=='correction':
    target.update(superseded_by=id,status='superseded');self.store.put('report','operator',target,event='report_superseded')
    for conflict in self.store.list('conflict','operator'):
     if target['id'] in conflict['report_ids']:
      conflict.update(status='superseded_evidence',resolution_reason='Reporter corrected the underlying report; original sources remain in history.');self.store.put('conflict','operator',conflict,event='conflict_source_corrected')
    self.store.db.execute("DELETE FROM objects WHERE kind='pending_correction' AND id=?",(id,))
   if kind=='correction':self.operations.supersede_report(target['id'])
   intake=next((x for x in self.store.list('intake',OPERATOR) if x.get('message_id')==id and (x.get('confirmed_event_geo') or x.get('location_unconfirmed'))),None)
   if intake and intake.get('location_unconfirmed'):
    for claim in report['claims']:
     loc=claim['location']
     if loc['role']!='reporter':
      loc.update(candidate_places=[loc['geo']] if loc.get('geo') else loc.get('candidate_places',[]),geo=None,status='needs_confirmation',geometry_status='unlocated',reason='Operator held the event location for confirmation.')
    report=self.store.put('report','operator',report,event='live_location_held')
   elif intake:
    target=next((c for c in report['claims'] if c['location']['role']!='reporter'),None)
    if target:
     target['location'].update(geo=intake['confirmed_event_geo'],status='operator_confirmed',geometry_status='mapped',precision='point',reason=intake['location_review_note'],derivation='operator_confirmation');report=self.store.put('report','operator',report,event='live_event_location_confirmed')
     campus_id=intake['confirmed_event_geo'].get('campus_building_id')
     if campus_id:target['location']['feature_id']=campus_id;report=self.store.put('report','operator',report,event='live_campus_building_confirmed')
   if session.get('world'):
    report['world']=session['world'];report=self.store.put('report','operator',report,event='report_workspace_associated')
   self.operations.on_report(report)
   self.detect_conflicts(report)
   for pending in self.store.list('pending_correction','operator'):
    if pending['packet']['payload'].get('correction_of')==id:
     try:self.receive(pending['id'],pending['revision'],pending['packet'],pending['body_hash'],stamp)
     except ValueError as e:
      pending.update(state='rejected',reason=str(e));self.store.put('pending_correction','operator',pending,event='correction_rejected')
   if p.get('reply_to'):self.apply_response(p['reply_to'],d,p.get('response_action','replied'),'',report_id=id)
   self.transport.acknowledge(id,OPERATOR,stamp,d['expires']<stamp)
  elif kind=='instruction':
   session=self.session(d['session_id'])
   if d['origin']!=OPERATOR or d['destination']!=session['endpoint_id']:raise ValueError('Wrong instruction route')
   inbox={'id':id,'session_id':d['session_id'],'endpoint':d['destination'],'text':p['text'],'questions':[{'id':str(uuid5(UUID(id),str(i))),'text':q,'state':'open'} for i,q in enumerate(p.get('questions',[]))],'approval_hash':p['approval_hash'],'issued_at':d['issued'],'expires_at':d['expires'],'body_hash':body_hash,'persisted':False,'replaces_message_id':p.get('replaces_message_id'),'responses':[]}
   replaces=p.get('replaces_message_id')
   if replaces:
    prior=self.store.get(replaces,'inbox')
    if prior and prior['session_id']!=d['session_id']:raise ValueError('Replacement/session mismatch')
    if prior:prior['superseded_by']=id;self.store.put('inbox',d['destination'],prior,event='instruction_superseded')
   later=[x for x in self.store.list('inbox',d['destination']) if x.get('replaces_message_id')==id]
   if later:inbox['superseded_by']=max(later,key=lambda x:x['issued_at'])['id']
   self.store.put('inbox',d['destination'],inbox,event='instruction_available')
  elif kind=='human_response':
   if d['destination']!=OPERATOR:raise ValueError('Wrong human response route')
   self.apply_response(p['message_id'],d,p['action'],p.get('text',''))
   self.transport.acknowledge(id,OPERATOR,stamp,d['expires']<stamp)

 def apply_response(self,target,d,action,text,report_id=None):
  original=self.store.get(target,'message')
  if not original or original['destination']!=d['origin'] or original['session_id']!=d['session_id']:raise ValueError('Response/session mismatch')
  event={'id':uid(),'action':action,'text':text,'report_id':report_id,'received_at':now()}
  original['human_responses'].append(event);self.store.put('message',original['origin'],original,event='human_response_received')
  for r in self.store.list('report','operator'):
   if r['session_id']==d['session_id'] and r['status']!='resolved':
    r['response_needed']=action in ['cannot_follow','needs_clarification','request_current'];self.store.put('report','operator',r,event='response_obligation_changed')
  # A human acknowledgment does not answer any question or assess comprehension.
  if action=='replied' and (text or report_id):
   inbox=self.store.get(target,'inbox')
   if inbox:
    for q in inbox['questions']:q['state']='answer_received'
    self.store.put('inbox',d['origin'],inbox,event='answer_received')

 def detect_conflicts(self,report):
  from .worlds import report_world
  for c in report['claims']:
   if c['kind']!='access' or c['assertion']!='asserted' or not c['location']['feature_id']:continue
   def polarity(claim):
    t=(claim['value']+' '+claim['excerpt']).lower()
    if any(x in t for x in ['not blocked','unblocked','open and clear','is clear','is open']):return 'clear'
    if any(x in t for x in ['blocked','closed','obstructed']):return 'blocked'
    return None
   for other in self.store.list('report','operator'):
    if other['id']==report['id'] or other.get('superseded_by') or report_world(other)!=report_world(report):continue
    a=other.get('observed_at') or epoch(other['received_at']);b=report.get('observed_at') or epoch(report['received_at'])
    if abs(a-b)>120:continue
    for oc in other['claims']:
     if oc['kind']=='access' and oc['assertion']=='asserted' and oc['location']['feature_id']==c['location']['feature_id'] and polarity(c) and polarity(oc) and polarity(c)!=polarity(oc):
      cid=str(uuid5(NAMESPACE_URL,':'.join(sorted([c['id'],oc['id']]))))
      conflict={'id':cid,'feature_id':c['location']['feature_id'],'claim_ids':[oc['id'],c['id']],'report_ids':[other['id'],report['id']],'status':'open','kind':'potential','reason':'Opposite access reports within two minutes of observation or receipt; time may be unknown. Human review required.'}
      self.store.put('conflict','operator',conflict,event='potential_conflict')

 def operator_snapshot(self,world=None):
  reports=self.store.list('report','operator');messages=[self.public_message(m) for m in self.store.list('message',OPERATOR) if m['kind']=='instruction']
  from .worlds import scope_snapshot
  return scope_snapshot(self,{'limits':{'sessions_per_world':MAX_SESSIONS_PER_WORLD,'active_reports':100},'site':sitepack(),'sessions':[self.visible_session(s) for s in self.store.list('session')],'reports':reports,'incidents':self.store.list('incident','operator'),'messages':messages,'conflicts':self.store.list('conflict','operator'),'pending_corrections':self.store.list('pending_correction','operator'),'operations':self.operations.snapshot(),'network':self.transport.config(),'provider':models.provider_status(),'last_event_id':self.store.last_event(),'at':now()},world)

 def public_message(self,m):
  p=decode(un64(m['body']))['payload']
  inbox=self.store.get(m['id'],'inbox') if m['kind']=='instruction' else None
  qs=inbox.get('questions',[]) if inbox else [{'text':q,'state':'open'} for q in p.get('questions',[])]
  return {k:v for k,v in m.items() if k not in ['body','frames']}|{'text':p.get('text',''),'questions':p.get('questions',[]),'question_states':qs,'followup_due':m['issued']+120,'superseded_by':inbox.get('superseded_by') if inbox else None,'comprehension':'not_assessed'}

 def field_snapshot(self,actor):
  return {'session':self.visible_session(self.session(actor['session_id'])),'jobs':self.store.list('job',actor['id']),'drafts':self.store.list('draft',actor['id']),'inbox':[{**m,'speaker_name':'Operator','speaker_voice':OPERATOR_VOICE} for m in self.store.list('inbox',actor['id'])],'messages':[self.public_message(m) for m in self.store.list('message',actor['id']) if m['kind']!='receipt'],'network':self.transport.config(),'provider':models.provider_status(),'at':now()}

 async def worker(self):
  while True:
   ran=await self.process_next()
   if not ran:await asyncio.sleep(.2)

 async def link_worker(self):
  while True:
   try:
    self.transport.tick()
    with self.store.transaction():self.operations.tick()
   except Exception as e:
    with self.store.transaction():self.store.event('system','transport','transport_error',{'error':str(e)[:300]})
   pending=any(m['state'] in ['queued','transmitting','awaiting_receipt'] for m in self.store.list('message'))
   await asyncio.sleep(.06 if pending else .75)

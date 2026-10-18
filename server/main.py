"""Loopback-only API and offline asset server. Run using scripts/start.sh."""
import asyncio
import hashlib
import json
import math
import os
import re
import shutil
import time
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID
from fastapi import FastAPI,Request,UploadFile,File,Form,HTTPException,Depends,WebSocket,WebSocketDisconnect
from fastapi.responses import JSONResponse,FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .store import Conflict,uid,now,dump
from .domain import Domain,OPERATOR
from .site import sitepack,resolve,BY_ID,urgency
from .models import provider_status,instruction_issues,validate_extraction,critical_fields
from .browser_access import BrowserAccess,COOKIE,LINK_SECONDS,SESSION_SECONDS

ROOT=Path(__file__).resolve().parents[1]

def create_app(data_dir=None,workers=True):
 d=Domain(data_dir or os.environ.get('COMM_DATA_DIR',str(ROOT/'.data')))
 access=BrowserAccess(d)
 @asynccontextmanager
 async def lifespan(app):
  tasks=[asyncio.create_task(d.worker()),asyncio.create_task(d.link_worker())] if workers else []
  yield
  for t in tasks:t.cancel()
  await asyncio.gather(*tasks,return_exceptions=True)
 app=FastAPI(title='Comm Control',version='0.1.0',lifespan=lifespan)
 app.state.domain=d
 app.add_middleware(CORSMiddleware,allow_origins=['http://127.0.0.1:8765','http://localhost:8765','http://127.0.0.1:5173','http://localhost:5173','http://127.0.0.1:8766','http://localhost:8766'],allow_methods=['GET','POST','PATCH'],allow_headers=['Authorization','Content-Type','Idempotency-Key'])

 @app.middleware('http')
 async def boundaries(request,call_next):
  host=request.headers.get('host','').split(':')[0]
  if host not in ['127.0.0.1','localhost','testserver']:return JSONResponse({'code':'host_denied','message':'This demo is loopback-only.'},status_code=403)
  origin=request.headers.get('origin')
  if origin and origin not in ['http://127.0.0.1:8765','http://localhost:8765','http://127.0.0.1:5173','http://localhost:5173','http://127.0.0.1:8766','http://localhost:8766']:return JSONResponse({'code':'origin_denied','message':'Untrusted request origin.'},status_code=403)
  try:length=int(request.headers.get('content-length','0'))
  except ValueError:return JSONResponse({'code':'invalid','message':'Invalid content length'},status_code=400)
  if length>11*1024*1024:return JSONResponse({'code':'too_large','message':'Recording limit is 10 MiB.'},status_code=413)
  response=await call_next(request)
  response.headers['X-Content-Type-Options']='nosniff'
  response.headers['X-Frame-Options']='DENY'
  response.headers['Content-Security-Policy']="frame-ancestors 'none'"
  response.headers['Referrer-Policy']='no-referrer' if request.url.path.startswith('/api') else 'strict-origin-when-cross-origin'
  response.headers['Cache-Control']='no-store' if request.url.path.startswith('/api') else 'no-cache'
  return response

 @app.exception_handler(Conflict)
 async def conflict(request,e):return JSONResponse({'code':'conflict','message':str(e),'retryable':False},status_code=409)
 @app.exception_handler(ValueError)
 async def invalid(request,e):return JSONResponse({'code':'invalid','message':str(e),'retryable':False},status_code=422)
 @app.exception_handler(PermissionError)
 async def forbidden(request,e):return JSONResponse({'code':'forbidden','message':str(e),'retryable':False},status_code=403)
 @app.exception_handler(OverflowError)
 async def capacity(request,e):return JSONResponse({'code':'busy','message':str(e),'retryable':True},status_code=429)

 async def json_body(request):
  try:body=await request.json()
  except (ValueError,UnicodeError):raise ValueError('Send a valid JSON object.')
  if not isinstance(body,dict):raise ValueError('Send a JSON object.')
  path=request.url.path;required=[]
  if path in ['/api/utterances/text','/api/drafts/manual']:required=['session_id','text']
  elif re.fullmatch(r'/api/drafts/[^/]+/(?:approve|send)',path) or request.method=='PATCH':required=['version']
  elif re.fullmatch(r'/api/inbox/[^/]+/persisted',path):required=['body_hash']
  elif re.fullmatch(r'/api/messages/[^/]+/responses',path):required=['action']
  elif re.fullmatch(r'/api/announcements/[^/]+/(approve|publish-demo)',path) or '/tasks/' in path:required=['version']
  elif path=='/api/incidents':required=['title','report_ids']
  missing=[key for key in required if key not in body]
  if missing:raise ValueError('Missing required fields: '+', '.join(missing))
  if 'version' in body and (type(body['version']) is not int or body['version']<1):raise ValueError('Version must be a positive integer.')
  if 'text' in body and not isinstance(body['text'],str):raise ValueError('Text must be a string.')
  if 'report_ids' in body and (not isinstance(body['report_ids'],list) or not all(isinstance(x,str) for x in body['report_ids'])):raise ValueError('Report IDs must be a list.')
  return body

 def actor(request:Request):return access.actor(request)
 def operator(a=Depends(actor)):
  if a['role'] not in ['operator','facilitator']:raise PermissionError('Operator access required')
  return a
 def field(a=Depends(actor)):
  if a['role']!='field':raise PermissionError('Open the reporting endpoint to access its source.')
  return a
 def get_draft(id,a):
  draft=d.store.get(id,'draft')
  if not draft:raise HTTPException(404,'Draft not found')
  if draft['origin']!=a['id']:raise PermissionError('This draft belongs to its originating endpoint.')
  return draft
 def idem(request,a,body,fn):
  key=request.headers.get('idempotency-key')
  if not key:raise ValueError('Idempotency-Key is required for this mutation.')
  if len(key)>150:raise ValueError('Invalid idempotency key')
  h=hashlib.sha256((request.url.path+dump(body)).encode()).hexdigest()
  # Mutation methods use coordinated transactions themselves. Server event loop serializes ordinary requests.
  row=d.store.db.execute('SELECT * FROM idempotency WHERE scope=? AND key=?',(a['id'],key)).fetchone()
  if row:
   if row['hash']!=h:raise Conflict('Idempotency key was used for different content.')
   return json.loads(row['result'])
  result=fn()
  d.store.db.execute('INSERT INTO idempotency VALUES(?,?,?,?)',(a['id'],key,h,dump(result)))
  return result

 @app.get('/api/health')
 def health():return {'ok':True,'provider':provider_status(),'transport':'simulation','offline_ai':False,'storage_free_gb':round(shutil.disk_usage(ROOT).free/1024**3,1)}
 @app.post('/api/operator/launch')
 def operator_launch(a=Depends(operator)):
  return {'url':'/control?live=1#launch='+access.issue_link(),'expires_in':LINK_SECONDS}
 @app.post('/api/operator/launch/exchange')
 async def exchange_launch(request:Request):
  access.same_origin(request)
  if request.headers.get('content-type','').split(';')[0].strip()!='application/json':
   raise ValueError('Send a JSON object.')
  body=await json_body(request)
  session=access.exchange(body.get('ticket'))
  response=JSONResponse({'authenticated':True})
  response.set_cookie(COOKIE,session,max_age=SESSION_SECONDS,httponly=True,samesite='strict',path='/')
  return response
 @app.get('/api/operator/session')
 def operator_session(a=Depends(operator)):return {'authenticated':True}
 @app.get('/api/site')
 def site():return sitepack()
 @app.get('/api/control/snapshot')
 def snapshot(world:str|None=None,a=Depends(operator)):return d.operator_snapshot(world)
 @app.get('/api/reports/{id}/context')
 def report_context(id,a=Depends(operator)):
  from .worlds import report_world
  report=d.store.get(id,'report')
  if not report:raise HTTPException(404,'Report not found')
  return {'world':report_world(report)}
 @app.get('/api/field/snapshot')
 def field_state(a=Depends(field)):return d.field_snapshot(a)
 @app.post('/api/sessions')
 async def session(request:Request,a=Depends(operator)):
  body=await json_body(request)
  return idem(request,a,body,lambda:d.create_session(str(body.get('name','Field reporter')),body.get('world')))
 @app.get('/api/sessions/{id}/launch')
 def launch(id,a=Depends(operator)):
  s=d.session(id);return {'url':'/field/'+id+'#token='+s['token']}
 @app.get('/api/jobs/{id}')
 def job(id,a=Depends(actor)):
  j=d.store.get(id,'job')
  if not j:raise HTTPException(404,'Job not found')
  if j['origin']!=a['id']:raise PermissionError('Source job belongs to another endpoint.')
  result=dict(j)
  if j.get('draft_id'):result['draft']=get_draft(j['draft_id'],a)
  result['queue_position']=1+sum(1 for x in d.store.list('job') if x['state']=='queued' and x['created_at']<j['created_at']) if j['state']=='queued' else None
  return result
 @app.post('/api/jobs/{id}/retry')
 async def retry(id,a=Depends(actor)):
  j=d.store.get(id,'job')
  if not j or j['origin']!=a['id']:raise PermissionError('Source job belongs to another endpoint')
  if j['state']!='failed':raise ValueError('Only failed jobs can be retried')
  if j.get('retry_id'):return d.store.get(j['retry_id'],'job')
  source=d.store.get(j['source_id'],'source')
  result={**j,'id':uid(),'state':'queued','error':None,'draft_id':None,'created_at':now(),'retry_of':j['id']}
  from .demo_budget import visitor
  if visitor.get():result['public_visitor']=visitor.get()
  with d.store.transaction():
   result=d.store.put('job',j['origin'],result,event='job_queued');j['retry_id']=result['id'];d.store.put('job',j['origin'],j,event='job_retried')
  return result
 @app.post('/api/utterances/text',status_code=202)
 async def text_input(request:Request,a=Depends(actor)):
  body=await json_body(request);origin=d.source_authority(a,body['session_id'],body.get('direction','inbound'))
  return idem(request,a,body,lambda:d.new_job(origin,body['session_id'],body.get('direction','inbound'),str(body['text']),reply_to=body.get('reply_to'),response_action=body.get('response_action','replied')))
 @app.post('/api/utterances',status_code=202)
 async def audio_input(request:Request,session_id:str=Form(),direction:str=Form('inbound'),reply_to:str=Form(''),response_action:str=Form('replied'),audio:UploadFile=File(),a=Depends(actor)):
  origin=d.source_authority(a,session_id,direction)
  content=await audio.read(10*1024*1024+1)
  if not content or len(content)>10*1024*1024:raise HTTPException(413,'Recordings must be 1 byte to 10 MiB.')
  folder=d.dir/'origins'/origin;folder.mkdir(parents=True,exist_ok=True)
  def create():
   path=folder/(uid()+'.upload');path.write_bytes(content)
   return d.new_job(origin,session_id,direction,audio_path=path,reply_to=reply_to or None,response_action=response_action)
  return idem(request,a,{'audio_hash':hashlib.sha256(content).hexdigest(),'session_id':session_id,'direction':direction,'reply_to':reply_to,'response_action':response_action},create)
 @app.post('/api/drafts/manual')
 async def manual(request:Request,a=Depends(actor)):
  body=await json_body(request);direction=body.get('direction','inbound');origin=d.source_authority(a,body['session_id'],direction)
  if not body.get('text') or len(body['text'])>6000:raise ValueError('Enter a source of 1–6,000 characters.')
  return idem(request,a,body,lambda:d.manual_draft(origin,body['session_id'],body['text'],body.get('claims',[]),direction,body.get('reply_to'),body.get('response_action','replied')))
 @app.get('/api/drafts/{id}')
 def draft(id,a=Depends(actor)):return get_draft(id,a)
 @app.get('/api/drafts/{id}/budget')
 def budget(id,a=Depends(actor)):
  from .transport import encode
  draft=get_draft(id,a)
  if draft['direction']=='outgoing':raise ValueError('Budget preview is for source reports')
  payload={'source_id':draft['source_id'],'source_revision':draft['source_revision'],'source_hash':draft['source_hash'],'origin_label':draft['origin_label']+' reviewed','claims':draft['claims'],'captured_at':draft.get('captured_at'),'correction_of':draft.get('correction_of'),'correction_reason':draft.get('correction_reason',''),'reply_to':draft.get('reply_to'),'response_action':draft.get('response_action','replied')}
  body=encode('correction' if draft.get('correction_of') else 'report',draft['session_id'],draft['origin'],OPERATOR,time.time(),time.time()+900,payload,enforce_limit=False)
  return {'body_bytes':len(body),'limit':1024,'frames':(len(body)+127)//128,'fits':len(body)<=1024}
 @app.patch('/api/drafts/{id}')
 async def edit_draft(id,request:Request,a=Depends(actor)):
  body=await json_body(request);draft=get_draft(id,a)
  if draft.get('sent_ids') or draft.get('sent_message_id'):raise Conflict('Sent content is immutable. Start a new report or instruction.')
  old_version=draft['version']
  if body['version']!=old_version:raise Conflict('Draft changed in another window. Reload and review it.')
  if draft['direction']=='outgoing':
   for name in ['text','recipient_ids','expires_at','replaces_message_id']:
    if name in body:draft[name]=body[name]
   if not isinstance(draft['text'],str) or len(draft['text'])>6000:raise ValueError('Instruction limit is 6,000 characters.')
   draft['issues']=instruction_issues(draft['source_text'],draft['text']);draft['approval']=None
   # Deliberate revised source is an explicit new operator instruction, with reason, not a dismissed error.
   if body.get('new_source'):
    if not body.get('reason'):raise ValueError('A revised source needs a reason.')
    draft['source_text']=body['new_source'];draft['source_revision']+=1;draft['source_hash']=hashlib.sha256(body['new_source'].encode()).hexdigest();draft['issues']=instruction_issues(draft['source_text'],draft['text'])
  else:
   if not body.get('reason'):raise ValueError('Fact corrections need a reason.')
   for c in draft['claims']:
    edit=next((x for x in body.get('claims',[]) if x['id']==c['id']),None)
    if edit:
     for name in ['value','count','assertion']:
      if name in edit:c[name]=edit[name]
     if c['count'] is not None and (not isinstance(c['count'],int) or c['count']<0):raise ValueError('Count must be nonnegative or unknown')
     if c['assertion'] not in ['asserted','negated','uncertain','hearsay','hypothetical']:raise ValueError('Invalid assertion')
     if 'excerpt' in edit and edit['excerpt']!=c['excerpt']:
      excerpt=edit['excerpt']
      if not excerpt or excerpt not in c['excerpt']:raise ValueError('Shortened evidence must be an exact span within the original excerpt.')
      if instruction_issues(c['excerpt'],excerpt):raise ValueError('Shortening would remove protected source details. Keep the original excerpt or correct the transcript.')
      c['excerpt']=excerpt;c['start']=draft['source_text'].index(excerpt);c['end']=c['start']+len(excerpt)
     c['derivation']='human_correction';c['correction_reason']=body['reason']
  with d.store.transaction():
   d.store.event(draft['origin'],id,'draft_before_correction',{'draft':get_draft(id,a),'reason':body.get('reason')});return d.store.put('draft',draft['origin'],draft,expected=old_version,event='draft_changed')
 @app.post('/api/drafts/{id}/send')
 async def send(id,request:Request,a=Depends(actor)):
  body=await json_body(request);draft=get_draft(id,a)
  if draft['version']!=body['version'] and not (draft.get('sent_ids') or draft.get('sent_message_id')):raise Conflict('Draft changed. Review before sending.')
  return idem(request,a,body,lambda:{'messages':[d.public_message(m) for m in (d.send_instruction(draft) if draft['direction']=='outgoing' else [d.send_report(draft,body.get('reviewed',True))])]})
 @app.post('/api/drafts/{id}/approve')
 async def approve(id,request:Request,a=Depends(operator)):
  body=await json_body(request);return d.approve(get_draft(id,a),body['version'])
 @app.post('/api/sources/{id}/text',status_code=202)
 async def correct_transcript(id,request:Request,a=Depends(actor)):
  body=await json_body(request);source=d.store.get(id,'source')
  if not source or source['origin']!=a['id']:raise PermissionError('Only the source endpoint may correct its transcript.')
  if body.get('source_revision')!=source['revision']:raise Conflict('Source revision changed. Reload before correction.')
  text=body.get('text','').strip()
  if not text or len(text)>6000:raise ValueError('Corrected transcript must be 1–6,000 characters.')
  if not body.get('reason'):raise ValueError('Transcript correction needs a reason.')
  def create_correction():
   if any(x.get('supersedes_source_id')==id for x in d.store.list('source',source['origin'])):raise Conflict('This source already has a correction. Resume the latest revision.')
   job=d.new_job(source['origin'],source['session_id'],source['direction'],text,reply_to=source.get('reply_to'),response_action=source.get('response_action','replied'))
   with d.store.transaction():
    newer=d.store.get(job['source_id'],'source');sent=next((x for x in reversed(d.store.list('draft',source['origin'])) if x['source_id']==id and x.get('sent_message_id')),None)
    newer.update(captured_at=source['captured_at'],corrected_at=now(),correction_of=sent['sent_message_id'] if sent else source.get('correction_of'),revision=source['revision']+1,supersedes_source_id=id,origin_label='corrected transcript',correction_reason=body['reason']);d.store.put('source',source['origin'],newer,event='transcript_corrected')
    for old in d.store.list('draft',source['origin']):
     if old['source_id']==id and not old.get('sent_message_id') and not old.get('sent_ids'):
      old['invalidated_by_source']=newer['id'];old['approval']=None;d.store.put('draft',old['origin'],old,event='draft_invalidated')
   return job
  return idem(request,a,body,create_correction)
 @app.post('/api/messages/{id}/questions/review')
 async def review_questions(id,request:Request,a=Depends(operator)):
  body=await json_body(request);inbox=d.store.get(id,'inbox')
  if not inbox:raise ValueError('Instruction has not reached its recipient yet.')
  if not body.get('reason'):raise ValueError('Question disposition needs a reason.')
  if body.get('state') not in ['operator_reviewed','closed_unanswered']:raise ValueError('Unknown question disposition')
  with d.store.transaction():
   for q in inbox['questions']:
    if body['state']=='operator_reviewed' and q['state']!='answer_received':raise ValueError('No answer has been received for this question.')
    q.update(state=body['state'],operator_reason=body['reason'])
   d.store.put('inbox',inbox['endpoint'],inbox,event='question_reviewed');d.store.event('operator',id,'question_disposition',{'state':body['state'],'reason':body['reason']})
  return {'reviewed':True}
 @app.post('/api/urgent')
 async def urgent(request:Request,a=Depends(field)):
  body=await json_body(request)
  def send_urgent():
   with d.store.transaction():return d.public_message(d.transport.enqueue('urgent_attention',a['session_id'],a['id'],OPERATOR,{'text':'Reporter requests immediate assistance'},ttl=300))
  return idem(request,a,body,send_urgent)
 @app.post('/api/inbox/{id}/persisted')
 async def persisted(id,request:Request,a=Depends(field)):
  body=await json_body(request);inbox=d.store.get(id,'inbox')
  if not inbox or inbox['endpoint']!=a['id']:raise PermissionError('Wrong recipient')
  if body['body_hash']!=inbox['body_hash']:raise Conflict('Persisted content hash mismatch')
  with d.store.transaction():
   inbox['persisted']=True;d.store.put('inbox',a['id'],inbox,event='endpoint_persisted');d.transport.acknowledge(id,a['id'],time.time(),inbox['expires_at']<=time.time())
  return {'persisted':True}
 @app.post('/api/inbox/{id}/listen')
 async def local_listen(id,mode:str='natural',a=Depends(field)):
  inbox=d.store.get(id,'inbox')
  if not inbox or inbox['endpoint']!=a['id']:raise PermissionError('Wrong recipient')
  if inbox.get('superseded_by') or inbox['expires_at']<=time.time():raise ValueError('This instruction is no longer current. Request current instructions.')
  if mode=='natural':
   from .speech import render_speech
   from .speakers import OPERATOR_VOICE
   wav=await render_speech(inbox['text'],d.dir/'origins'/a['id']/'speech',OPERATOR_VOICE)
   return FileResponse(wav,media_type='audio/wav')
  if mode!='local':raise ValueError('Choose natural or local playback.')
  if not shutil.which('say') or not shutil.which('ffmpeg'):raise ValueError('No installed local speech helper. Read the instruction or enable a device voice.')
  folder=d.dir/'origins'/a['id']/'speech';folder.mkdir(parents=True,exist_ok=True)
  stem=folder/(id+'-'+inbox['body_hash'][:12]);wav=stem.with_suffix('.wav')
  if not wav.exists():
   textfile=stem.with_suffix('.txt');textfile.write_text(inbox['text']);aiff=stem.with_suffix('.aiff')
   process=await asyncio.create_subprocess_exec('say','-o',str(aiff),'-f',str(textfile),stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
   try:await asyncio.wait_for(process.communicate(),30)
   except asyncio.TimeoutError:
    process.kill();await process.communicate();raise ValueError('Local speech took too long. Read the instruction or retry.')
   if process.returncode:raise ValueError('Local speech failed. The exact instruction text remains available.')
   process=await asyncio.create_subprocess_exec('ffmpeg','-v','error','-y','-i',str(aiff),'-ar','22050','-ac','1',str(wav),stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
   await process.communicate()
   if process.returncode:raise ValueError('Local audio conversion failed.')
   aiff.unlink(missing_ok=True)
  return FileResponse(wav,media_type='audio/wav')
 @app.post('/api/messages/{id}/responses',status_code=202)
 async def respond(id,request:Request,a=Depends(field)):
  body=await json_body(request);m=d.store.get(id,'message')
  if not m or m['kind']!='instruction' or m['destination']!=a['id']:raise PermissionError('Wrong recipient')
  action=body['action']
  if action not in ['acknowledged','cannot_follow','needs_clarification','replied','request_current']:raise ValueError('Unknown response action')
  if ((d.store.get(id,'inbox') or {}).get('superseded_by') or m['expires']<=time.time()) and action=='acknowledged':raise ValueError('This instruction is expired or replaced. Request current instructions.')
  if len(body.get('text',''))>1000:raise ValueError('Reply is too long for one packet. Shorten it or record a source-linked report.')
  def enqueue():
   with d.store.transaction():return d.public_message(d.transport.enqueue('human_response',a['session_id'],a['id'],OPERATOR,{'message_id':id,'action':action,'text':body.get('text','')},ttl=900))
  return idem(request,a,body,enqueue)
 from .cases import register_cases
 register_cases(app,d,operator,json_body,idem)
 @app.patch('/api/reports/{id}')
 async def correction(id,request:Request,a=Depends(operator)):
  body=await json_body(request);r=d.store.get(id,'report')
  if not r:raise HTTPException(404,'Report not found')
  if not body.get('reason'):raise ValueError('A correction or status change needs a reason.')
  if 'status' in body and (body['status']=='resolved' or r['status']=='resolved' and body['status']!='resolved'):
   raise ValueError('Use Case history to close or reopen an incident with a recorded outcome.')
  before=json.loads(dump(r))
  for key in ['urgency','status','owner','incident_id']:
   if key in body:r[key]=body[key]
  if 'urgency' in body:r['priority_override']={'urgency':body['urgency'],'reason':str(body['reason'])[:2000],'at':now()}
  if r['urgency'] not in ['critical','elevated','routine','unknown']:raise ValueError('Invalid urgency')
  if r['status'] not in ['open','monitoring','awaiting_response','resolved','superseded']:raise ValueError('Invalid status')
  if body.get('claim_id'):
   c=next((c for c in r['claims'] if c['id']==body['claim_id']),None)
   if not c:raise ValueError('Claim not found')
   if 'feature_id' in body:
    f=body['feature_id']
    if f and f not in BY_ID:raise ValueError('Unknown site feature')
    if f and f.startswith('usc-'):c['location'].update(geo=None,named_subarea=BY_ID[f]['name'])
    c['location'].pop('plan_point',None);c['location'].pop('geometry',None)
    c['location'].update(geometry_status='mapped' if f else 'unmapped',feature_id=f,status='operator_confirmed' if f else 'unlocated',candidate_ids=[],precision='building' if f else 'unknown',resolved_by=OPERATOR,reason=body['reason'])
   if 'estimated_point' in body:
    point=body['estimated_point'];x=float(point['x']);y=float(point['y'])
    if not 70<=x<=925 or not 50<=y<=680:raise ValueError('Choose an estimate within the fictional site plan')
    c['location'].update(feature_id=None,status='operator_estimated',candidate_ids=[],precision='point',geometry_status='mapped',plan_point={'x':x,'y':y},geometry={'type':'Point','coordinates':[-118.27+x/100000,33.74-y/100000]},resolved_by=OPERATOR,reason=body['reason'])
   if 'value' in body:c['value']=body['value'];c['derivation']='human_correction'
   if 'assertion' in body:
    if body['assertion'] not in ['asserted','negated','uncertain','hearsay','hypothetical']:raise ValueError('Invalid assertion')
    c['assertion']=body['assertion']
   if 'count' in body:
    if body['count'] is not None and (not isinstance(body['count'],int) or body['count']<0):raise ValueError('Count must be nonnegative or unknown')
    c['count']=body['count']
  if body.get('claim_id'):
   priority,reasons,review=urgency(r['claims']);r.update(urgency=priority,urgency_reasons=reasons,needs_urgent_review=review)
   r['summary']=next((c['value'] for c in r['claims'] if c['kind'] not in ['reporter_location','event_time','event_location']),r['summary'])
  with d.store.transaction():
   r['corrections'].append({'at':now(),'actor':OPERATOR,'reason':body['reason'],'previous_version':before['version']});d.store.event('operator',id,'report_before_correction',{'report':before,'reason':body['reason']});saved=d.store.put('report','operator',r,expected=body['version'],event='report_corrected');d.operations.on_report(saved);return d.store.get(id,'report')
 @app.post('/api/incidents')
 async def incident(request:Request,a=Depends(operator)):
  body=await json_body(request)
  def create():
   with d.store.transaction():
    for id in body['report_ids']:
     if not d.store.get(id,'report'):raise ValueError('Only received reports may be linked')
    from .worlds import report_world
    if len({report_world(d.store.get(rid,'report')) for rid in body['report_ids']})>1:raise ValueError('Reports from different workspaces cannot be linked.')
    obj={'id':uid(),'title':body['title'][:120],'report_ids':body['report_ids'],'status':'open','owner':None,'created_at':now()};obj=d.store.put('incident','operator',obj,event='incident_created')
    for id in body['report_ids']:
     r=d.store.get(id,'report');r['incident_id']=obj['id'];d.store.put('report','operator',r,event='report_linked')
    return obj
  return idem(request,a,body,create)
 @app.patch('/api/incidents/{id}')
 async def edit_incident(id,request:Request,a=Depends(operator)):
  body=await json_body(request);obj=d.store.get(id,'incident')
  if not obj:raise HTTPException(404,'Incident not found')
  if not body.get('reason'):raise ValueError('Changes need a reason')
  with d.store.transaction():
   old_ids=set(obj['report_ids'])
   if 'report_ids' in body and any(not d.store.get(rid,'report') for rid in body['report_ids']):raise ValueError('Only received reports may be linked')
   from .worlds import report_world
   if len({report_world(d.store.get(rid,'report')) for rid in body.get('report_ids',obj['report_ids'])})>1:raise ValueError('Reports from different workspaces cannot be linked.')
   for key in ['title','status','owner','report_ids']:
    if key in body:obj[key]=body[key]
   if obj['status']=='resolved' and any((r:=d.store.get(rid,'report')) and r['urgency']=='critical' and r['status']!='resolved' for rid in obj['report_ids']):raise ValueError('Review unresolved critical reports before resolving this incident')
   saved=d.store.put('incident','operator',obj,expected=body['version'],event='incident_changed')
   for rid in old_ids|set(obj['report_ids']):
    r=d.store.get(rid,'report')
    if r and (r.get('incident_id')==id or rid in obj['report_ids']):
     r['incident_id']=id if rid in obj['report_ids'] else None;d.store.put('report','operator',r,event='report_link_changed')
   return saved
 @app.patch('/api/conflicts/{id}')
 async def resolve_conflict(id,request:Request,a=Depends(operator)):
  body=await json_body(request);c=d.store.get(id,'conflict')
  if not c:raise HTTPException(404,'Conflict not found')
  if body.get('status') not in ['reviewed','resolved_as_change','resolved_as_interpretation_error','unresolved']:raise ValueError('Choose a valid disposition')
  if not body.get('reason'):raise ValueError('Explain the disposition')
  with d.store.transaction():c.update(status=body['status'],resolution_reason=body['reason']);return d.store.put('conflict','operator',c,expected=body['version'],event='conflict_reviewed')
 @app.post('/api/demo/network')
 async def network(request:Request,a=Depends(operator)):
  body=await json_body(request);cfg=d.transport.config()
  for key in ['enabled','mode','bits_per_second','latency_ms','jitter_ms','loss','seed','paused_endpoints']:
   if key in body:cfg[key]=body[key]
  if cfg['mode'] not in ['direct','simulated'] or not 100<=cfg['bits_per_second']<=100000 or not 0<=cfg['latency_ms']<=10000 or not 0<=cfg['jitter_ms']<=10000 or not 0<=cfg['loss']<=1:raise ValueError('Network profile outside demo limits')
  with d.store.transaction():return d.store.put('config','system',cfg,event='network_changed')
 @app.post('/api/demo/messages/{id}/retry')
 def retry_message(id,a=Depends(actor)):
  m=d.store.get(id,'message')
  if not m or m['origin']!=a['id']:raise PermissionError('Wrong source')
  if m['expires']<=time.time():raise ValueError('Expired content requires a new reviewed message.')
  with d.store.transaction():m.update(state='queued',part=0,attempts=0,next_at=time.time());return d.store.put('message',m['origin'],m,event='manual_retry')
 @app.post('/api/demo/messages/{id}/replay')
 def replay(id,a=Depends(operator)):
  m=d.store.get(id,'message')
  if not m:raise ValueError('Message not found')
  with d.store.transaction():
   for f in m['frames']:d.transport.receive_frame(un64(f),m['origin'],m['destination'],time.time())
  return {'replayed':True,'message_id':id}
 @app.get('/api/events')
 def events(after:int=0,a=Depends(actor)):
  scope='operator' if a['role']!='field' else a['id'];rows=d.store.events(after,scope)
  return {'events':rows,'next_after':rows[-1]['event_id'] if rows else after}
 @app.websocket('/api/live')
 async def live(ws:WebSocket):
  # No credentials in URLs/logs; first frame authenticates this socket.
  if ws.headers.get('origin') not in [None,'http://127.0.0.1:8765','http://localhost:8765','http://127.0.0.1:8766','http://localhost:8766','http://127.0.0.1:5173','http://localhost:5173']:
   await ws.close(code=1008);return
  await ws.accept()
  try:
   auth=await asyncio.wait_for(ws.receive_json(),5)
   if auth.get('token'):a=d.actor(auth['token'])
   else:
    access.same_origin(ws)
    a=access.cookie_actor(ws)
   cursor=auth.get('after',0)
   scope='operator' if a['role']!='field' else a['id']
   while True:
    events=d.store.events(cursor,scope)
    if events:cursor=events[-1]['event_id'];await ws.send_json({'events':events,'last_event_id':cursor})
    else:await ws.send_json({'heartbeat':True,'last_event_id':cursor})
    await asyncio.sleep(.7)
  except (WebSocketDisconnect,asyncio.TimeoutError,PermissionError):
   try:await ws.close()
   except (RuntimeError,WebSocketDisconnect):pass
 from .intake import register_intake
 register_intake(app,d,operator,json_body,idem)
 from .resources import register_resources
 register_resources(app,d,operator,json_body,idem)
 @app.get('/api/geo')
 def geographic_metadata(a=Depends(actor)):return d.operations.map.public()|{'tile_url':d.operations.config()['tile_url']}
 @app.get('/api/geo/search')
 def place_search(q:str='',a=Depends(actor)):
  if len(q)>180:raise ValueError('Place query is too long')
  return {'places':d.operations.map.search(q),'scope':'Local OpenStreetMap catalog for Downtown Los Angeles; no public geocoder request.'}
 @app.post('/api/geo/route')
 async def route_preview(request:Request,a=Depends(operator)):
  body=await json_body(request)
  if not all(isinstance(body.get(k),dict) and all(type(body[k].get(c)) in [int,float] and math.isfinite(body[k][c]) for c in ['lon','lat']) and -180<=body[k]['lon']<=180 and -90<=body[k]['lat']<=90 for k in ['origin','destination']):raise ValueError('Origin and destination need valid longitude and latitude')
  return d.operations.map.route(body['origin'],body['destination'],d.operations.excluded())|{'closure_revision':d.operations.config()['closure_revision']}
 @app.patch('/api/reports/{id}/geo')
 async def confirm_geo(id,request:Request,a=Depends(operator)):
  body=await json_body(request);r=d.store.get(id,'report')
  if not r:raise ValueError('Received report not found')
  if not body.get('reason'):raise ValueError('Explain the location confirmation')
  geo=body.get('geo',{})
  if not all(type(geo.get(k)) in [int,float] for k in ['lat','lon']) or not -90<=geo['lat']<=90 or not -180<=geo['lon']<=180:raise ValueError('Choose valid map coordinates')
  claim=next((c for c in r['claims'] if c['id']==body.get('claim_id')),None)
  if not claim:raise ValueError('Choose a received fact to locate')
  if claim['location']['role']=='reporter':raise ValueError('Reporter position is separate. Choose an event or access fact.')
  with d.store.transaction():
   d.store.event('operator',id,'report_before_location_confirmation',{'report':r,'reason':body['reason']})
   accuracy='operator_estimated' if geo.get('accuracy')=='operator_estimated' else 'operator_confirmed'
   claim['location'].update(geo={'id':geo.get('id','operator:'+id),'label':str(geo.get('label','Operator map selection'))[:180],'lon':geo['lon'],'lat':geo['lat'],'accuracy':accuracy,'source':geo.get('source','operator')},candidate_places=[],status=accuracy,precision='point',geometry_status='mapped',reason=body['reason'])
   r=d.store.put('report','operator',r,expected=body['version'],event='geographic_location_confirmed');d.operations.on_report(r);d.operations.recompute_routes();return d.store.get(id,'report')
 @app.post('/api/operations/replan/{id}')
 async def replan(id,request:Request,a=Depends(operator)):
  body=await json_body(request);r=d.store.get(id,'report')
  if not r:raise ValueError('Received report not found')
  def apply():
   with d.store.transaction():d.operations.on_report(r);d.operations.recompute_routes();return d.store.get(id,'plan')
  return idem(request,a,body,apply)
 @app.patch('/api/operations/config')
 async def automation_config(request:Request,a=Depends(operator)):
  body=await json_body(request);cfg=d.operations.config()
  if not all(type(body[k]) is bool for k in ['enabled','auto_assign','auto_escalate'] if k in body):raise ValueError('Automation settings must be true or false')
  with d.store.transaction():
   for key in ['enabled','auto_assign','auto_escalate']:
    if key in body:cfg[key]=body[key]
   return d.store.put('config','operator',cfg,expected=body['version'],event='automation_settings_changed')
 @app.patch('/api/units/{id}')
 async def unit_status(id,request:Request,a=Depends(operator)):
  body=await json_body(request)
  with d.store.transaction():return d.operations.set_unit(id,body)
 @app.patch('/api/assignments/{id}/route')
 async def select_route(id,request:Request,a=Depends(operator)):
  body=await json_body(request);obj=d.store.get(id,'assignment')
  if not obj or obj['state']=='released':raise ValueError('Active demo assignment not found')
  if body.get('closure_revision')!=obj['route']['closure_revision'] or body.get('closure_revision')!=d.operations.config()['closure_revision']:raise Conflict('Road reports changed. Review the updated routes.')
  if body.get('route_id') not in [r['id'] for r in obj['route']['routes']]:raise ValueError('Choose a currently supported route')
  with d.store.transaction():obj['selected_route']=body['route_id'];return d.store.put('assignment','operator',obj,expected=body['version'],event='operator_route_selected')
 @app.post('/api/closures')
 async def road_closure(request:Request,a=Depends(operator)):
  body=await json_body(request);keys=body.get('edge_ids',[])
  if not keys or len(keys)>30 or any(k not in d.operations.map.edges for k in keys):raise ValueError('Choose up to 30 supported road segments')
  if not body.get('reason'):raise ValueError('Road closure needs a source or reason')
  def create():
   with d.store.transaction():
    obj={'id':uid(),'report_id':body.get('report_id'),'label':str(body.get('label') or d.operations.map.edges[keys[0]]['name'])[:120],'edge_ids':keys,'coordinates':[d.operations.map.edges[k]['coordinates'] for k in keys],'state':'active','reported':True,'verification':'operator reported, unverified','reason':body['reason'],'created_at':now(),'expires_at':time.time()+min(86400,max(60,int(body.get('duration_seconds',1800))))}
    result=d.store.put('closure','operator',obj,event='operator_road_closed');d.operations.bump_closures();d.operations.recompute_routes();return result
  return idem(request,a,body,create)
 @app.patch('/api/closures/{id}')
 async def change_closure(id,request:Request,a=Depends(operator)):
  body=await json_body(request);obj=d.store.get(id,'closure')
  if not obj:raise ValueError('Road report not found')
  if body.get('state') not in ['active','reopened'] or not body.get('reason'):raise ValueError('Choose road state and explain the change')
  with d.store.transaction():
   obj.update(state=body['state'],operator_reason=body['reason'])
   if obj['state']=='active':obj['expires_at']=time.time()+1800
   result=d.store.put('closure','operator',obj,expected=body['version'],event='road_report_changed');d.operations.bump_closures();d.operations.recompute_routes();return result
 @app.post('/api/plans/{id}/tasks/{task_id}')
 async def task_review(id,task_id,request:Request,a=Depends(operator)):
  body=await json_body(request);plan=d.store.get(id,'plan')
  if not plan:raise ValueError('Response plan not found')
  if body.get('state') not in ['reviewed','open'] or not body.get('reason'):raise ValueError('Choose task state and a review note')
  task=next((t for t in plan['tasks'] if t['id']==task_id),None)
  if not task:raise ValueError('Task not found')
  with d.store.transaction():task.update(state=body['state'],operator_reason=body['reason'],reviewed_at=now());return d.store.put('plan','operator',plan,expected=body['version'],event='plan_task_reviewed')
 @app.post('/api/announcements')
 async def prepare_advisory(request:Request,a=Depends(operator)):
  body=await json_body(request)
  def create():
   with d.store.transaction():return d.operations.advisory(body.get('report_id'),str(body.get('audience','Public demo board')))
  return idem(request,a,body,create)
 @app.post('/api/announcements/{id}/approve')
 async def approve_advisory(id,request:Request,a=Depends(operator)):
  body=await json_body(request)
  with d.store.transaction():return d.operations.approve_advisory(id,body)
 @app.post('/api/announcements/{id}/publish-demo')
 async def publish_advisory(id,request:Request,a=Depends(operator)):
  body=await json_body(request)
  def publish():
   with d.store.transaction():return d.operations.publish_advisory(id,body.get('version'))
  return idem(request,a,body,publish)
 @app.post('/api/demo/city')
 async def city_scenario(request:Request,a=Depends(operator)):
  body=await json_body(request)
  from .city_scenarios import seed_city
  return idem(request,a,body,lambda:seed_city(d))
 @app.get('/api/trace')
 def trace(a=Depends(operator)):return {'events':d.store.events(0,'transport',1000)}
 @app.get('/api/export')
 def export(world:str|None=None,a=Depends(operator)):
  snapshot=d.operator_snapshot(world);events=d.store.events(0,'operator',10000);transport=d.store.events(0,'transport',10000)
  if world:
   ids={v['id'] for key in ['reports','sessions','messages','incidents','conflicts'] for v in snapshot[key]}
   ids.update(v['id'] for key in ['plans','assignments','actions','announcements'] for v in snapshot['operations'][key])
   events=[e for e in events if e['aggregate_id'] in ids];transport=[e for e in transport if e['aggregate_id'] in ids]
  return {'format':'comm-control-evidence-v1','world':world,'exported_at':now(),'mode':'demo operations; cached OSM geometry; simulated transport; connected AI','snapshot':snapshot,'events':events,'transport':transport,'limitations':['Demo resources and communications; no external dispatch or public alert integration','Route preview only; no live traffic','No RF validation','Source audio and unsent drafts excluded','No inferred comprehension']}
 @app.get('/api/source/{id}/audio')
 def source_audio(id,a=Depends(actor)):
  source=d.store.get(id,'source')
  if not source or source['origin']!=a['id']:raise PermissionError('Audio remains at its originating endpoint')
  if not source.get('audio_path'):raise HTTPException(404,'This source is typed')
  return FileResponse(source['audio_path'],media_type='application/octet-stream',filename=id+'.audio')
 @app.post('/api/demo/seed')
 async def seed(request:Request,a=Depends(operator)):
  body=await json_body(request)
  from .scenarios import seed_scenario
  return idem(request,a,body,lambda:seed_scenario(d))
 @app.post('/api/demo/reset')
 async def reset(request:Request,a=Depends(operator)):
  body=await json_body(request)
  if body.get('confirmation')!='RESET SYNTHETIC RUN':raise ValueError('Type RESET SYNTHETIC RUN to clear this demo only.')
  with d.store.transaction():
   d.store.db.execute("DELETE FROM objects WHERE kind NOT IN ('config')");d.store.db.execute('DELETE FROM idempotency');d.store.event('operator','run','synthetic_run_reset',{'at':now()})
   d.operations.last_tick=0;d.operations.bootstrap();d.transport.busy_until=0;d.outgoing_streak=0
  await asyncio.to_thread(shutil.rmtree,d.dir/'origins',ignore_errors=True)
  return {'reset':True}
 from .usc_ops import register_usc
 register_usc(app,d,operator,json_body,idem)
 from .dispatch_queue import register as register_dispatch_queues
 register_dispatch_queues(app,d,operator,json_body,idem)
 from .campus import register_campus
 register_campus(app,d,operator,json_body)
 from .aggregation import register_aggregation
 register_aggregation(app,d,operator,json_body,idem)
 from .runs import register_runs
 register_runs(app,d,operator,json_body,idem)
 dist=Path(os.environ.get('COMM_WEB_DIST',str(ROOT/'web/dist')))
 if (dist/'assets').is_dir():app.mount('/assets',StaticFiles(directory=dist/'assets'),name='assets')
 @app.get('/{path:path}')
 def frontend(path):
  if path.startswith('api/'):raise HTTPException(404,'API route not found')
  if not (dist/'index.html').is_file():return JSONResponse({'message':'Build the frontend with npm run build in web/.'},status_code=503)
  if path in ['sw.js','manifest.webmanifest'] and (dist/path).is_file():return FileResponse(dist/path)
  return FileResponse(dist/'index.html')
 return app


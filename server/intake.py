"""Explicit desk-captured demo calls. Normal unsent field sources stay private.

Cumulative audio snapshots yield provisional transcript/place candidates. Only a
finished, extracted and reviewed call enters the normal constrained report link.
"""
import asyncio,hashlib,re,time,math
from pathlib import Path
from fastapi import Depends,Request,UploadFile,File,Form
from . import models
from .domain import OPERATOR
from .store import uid,now,Conflict
from .geography import atlas,point,distance,norm


def preview_places(text):
 """Literal place mentions only; these are candidates, never event assertions."""
 a=atlas();hits=[]
 for place in a.places:
  for alias in place.get('aliases',[place['label']]):
   if len(alias)<7:continue
   match=re.search(r'\b'+re.escape(alias)+r'\b',text,re.I)
   if match:hits.append((match.start(),place));break
 result=[]
 for _,p in sorted(hits,key=lambda h:h[0]):
  if any(distance(point(p),point(q))<220 for q in result):continue
  result.append({k:v for k,v in p.items() if k not in ['score','aliases']})
 from .usc_atlas import resolve as usc_resolve
 for b in usc_resolve(text):
  result.append({'id':b['id'],'label':b['name'],'lon':b['center'][0],'lat':b['center'][1],'accuracy':'building','source':'USC campus / OpenStreetMap'})
 streets=[]
 for name in a.streets:
  short=re.sub(r'^(north|south|east|west) ','',name)
  match=re.search(r'\b'+re.escape(short)+r'\b',text,re.I)
  if match and not any(x[2]==short for x in streets):streets.append((match.start(),match.end(),short))
 streets.sort()
 for first,second in zip(streets,streets[1:]):
  between=text[first[1]:second[0]]
  if second[0]-first[1]>80 or not re.search(r'\b(at|and)\b|[&@]',between,re.I):continue
  candidates=a.search(first[2]+' and '+second[2])
  if len(candidates)==1 and candidates[0]['accuracy']=='intersection':result.append(candidates[0])
 return result[:5]


def register_intake(app,d,operator,json_body,idem):
 locks={}
 def get(id):
  obj=d.store.get(id,'intake')
  if not obj:raise ValueError('Live call not found.')
  return obj
 def public(obj):
  value={k:v for k,v in obj.items() if k not in ['last_hash','audio_path','last_request_at']}
  if obj.get('world'):value['places']=[p for p in value['places'] if str(p['id']).startswith('usc-')==(obj['world']=='usc')]
  if obj.get('job_id'):
   job=d.store.get(obj['job_id'],'job');value['job']=job
   if job and job.get('draft_id'):
    draft=d.store.get(job['draft_id'],'draft')
    if draft and draft['session_id']==obj['session_id'] and draft['source_id'] in obj.get('source_ids',[]):value['draft']=draft
  return value
 def check_open(obj):
  if obj['state'] in ['cancelled','queued']:raise Conflict('This call is closed. Start a new live call.')

 @app.get('/api/demo/intake/current')
 def current(world:str|None=None,a=Depends(operator)):
  from .worlds import validate
  validate(world)
  calls=[x for x in d.store.list('intake',OPERATOR) if x['state'] not in ['cancelled','queued'] and (world is None or x.get('world','city')==world)]
  return {'intake':public(calls[-1]) if calls else None}

 @app.post('/api/demo/intake/new')
 async def fresh(request:Request,a=Depends(operator)):
  body=await json_body(request)
  from .worlds import validate
  world=validate(body.get('world')) or 'city'
  def reset():
   with d.store.transaction():
    for old in d.store.list('intake',OPERATOR):
     if old.get('world','city')==world and old['state'] not in ['cancelled','queued']:
      old.update(state='cancelled',places=[],ended_for_new_call_at=now());d.store.put('intake',OPERATOR,old,event='live_call_replaced_by_new_intake')
    return {'ready':True,'world':world}
  return idem(request,a,body,reset)

 @app.post('/api/demo/intake')
 async def create(request:Request,a=Depends(operator)):
  body=await json_body(request)
  from .worlds import validate
  world=validate(body.get('world'))
  def start():
   previous=[x for x in d.store.list('intake',OPERATOR) if x['state']=='listening' and x.get('world','city')==(world or 'city')]
   if previous:raise Conflict('A live call is already open. Finish or discard it first.')
   config_id='live-demo-session'+(':'+world if world else '')
   cfg=d.store.get(config_id,'config');session=d.store.get(cfg['session_id'],'session') if cfg else None
   if not session:
    session=d.create_session('Live demo caller',world);d.store.put('config',OPERATOR,{'id':config_id,'session_id':session['id']})
   with d.store.transaction():
    obj={'id':uid(),'session_id':session['id'],'state':'listening','created_at':now(),'sequence':0,'transcript':'','places':[],'error':None,'source_ids':[],'mode':'operator-captured live demo','shared_with_operator':True,'captured_at':now()}
    if world:obj['world']=world
    return public(d.store.put('intake',OPERATOR,obj,event='live_call_started'))
  return idem(request,a,body,start)

 @app.get('/api/demo/intake/{id}')
 def snapshot(id,a=Depends(operator)):return public(get(id))

 @app.post('/api/demo/intake/{id}/audio')
 async def audio(id,sequence:int=Form(),final:bool=Form(False),audio:UploadFile=File(),a=Depends(operator)):
  if not 1<=sequence<=8:raise ValueError('A live call supports up to eight audio updates.')
  content=await audio.read(10*1024*1024+1)
  if not content or len(content)>10*1024*1024:raise ValueError('Choose a recording under 10 MB.')
  lock=locks.setdefault(id,asyncio.Lock())
  if lock.locked():raise Conflict('The last audio update is still processing.')
  async with lock:
   obj=get(id);check_open(obj);fingerprint=hashlib.sha256(content+str(final).encode()).hexdigest()
   if sequence==obj['sequence']:
    if obj.get('last_hash')!=fingerprint:raise Conflict('This audio update changed. Use the next sequence.')
    return public(obj)
   if sequence!=obj['sequence']+1:raise Conflict('Audio arrived out of order. Resume with the next update.')
   if obj.get('job_id'):raise Conflict('This recording is finished. Review the facts or start a new call.')
   if not final and time.time()-obj.get('last_request_at',0)<3:raise Conflict('Audio updates are limited to one every few seconds.')
   folder=d.dir/'live-intakes'/id;folder.mkdir(parents=True,exist_ok=True);path=folder/(str(sequence)+'.upload');path.write_bytes(content)
   with d.store.transaction():
    obj.update(sequence=sequence,last_hash=fingerprint,last_request_at=time.time(),error=None,audio_path=str(path));obj=d.store.put('intake',OPERATOR,obj,event='live_audio_received')
   try:
    result=await models.transcribe(path)
    current=get(id)
    if current['state']=='cancelled':return public(current)
    job=d.new_job(d.session(current['session_id'])['endpoint_id'],current['session_id'],'inbound',audio_path=path) if final else None
    with d.store.transaction():
     current.update(transcript=result['text'],places=preview_places(result['text']),updated_at=now(),error=None)
     if final:
      source=d.store.get(job['source_id'],'source');source.update(text=result['text'],segments=result['segments'],stt_model=result['model'],stt_ms=result['processing_ms'],captured_at=current['captured_at'],origin_label='live demo voice')
      d.store.put('source',source['origin'],source,event='live_transcript_finished');current.update(state='review',job_id=job['id'],source_ids=current['source_ids']+[source['id']])
     current=d.store.put('intake',OPERATOR,current,event='live_preview_updated')
    if not final:
     path.unlink(missing_ok=True);Path(result['normalized_path']).unlink(missing_ok=True)
    return public(current)
   except Exception as error:
    current=get(id)
    if current['state']=='cancelled':return public(current)
    with d.store.transaction():
     current.update(state='failed',error=str(error)[:350]);current=d.store.put('intake',OPERATOR,current,event='live_transcription_failed')
    return public(current)

 @app.post('/api/demo/intake/{id}/revise')
 async def revise(id,request:Request,a=Depends(operator)):
  body=await json_body(request);text=body.get('text','');obj=get(id);check_open(obj)
  if not isinstance(text,str) or not 1<=len(text.strip())<=6000 or not body.get('reason'):raise ValueError('Enter the transcript and a reason for the correction.')
  if body.get('version')!=obj['version']:raise Conflict('This call changed. Review the current transcript.')
  if locks.setdefault(id,asyncio.Lock()).locked():raise Conflict('Wait for the audio update to finish before editing the transcript.')
  def update():
   old=d.store.get(obj.get('job_id',''),'job')
   if old and old['state'] in ['queued','transcribing','extracting']:raise Conflict('Wait for the facts to finish processing.')
   job=d.new_job(d.session(obj['session_id'])['endpoint_id'],obj['session_id'],'inbound',text=text.strip())
   with d.store.transaction():
    for source_id in obj['source_ids']:
     for draft in d.store.list('draft'):
      if draft['source_id']==source_id and not draft.get('sent_message_id'):draft['invalidated_by_source']='live transcript revision';d.store.put('draft',draft['origin'],draft,event='live_draft_replaced')
    source=d.store.get(job['source_id'],'source');source.update(origin_label='corrected live demo transcript' if obj['source_ids'] else 'typed live demo',captured_at=obj['captured_at']);d.store.put('source',source['origin'],source,event='live_transcript_corrected')
    obj.update(transcript=text.strip(),places=preview_places(text),state='review',job_id=job['id'],source_ids=obj['source_ids']+[source['id']],correction_reason=body['reason'],error=None)
    return public(d.store.put('intake',OPERATOR,obj,expected=body['version'],event='live_revision_requested'))
  return idem(request,a,body,update)

 @app.post('/api/demo/intake/{id}/send')
 async def send(id,request:Request,a=Depends(operator)):
  body=await json_body(request);obj=get(id)
  if obj.get('message_id'):
   supplied=body.get('event_location');saved=obj.get('confirmed_event_geo')
   if supplied is not None and not isinstance(supplied,dict):raise ValueError('Choose a valid event location.')
   if bool(supplied)!=bool(saved) or supplied and any(supplied.get(k)!=saved.get(k) for k in ['lon','lat','label']) or (body.get('location_unconfirmed') is True)!=bool(obj.get('location_unconfirmed')):raise Conflict('This call was already sent with a different location review. Update the received incident instead.')
   return {'message_id':obj['message_id']}
  check_open(obj)
  if body.get('reviewed') is not True:raise ValueError('Review the live call facts before adding the incident.')
  job=d.store.get(obj.get('job_id',''),'job');draft=d.store.get(job.get('draft_id',''),'draft') if job else None
  if not job or job['state']!='ready' or not draft:raise Conflict('The facts are not ready. Wait or correct the transcript.')
  if body.get('draft_version')!=draft['version'] or body.get('draft_id')!=draft['id'] or body.get('version')!=obj['version']:raise Conflict('The live report changed. Review its current facts.')
  event_geo=body.get('event_location')
  location_held=body.get('location_unconfirmed') is True
  if event_geo and location_held:raise ValueError('A location cannot be both confirmed and held.')
  if event_geo is not None:
   if isinstance(event_geo,dict) and obj.get('world')=='usc' and not str(event_geo.get('id','')).startswith('usc-'):raise ValueError('Choose a USC building or keep the location unconfirmed.')
   if isinstance(event_geo,dict) and obj.get('world')=='city' and str(event_geo.get('id','')).startswith('usc-'):raise ValueError('This call belongs to Downtown LA. Keep an out-of-area location unconfirmed.')
   if not isinstance(event_geo,dict) or not all(type(event_geo.get(k)) in [int,float] and math.isfinite(event_geo[k]) for k in ['lon','lat']):raise ValueError('Choose a valid event location.')
   south,west,north,east=d.operations.map.public()['bounds']
   from .usc_atlas import atlas as usc_atlas,distance as usc_distance
   campus=next((b for b in usc_atlas()['buildings'] if b['id']==event_geo.get('id') and usc_distance(b['center'],[event_geo['lon'],event_geo['lat']])<5),None)
   if not campus and (not west<=event_geo['lon']<=east or not south<=event_geo['lat']<=north):raise ValueError('The event is outside the loaded Downtown LA routing area. Add the incident without an allocation and review its location.')
   if not any(c['location']['role']!='reporter' for c in draft['claims']):raise ValueError('An event detail is needed before confirming the incident location.')
   event_geo={'id':str(event_geo.get('id','operator-confirmed'))[:160],'label':str(event_geo.get('label','Reviewed event location'))[:180],'lon':event_geo['lon'],'lat':event_geo['lat'],'accuracy':'operator_confirmed','source':'operator review','campus_building_id':campus['id'] if campus else None}
  def commit():
   message=d.send_report(draft,True)
   with d.store.transaction():
    obj.update(state='queued',message_id=message['id'],confirmed_event_geo=event_geo,location_unconfirmed=location_held,location_review_note='Operator confirmed the event location while reviewing this call.' if event_geo else None);d.store.put('intake',OPERATOR,obj,expected=body['version'],event='live_report_queued');return {'message_id':message['id']}
  return idem(request,a,body,commit)

 @app.post('/api/demo/intake/{id}/cancel')
 async def cancel(id,request:Request,a=Depends(operator)):
  body=await json_body(request);obj=get(id)
  if obj['state']=='queued':raise Conflict('This report has already been queued. Review it in the incident list.')
  with d.store.transaction():
   obj.update(state='cancelled',places=[]);return public(d.store.put('intake',OPERATOR,obj,event='live_call_cancelled'))

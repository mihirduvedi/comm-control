"""Recoverable local test runs. Archives stay private and retain source file references."""
import json,os
from uuid import UUID
from .store import uid,now,Conflict

def register_runs(app,d,operator,json_body,idem):
 from fastapi import Depends,Request
 folder=d.dir/'saved-runs'
 def guard():
  if any(j['state'] in ['queued','transcribing','extracting'] for j in d.store.list('job')) or any(x['state'] in ['listening','transcribing'] for x in d.store.list('intake')):raise Conflict('Finish or discard the current recording and wait for AI processing before changing runs.')
 def archive():
  folder.mkdir(mode=0o700,exist_ok=True);id=uid();rows=[dict(r) for r in d.store.db.execute('SELECT * FROM objects')];meta={'id':id,'at':now(),'reports':sum(r['kind']=='report' for r in rows),'sessions':sum(r['kind']=='session' for r in rows)}
  path=folder/(id+'.json');fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
  with os.fdopen(fd,'w') as f:json.dump({'meta':meta,'rows':rows},f);f.flush();os.fsync(f.fileno())
  return meta
 @app.get('/api/queue')
 def queue(world:str|None=None,a=Depends(operator)):
  from .worlds import validate,report_world
  validate(world);id='queue-order'+(':'+world if world else '')
  with d.store.transaction():
   old=d.store.get('queue-order','config') if world=='city' else None
   return d.store.get(id,'config') or d.store.put('config','operator',{'id':id,'mode':old['mode'] if old else 'priority','order':[rid for rid in old['order'] if (r:=d.store.get(rid,'report')) and report_world(r)==world] if old else []})
 @app.post('/api/queue')
 async def reorder(request:Request,a=Depends(operator)):
  body=await json_body(request);mode=body.get('mode');ids=body.get('order',[])
  from .worlds import validate,report_world
  world=validate(body.get('world'));queue_id='queue-order'+(':'+world if world else '')
  if mode not in ['priority','manual'] or not isinstance(ids,list) or len(ids)>100 or any(not isinstance(x,str) for x in ids) or len(ids)!=len(set(ids)):raise ValueError('Choose a valid queue order.')
  with d.store.transaction():
   current=d.store.get(queue_id,'config');version=current['version'] if current else 0
   if body.get('version')!=version:raise Conflict('Queue changed. Refresh before reordering.')
   if any(not d.store.get(id,'report') for id in ids):raise ValueError('Only received reports can be reordered.')
   if world and any(report_world(d.store.get(id,'report'))!=world for id in ids):raise ValueError('Queue order belongs to one workspace.')
   return d.store.put('config','operator',{'id':queue_id,'mode':mode,'order':ids if mode=='manual' else [],'updated_at':now()},event='operator_queue_ordered')
 @app.get('/api/demo/runs')
 def runs(a=Depends(operator)):
  saved=[]
  for path in folder.glob('*.json'):
   saved.append(json.loads(path.read_text())['meta'])
  return {'saved':sorted(saved,key=lambda x:x['at'],reverse=True)}
 @app.post('/api/demo/fresh-run')
 async def fresh(request:Request,a=Depends(operator)):
  body=await json_body(request)
  if body.get('confirmation')!='START NEW TEST':raise ValueError('Type START NEW TEST to confirm.')
  mode=body.get('scenario','city')
  if mode not in ['city','site','usc','empty']:raise ValueError('Choose the city demo or an empty test.')
  def start():
   with d.store.transaction():
    guard();saved=archive();d.store.db.execute('DELETE FROM objects');d.store.db.execute('DELETE FROM idempotency')
    # Keep authentication/provider credentials, source audio and event history.
    d.store.put('config','system',{'id':'network','enabled':True,'mode':'direct','bits_per_second':1000,'latency_ms':500,'jitter_ms':0,'loss':0.0,'seed':42,'paused_endpoints':[]})
    d.transport.busy_until=0;d.operations.last_tick=0;d.outgoing_streak=0;d.operations.bootstrap()
    d.store.event('operator','run','fresh_test_started',{'scenario':mode,'saved_run':saved['id']})
   if mode=='city':
    from .city_scenarios import seed_city
    seed_city(d)
   elif mode=='site':
    from .scenarios import seed_scenario
    seed_scenario(d)
   elif mode=='usc':
    from .usc_scenarios import seed_usc
    seed_usc(d)
   return {'scenario':mode,'saved_run':saved,'label':'Default city demo queued.' if mode=='city' else 'Empty test ready.'}
  return idem(request,a,body,start)
 @app.post('/api/demo/runs/{id}/restore')
 async def restore(id,request:Request,a=Depends(operator)):
  body=await json_body(request)
  if body.get('confirmation')!='RESTORE SAVED TEST':raise ValueError('Type RESTORE SAVED TEST to confirm.')
  try:UUID(id)
  except (ValueError,TypeError):raise ValueError('Invalid saved run.')
  path=folder/(id+'.json')
  if not path.is_file():raise ValueError('Saved run not found.')
  def load():
   with d.store.transaction():
    guard();previous=archive();content=json.loads(path.read_text());d.store.db.execute('DELETE FROM objects');d.store.db.execute('DELETE FROM idempotency')
    for row in content['rows']:
     obj=json.loads(row['data']);obj['version']=max(obj.get('version',0),d.store.last_event())+1
     if row['kind']=='job' and obj['state'] in ['queued','transcribing','extracting']:obj.update(state='failed',error='Restored test: review and retry processing.')
     if row['kind']=='message' and obj['state']=='transmitting':obj['state']='queued';obj['part']=0
     d.store.db.execute('INSERT INTO objects VALUES (?,?,?,?,?)',(row['id'],row['kind'],row['scope'],obj['version'],json.dumps(obj)))
    d.transport.busy_until=0;d.operations.last_tick=0;d.store.event('operator','run','saved_test_restored',{'restored':id,'saved_run':previous['id']})
    return {'restored':content['meta'],'saved_run':previous}
  return idem(request,a,body,load)

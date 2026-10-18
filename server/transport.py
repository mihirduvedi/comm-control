"""Real bounded CBOR/frame simulation; no RF or physical connectivity claims."""
import base64
import hashlib
import hmac
import math
import struct
import time
import zlib
from uuid import UUID,uuid5,NAMESPACE_URL
import cbor2
from .store import uid,now,Conflict
from .site import SITE_ID,SITE_VERSION

HEADER=struct.Struct('!BBBB16sIBBIH')
KINDS=['report','instruction','human_response','receipt','urgent_attention','correction']
CLAIMS=['smoke','fire','people_outside','people_inside','access','observation','hazard','request','question','reporter_location','event_time','event_location','violence','self_harm','medical','basic_need']
ASSERTIONS=['asserted','negated','uncertain','hearsay','hypothetical']
ROLES=['reporter','event','access','none']
def b64(x):return base64.b64encode(x).decode()
def un64(x):return base64.b64decode(x)
def uuidbytes(x):return UUID(x).bytes

def compact_payload(kind,p):
 if kind in ['report','correction']:
  return [uuidbytes(p['source_id']),p.get('source_revision',1),bytes.fromhex(p['source_hash']),p.get('origin_label','typed'),[
   [CLAIMS.index(c['kind']),c['value'],c.get('count'),ASSERTIONS.index(c['assertion']),c['excerpt'],c['start'],c['end'],c['location']['raw_text'],ROLES.index(c['location']['role']),c.get('derivation','explicit'),c.get('correction_reason','')] for c in p['claims']],p.get('reply_to'),p.get('response_action','replied'),p.get('captured_at'),uuidbytes(p['correction_of']) if p.get('correction_of') else None,p.get('correction_reason','')]
 return p

def unpack_payload(kind,p):
 if kind in ['report','correction']:
  return {'captured_at':p[7] if len(p)>7 else None,'correction_of':str(UUID(bytes=p[8])) if len(p)>8 and p[8] else None,'correction_reason':p[9] if len(p)>9 else '', 'source_id':str(UUID(bytes=p[0])),'source_revision':p[1],'source_hash':p[2].hex(),'origin_label':p[3],'reply_to':p[5] if len(p)>5 else None,'response_action':p[6] if len(p)>6 else 'replied', 'claims':[
   {'id':str(uuid5(NAMESPACE_URL,str(p[0])+str(i))),'kind':CLAIMS[c[0]],'value':c[1],'count':c[2],'assertion':ASSERTIONS[c[3]],'excerpt':c[4],'start':c[5],'end':c[6],'location_text':c[7],'location_role':ROLES[c[8]],'review_state':'sender_reviewed' if p[3].endswith(' reviewed') else 'unreviewed','derivation':c[9] if len(c)>9 else 'explicit','correction_reason':c[10] if len(c)>10 else ''} for i,c in enumerate(p[4]) ]}
 return p

def encode(kind,session,origin,destination,issued,expires,payload,enforce_limit=True):
 body=cbor2.dumps([1,KINDS.index(kind),uuidbytes(SITE_ID),SITE_VERSION,uuidbytes(session),uuidbytes(origin),uuidbytes(destination),int(issued*1000),int(expires*1000),compact_payload(kind,payload)],canonical=True)
 if enforce_limit and len(body)>1024:raise ValueError(f'Message is {len(body)} bytes; maximum is 1,024. Shorten the reviewed report without removing critical facts. Nothing has been sent.')
 return body

def decode(body):
 if len(body)>1024:raise ValueError('Body too large')
 d=cbor2.loads(body)
 if not isinstance(d,list) or len(d)!=10 or d[0]!=1 or str(UUID(bytes=d[2]))!=SITE_ID or d[3]!=SITE_VERSION:raise ValueError('Unsupported message/site version')
 if not 0<=d[1]<len(KINDS):raise ValueError('Unknown message kind')
 kind=KINDS[d[1]]
 return {'kind':kind,'session_id':str(UUID(bytes=d[4])),'origin':str(UUID(bytes=d[5])),'destination':str(UUID(bytes=d[6])),'issued':d[7]/1000,'expires':d[8]/1000,'payload':unpack_payload(kind,d[9])}

def frames(body,id,revision,key):
 chunks=[body[i:i+128] for i in range(0,len(body),128)]
 if not 1<=len(chunks)<=8:raise ValueError('Invalid frame count')
 result=[]
 for i,chunk in enumerate(chunks):
  header=HEADER.pack(1,0,0,1,uuidbytes(id),revision,i,len(chunks),zlib.crc32(body),len(chunk))
  result.append(header+chunk+hmac.new(key,header+chunk,hashlib.sha256).digest()[:16])
 return result

def read_frame(frame,key):
 if not 48<=len(frame)<=176:raise ValueError('Invalid frame length')
 version,kind,flags,keyid,mid,rev,part,total,crc,length=HEADER.unpack(frame[:32])
 if version!=1 or keyid!=1 or total<1 or total>8 or part>=total or length>128 or len(frame)!=48+length:raise ValueError('Invalid frame header')
 if not hmac.compare_digest(frame[-16:],hmac.new(key,frame[:-16],hashlib.sha256).digest()[:16]):raise ValueError('Frame authentication failed')
 return str(UUID(bytes=mid)),rev,part,total,crc,frame[32:-16]

class Transport:
 def __init__(self,store,key,receiver):
  self.store=store;self.key=key;self.receiver=receiver;self.busy_until=0
  if not store.get('network'):
   store.put('config','system',{'id':'network','enabled':True,'mode':'simulated','bits_per_second':1000,'latency_ms':500,'jitter_ms':0,'loss':0.0,'seed':42,'paused_endpoints':[]})
  # Restart never creates a new logical send. Current batch can replay idempotently.
  with store.transaction():
   for m in store.list('message'):
    if m['state']=='transmitting':m.update(state='queued',next_at=time.time(),part=0);store.put('message',m['origin'],m,event='transport_resumed')

 def config(self):return self.store.get('network')
 def trace(self,id,type,data):self.store.event('transport',id,type,data)

 def enqueue(self,kind,session,origin,destination,payload,ttl=900,id=None,expires=None):
  stamp=time.time();id=id or uid();old=self.store.get(id,'message')
  if old:return old
  expires=expires or stamp+ttl
  body=encode(kind,session,origin,destination,stamp,expires,payload)
  frame_list=frames(body,id,1,self.key)
  m={'id':id,'revision':1,'kind':kind,'session_id':session,'origin':origin,'destination':destination,'issued':stamp,'expires':expires,'body':b64(body),'body_hash':hashlib.sha256(body).hexdigest(),'frames':[b64(f) for f in frame_list],'byte_count':len(body),'frame_bytes':sum(len(f) for f in frame_list),'state':'queued','attempts':0,'part':0,'next_at':stamp,'received_at':None,'expired_on_receipt':False,'human_responses':[]}
  self.store.put('message',origin,m,event='message_queued');self.trace(id,'queued',{'kind':kind,'bytes':len(body),'frames':len(frame_list)})
  return self.store.get(id)

 def receive_frame(self,frame,route_origin,route_destination,stamp):
  id,rev,index,total,crc,chunk=read_frame(frame,self.key)
  partial_id='partial:'+route_origin+':'+id
  p=self.store.get(partial_id,'partial')
  if p and p['deadline']<stamp:p=None
  if not p:
   active=[x for x in self.store.list('partial',route_destination) if x['deadline']>stamp]
   if len(active)>=32:raise ValueError('Reassembly capacity reached')
   p={'id':partial_id,'message_id':id,'origin':route_origin,'destination':route_destination,'revision':rev,'total':total,'crc':crc,'chunks':{},'deadline':stamp+120}
  if (p['revision'],p['total'],p['crc'])!=(rev,total,crc):raise ValueError('Conflicting fragment metadata')
  old=p['chunks'].get(str(index))
  if old and old!=b64(chunk):raise ValueError('Conflicting duplicate fragment')
  p['chunks'][str(index)]=b64(chunk)
  self.store.put('partial',route_destination,p)
  if len(p['chunks'])!=total:return
  body=b''.join(un64(p['chunks'][str(i)]) for i in range(total))
  if len(body)>1024 or zlib.crc32(body)!=crc:raise ValueError('Message checksum/length failed')
  d=decode(body)
  if d['origin']!=route_origin or d['destination']!=route_destination:raise ValueError('Authenticated routing mismatch')
  self.store.db.execute('SAVEPOINT apply_received')
  try:
   self.receiver(id,rev,d,hashlib.sha256(body).hexdigest(),stamp)
   self.store.db.execute('RELEASE apply_received')
  except Exception:
   self.store.db.execute('ROLLBACK TO apply_received');self.store.db.execute('RELEASE apply_received');raise
  self.store.db.execute('DELETE FROM objects WHERE id=?',(partial_id,))

 def tick(self,stamp=None):
  stamp=stamp if stamp is not None else time.time();cfg=self.config()
  with self.store.transaction():
   # In-flight frames survive a link toggle; a paused link prevents new emissions.
   for flight in self.store.list('flight'):
    if flight['due']<=stamp:
     try:self.receive_frame(un64(flight['frame']),flight['origin'],flight['destination'],stamp)
     except (ValueError,KeyError,IndexError,TypeError) as e:self.trace(flight['message_id'],'frame_rejected',{'reason':str(e)})
     self.store.db.execute('DELETE FROM objects WHERE id=?',(flight['id'],))
   for p in self.store.list('partial'):
    if p['deadline']<stamp:self.store.db.execute('DELETE FROM objects WHERE id=?',(p['id'],))
   messages=self.store.list('message')
   for m in messages:
    if m['state'] in ['received','delivery_unconfirmed','expired_unconfirmed']:continue
    if m['expires']<=stamp:
     m['state']='expired_unconfirmed';self.store.put('message',m['origin'],m,event='message_expired');continue
    if m['state']=='awaiting_receipt' and stamp>=m['next_at']:
     if m['attempts']>=5:m['state']='delivery_unconfirmed';self.trace(m['id'],'retry_exhausted',{})
     else:m.update(state='queued',part=0)
     self.store.put('message',m['origin'],m,event='transport_changed')
   if not cfg['enabled'] or stamp<self.busy_until:return
   candidates=[m for m in self.store.list('message') if m['state'] in ['queued','transmitting'] and m['next_at']<=stamp and m['expires']>stamp and m['origin'] not in cfg['paused_endpoints'] and m['destination'] not in cfg['paused_endpoints']]
   # One frame per turn. Oldest last-served session avoids starvation.
   candidates.sort(key=lambda m:(0 if m['kind']=='receipt' else 1 if m['kind']=='urgent_attention' else 2,m.get('last_frame',0),m['issued']))
   if not candidates:return
   m=candidates[0];part=m['part'];frame=un64(m['frames'][part]);airtime=0 if cfg['mode']=='direct' else len(frame)*8/cfg['bits_per_second']
   self.busy_until=stamp+airtime
   if part==0:m['attempts']+=1
   seed=f"{cfg['seed']}:{m['id']}:{m['attempts']}:{part}"
   dice=int.from_bytes(hashlib.sha256(seed.encode()).digest()[:4],'big')/2**32
   delay=0 if cfg['mode']=='direct' else cfg['latency_ms']/1000 + dice*cfg.get('jitter_ms',0)/1000
   lost=cfg['mode']!='direct' and dice<cfg['loss']
   if not lost:
    flight={'id':uid(),'message_id':m['id'],'origin':m['origin'],'destination':m['destination'],'frame':b64(frame),'due':stamp+airtime+delay}
    self.store.put('flight','transport',flight)
   self.trace(m['id'],'frame_lost' if lost else 'frame_transmitted',{'part':part,'attempt':m['attempts'],'bytes':len(frame),'airtime_ms':round(airtime*1000)})
   m.update(part=part+1,last_frame=stamp,state='transmitting')
   if m['part']==len(m['frames']):
    if m['kind']=='receipt':m.update(state='received',received_at=now())
    else:
     wait=max(10,2*(cfg['latency_ms']+cfg.get('jitter_ms',0))/1000+176*8/cfg['bits_per_second'])
     m.update(state='awaiting_receipt',next_at=stamp+airtime+min(60,wait*2**(m['attempts']-1)))
   self.store.put('message',m['origin'],m,event='transport_changed')

 def acknowledge(self,original,endpoint,stamp,expired=False):
  m=self.store.get(original,'message')
  if not m or m['destination']!=endpoint:raise ValueError('Wrong destination')
  # Receipt ID deterministic: duplicates recreate at most one pending attempt.
  receiptid=str(uuid5(UUID(m['id']),'receipt:'+endpoint))
  receipt=self.store.get(receiptid,'message')
  if receipt and receipt['state']=='received' and receipt['expires']>stamp:
   # Reemit identical authenticated bytes; an ID/revision never changes its body.
   receipt.update(state='queued',part=0,next_at=stamp)
   self.store.put('message',endpoint,receipt,event='receipt_replayed')
  elif receipt and receipt['expires']<=stamp:
   self.enqueue('receipt',m['session_id'],endpoint,m['origin'],{'message_id':m['id'],'body_hash':m['body_hash'],'persisted_at':stamp,'expired':expired},ttl=300)
  elif not receipt:self.enqueue('receipt',m['session_id'],endpoint,m['origin'],{'message_id':m['id'],'body_hash':m['body_hash'],'persisted_at':stamp,'expired':expired},ttl=300,id=receiptid)

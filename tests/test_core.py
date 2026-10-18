import json,time,hashlib
import pytest
from uuid import uuid4
from server.store import Store,Conflict,uid
from server.domain import Domain,OPERATOR
from server.transport import frames,read_frame,decode,encode,un64
from server.site import resolve
from server.scenarios import SMOKE,SCENARIOS,fact
from server.models import validate_extraction,instruction_issues

@pytest.fixture
def domain(tmp_path):return Domain(tmp_path)

def deliver(d,steps=1800):
 stamp=time.time()
 for i in range(steps):d.transport.tick(stamp+i*.05)

def configure(d,**kw):
 with d.store.transaction():
  cfg=d.transport.config();cfg.update(mode='direct',latency_ms=0,bits_per_second=100000,**kw);d.store.put('config','system',cfg)

def report(d,index=0):
 name,text,facts=SCENARIOS[index];s=d.create_session(name);draft=d.manual_draft(s['endpoint_id'],s['id'],text,facts);m=d.send_report(draft);return s,draft,m

@pytest.mark.parametrize('text,feature,status',[('east warehouse','east-warehouse','proposed_match'),('north gate','north-gate','proposed_match'),('warehouse',None,'ambiguous'),('over there',None,'unlocated'),('',None,'unlocated'),('west warehouse','west-warehouse','proposed_match'),('warehouse loading side',None,'ambiguous'),('electrical room','east-warehouse','proposed_match')])
def test_locations(text,feature,status):
 r=resolve(text,'east warehouse' if text=='electrical room' else '')
 assert r['feature_id']==feature and r['status']==status
 if text=='electrical room':assert r['geometry_status']=='parent_only'

def test_reporter_event_separation():
 result=validate_extraction(SMOKE,{'event_type':'smoke','facts':SCENARIOS[0][2]})
 c=result['claims'];smoke=next(x for x in c if x['kind']=='smoke');assert next(x for x in c if x['kind']=='reporter_location')['location']['role']=='reporter';assert smoke['location']['feature_id']=='east-warehouse';assert smoke['location']['geometry_status']=='parent_only';assert next(x for x in c if x['kind']=='access')['location']['feature_id']=='north-gate';assert next(x for x in c if x['kind']=='people_inside')['count'] is None

def test_source_offsets_unicode():
 text='At the east warehouse — no fire. Two people outside.'
 c=validate_extraction(text,{'facts':[fact('people_outside','Two people outside','Two people outside.','east warehouse',count=2)]})['claims'][0]
 assert text[c['start']:c['end']]==c['excerpt']

def test_unsupported_evidence_rejected():
 with pytest.raises(ValueError):validate_extraction('Nothing here',{'facts':[fact('smoke','smoke','made up','east warehouse')]})

def test_unknown_occupancy_never_zero():
 c=validate_extraction("I don't know if anyone is inside.",{'facts':[fact('people_inside','Unknown',"I don't know if anyone is inside.",assertion='asserted',count=0)]})['claims'][0]
 assert c['assertion']=='uncertain' and c['count'] is None

@pytest.mark.parametrize('source,draft,issue',[
 ('Do not use the north gate.','Use the north gate.',True),
 ('Wait five minutes.','Wait two minutes.',True),
 ('If smoke increases, report it.','Report it.',True),
 ('Do not use the north gate.','Do not use the north gate.',False),
 ('Go to the east warehouse.','Go to the west warehouse.',True),
 ('Stay outside.','Stay outside.',False)])
def test_instruction_fidelity(source,draft,issue):assert bool(instruction_issues(source,draft))==issue

def test_roundtrip_and_bounded_wire(domain):
 s,dr,m=report(domain);assert m['byte_count']<=1024;assert max(map(lambda f:len(un64(f)),m['frames']))<=176
 decoded=decode(un64(m['body']));assert next(c for c in decoded['payload']['claims'] if c['kind']=='smoke')['excerpt']==SCENARIOS[0][2][1]['excerpt']
 assert domain.operator_snapshot()['reports']==[]
 configure(domain);deliver(domain)
 r=domain.operator_snapshot()['reports'];assert len(r)==1 and r[0]['session_id']==s['id'];assert domain.store.get(m['id'],'message')['state']=='received'

@pytest.mark.parametrize('tamper',['tag','header','body','short'])
def test_tamper_rejected(tamper):
 key=b'x'*32;body=b'hello';frame=bytearray(frames(body,uid(),1,key)[0])
 if tamper=='short':frame=frame[:20]
 else:frame[{'tag':-1,'header':0,'body':32}[tamper]]^=1
 with pytest.raises(ValueError):read_frame(bytes(frame),key)

def test_oversize():
 with pytest.raises(ValueError):encode('human_response',uid(),uid(),uid(),time.time(),time.time()+300,{'text':'x'*2000})

def test_paused_no_side_channel(domain):
 configure(domain,enabled=False);s,dr,m=report(domain);deliver(domain,100)
 assert not domain.operator_snapshot()['reports'];assert domain.store.get(m['id'],'message')['state']=='queued'
 configure(domain,enabled=True);deliver(domain);assert len(domain.operator_snapshot()['reports'])==1

def test_urgent_still_uses_link(domain):
 s=domain.create_session('A');configure(domain,enabled=False)
 with domain.store.transaction():m=domain.transport.enqueue('urgent_attention',s['id'],s['endpoint_id'],OPERATOR,{'text':'Reporter requests immediate assistance'},ttl=300)
 deliver(domain,100);assert not domain.operator_snapshot()['reports']
 configure(domain,enabled=True);deliver(domain);assert domain.operator_snapshot()['reports'][0]['urgency']=='critical'

def test_duplicate_reordered_frames(domain):
 s,dr,m=report(domain);f=[un64(x) for x in m['frames']]
 with domain.store.transaction():
  for frame in [*reversed(f),*f]:domain.transport.receive_frame(frame,m['origin'],m['destination'],time.time())
 assert len(domain.operator_snapshot()['reports'])==1

def test_receipt_is_not_human_ack(domain):
 configure(domain);s,dr,m=report(domain);deliver(domain)
 original=domain.store.get(m['id'],'message');assert original['state']=='received' and original['human_responses']==[]

def test_conflicting_gate_not_unknown_occupancy(domain):
 configure(domain);report(domain,0);report(domain,1);deliver(domain)
 conflicts=domain.store.list('conflict');assert len(conflicts)==1;assert conflicts[0]['feature_id']=='north-gate'

def test_session_isolation(domain):
 configure(domain)
 for i in range(10):
  s=domain.create_session('Reporter '+str(i));text=f'At the north gate, report {i}.';draft=domain.manual_draft(s['endpoint_id'],s['id'],text,[fact('observation',f'report {i}',text,'north gate')]);domain.send_report(draft)
 deliver(domain,4000);reports=domain.operator_snapshot()['reports'];assert len(reports)==10;assert len({r['session_id'] for r in reports})==10
 for i in range(10,100):domain.create_session('Additional reporter '+str(i))
 with pytest.raises(ValueError):domain.create_session('overflow')

def test_source_scope_and_snapshot(domain):
 s,dr,m=report(domain);snap=domain.operator_snapshot();assert 'source_text' not in json.dumps(snap);assert not snap['reports']
 field=domain.field_snapshot({'id':s['endpoint_id'],'session_id':s['id']});assert field['drafts'][0]['source_text']==SMOKE

def instruction(d,s,text='Do not use the north gate. Is anyone inside?'):
 dr=d.manual_draft(OPERATOR,s['id'],text,[],direction='outgoing');dr=d.approve(dr,dr['version']);return dr,d.send_instruction(dr)[0]

def test_closed_recipient_no_receipt(domain):
 configure(domain);s=domain.create_session('A');dr,m=instruction(domain,s);deliver(domain,200)
 assert domain.store.get(m['id'],'inbox')['persisted'] is False
 assert domain.store.get(m['id'],'message')['received_at'] is None
 with domain.store.transaction():
  inbox=domain.store.get(m['id'],'inbox');inbox['persisted']=True;domain.store.put('inbox',s['endpoint_id'],inbox);domain.transport.acknowledge(m['id'],s['endpoint_id'],time.time())
 deliver(domain);assert domain.store.get(m['id'],'message')['state']=='received'

def test_approval_binds_audience_and_content(domain):
 s=domain.create_session('A');dr=domain.manual_draft(OPERATOR,s['id'],'Do not use the north gate.',[],direction='outgoing');dr=domain.approve(dr,dr['version']);dr['text']='Use the north gate.'
 with pytest.raises(Conflict):domain.send_instruction(dr)

def test_same_draft_cannot_double_send(domain):
 s=domain.create_session('A');dr,m=instruction(domain,s)
 fresh=domain.store.get(dr['id'],'draft');assert d_ids(domain.send_instruction(fresh))==[m['id']]

def d_ids(messages):return [m['id'] for m in messages]

def test_human_response_only_on_return_receipt(domain):
 configure(domain);s=domain.create_session('A');dr,m=instruction(domain,s);deliver(domain,150)
 configure(domain,enabled=False)
 with domain.store.transaction():domain.transport.enqueue('human_response',s['id'],s['endpoint_id'],OPERATOR,{'message_id':m['id'],'action':'cannot_follow','text':'Smoke is reaching us.'})
 deliver(domain,100);assert domain.store.get(m['id'],'message')['human_responses']==[]
 configure(domain,enabled=True);deliver(domain)
 response=domain.store.get(m['id'],'message')['human_responses'];assert len(response)==1 and response[0]['action']=='cannot_follow'

def test_expiry_preserves_no_false_receipt(domain):
 configure(domain,enabled=False);s,dr,m=report(domain)
 domain.transport.tick(time.time()+1000);m=domain.store.get(m['id'],'message');assert m['state']=='expired_unconfirmed' and m['received_at'] is None

def test_restart_preserves_source_and_delivery(tmp_path):
 d=Domain(tmp_path);configure(d,enabled=False);s,dr,m=report(d);again=Domain(tmp_path)
 assert again.store.get(dr['id'],'draft')['source_text']==SMOKE;assert not again.operator_snapshot()['reports'];configure(again,enabled=True);deliver(again);assert len(again.operator_snapshot()['reports'])==1

def test_stale_version_conflict(domain):
 s=domain.create_session('A')
 with domain.store.transaction():
  v=domain.store.put('incident','operator',{'id':uid(),'title':'one'});domain.store.put('incident','operator',{**v,'title':'two'},expected=v['version'])
 with pytest.raises(Conflict):
  with domain.store.transaction():domain.store.put('incident','operator',{**v,'title':'three'},expected=v['version'])

"""Revision, time and dependency behavior: exercise the received projection boundary."""
import time
import pytest
from server.domain import Domain,OPERATOR
from server.store import uid
from server.transport import un64,decode
from server.observation_time import observation_time
from server.scenarios import fact
from test_core import configure,deliver,report,instruction

@pytest.mark.parametrize('phrase,delta,status', [('five minutes ago',300,'relative_source'),('two hours ago',7200,'relative_source'),('right now',0,'source_current'),('at 10:30 PM',None,'unknown')])
def test_time_only_normalized_when_explicit(phrase,delta,status):
 result=observation_time([{'kind':'event_time','assertion':'asserted','excerpt':phrase}],10000)
 assert result['observed_at']==(None if delta is None else 10000-delta)
 assert result['observation_time_status']==status

def test_receipt_does_not_invent_observation_time(tmp_path):
 d=Domain(tmp_path);configure(d);s,dr,m=report(d);deliver(d)
 r=d.store.get(m['id'],'report');assert r['observed_at'] is None and r['observation_time_status']=='unknown';assert r['captured_at'] and r['issued_at'] and r['received_at']

def correction(d,s,dr,m):
 newer=d.manual_draft(s['endpoint_id'],s['id'],'The north gate is clear.',[fact('access','North gate clear','The north gate is clear.','north gate')])
 with d.store.transaction():
  newer.update(correction_of=m['id'],correction_reason='Reporter rechecked the gate')
  newer=d.store.put('draft',newer['origin'],newer)
 return d.send_report(newer)

def inject(d,m):
 with d.store.transaction():
  for f in reversed(m['frames']):d.transport.receive_frame(un64(f),m['origin'],m['destination'],time.time())

def test_correction_waits_for_original_then_retains_both(tmp_path):
 d=Domain(tmp_path);s,dr,m=report(d);c=correction(d,s,dr,m)
 assert decode(un64(c['body']))['kind']=='correction'
 inject(d,c);assert not d.store.list('report');assert d.store.get(c['id'],'pending_correction')['state']=='waiting_for_original'
 inject(d,m)
 assert len(d.store.list('report'))==2 and not d.store.list('pending_correction')
 assert d.store.get(m['id'],'report')['superseded_by']==c['id']
 assert d.store.get(c['id'],'report')['correction_of']==m['id']
 inject(d,c);assert len(d.store.list('report'))==2

def test_correction_cannot_modify_other_session(tmp_path):
 d=Domain(tmp_path);s,dr,m=report(d);inject(d,m);other=d.create_session('Other')
 c=correction(d,other,dr,m)
 with pytest.raises(ValueError,match='another reporting session'):inject(d,c)
 assert not d.store.get(c['id'],'report') and not d.store.get(m['id'],'report').get('superseded_by')

def test_replacement_supersedes_only_after_delivery(tmp_path):
 d=Domain(tmp_path);configure(d);s=d.create_session('A');dr,m=instruction(d,s);deliver(d)
 newer=d.manual_draft(OPERATOR,s['id'],'Use the south gate.',[],direction='outgoing')
 with d.store.transaction():newer['replaces_message_id']=m['id'];newer=d.store.put('draft',OPERATOR,newer)
 newer=d.approve(newer,newer['version']);replacement=d.send_instruction(newer)[0]
 assert not d.store.get(m['id'],'inbox').get('superseded_by')
 deliver(d);assert d.store.get(m['id'],'inbox')['superseded_by']==replacement['id']

def test_unreviewed_wire_remains_unreviewed(tmp_path):
 d=Domain(tmp_path);s,dr,m=report(d)
 newer=d.manual_draft(s['endpoint_id'],s['id'],'The south gate is clear.',[fact('access','clear','The south gate is clear.','south gate')]);message=d.send_report(newer,False)
 assert all(c['review_state']=='unreviewed' for c in decode(un64(message['body']))['payload']['claims'])

def test_explicit_west_room_never_uses_east_context():
 from server.site import resolve
 assert resolve('west warehouse electrical room','east warehouse')['feature_id']=='west-warehouse'
 assert resolve('electrical room','east warehouse and west warehouse')['feature_id'] is None
 assert resolve('west warehouse loading side','east warehouse')['feature_id']=='west-loading'

def test_authenticated_malformed_payload_rolls_back_domain(tmp_path):
 d=Domain(tmp_path);s=d.create_session('A')
 with d.store.transaction():m=d.transport.enqueue('human_response',s['id'],s['endpoint_id'],OPERATOR,{'message_id':uid(),'action':'replied','text':'answer'})
 with pytest.raises(ValueError):inject(d,m)
 assert not d.store.list('received') and not d.store.list('report')

def test_retry_exhaustion_keeps_delivery_unconfirmed(tmp_path):
 d=Domain(tmp_path);s,dr,m=report(d)
 with d.store.transaction():cfg=d.transport.config();cfg.update(mode='simulated',loss=1,latency_ms=0,bits_per_second=100000);d.store.put('config','system',cfg)
 start=time.time()
 for i in range(8500):d.transport.tick(start+i*.05)
 sent=d.store.get(m['id'],'message');assert sent['attempts']==5 and sent['state']=='delivery_unconfirmed' and sent['received_at'] is None
 assert not d.store.list('report')

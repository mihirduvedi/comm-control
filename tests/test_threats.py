"""Frozen synthetic regression cases; these do not certify emergency dispatch accuracy."""
import pytest
from server.models import validate_extraction
from server.threats import assess,claim_priority
from server.scenarios import fact
from server.transport import decode,un64
from test_operations import city_report

CASES=[
 ('My husband has a gun and is going to shoot me.','violence',100),
 ("I think I'm going to kill myself.",'self_harm',100),
 ('I am going to end my life.','self_harm',100),
 ('Someone is unconscious at City Hall.','medical',98),
 ('He is not breathing.','medical',98),
 ("I can't breathe.",'medical',98),
 ('There are shots fired near Union Station.','violence',100),
 ("I'm not safe. He has a gun and is going to kill me.",'violence',100),
 ("I don't know, he has a gun and is going to shoot me.",'violence',100),
 ("I am not going to kill myself.",'self_harm',0),
 ("I don't want to die.",'self_harm',0),
 ('In the movie he has a gun and is going to shoot me.','violence',0),
 ('Someone told me there are shots fired.','violence',92),
 ('I am hungry and need food.','basic_need',25),
 ('I am sad and itchy.','observation',25),
 ('I am sad today.','observation',20),
 ('I am gonna die.','observation',85),
]
@pytest.mark.parametrize('text,kind,score',CASES)
def test_evidence_priority_and_polarity(text,kind,score):
 out=validate_extraction(text,{'facts':[fact(kind,'none',text)]})
 c=out['claims'][0];assert c['kind']==kind;assert claim_priority(c)[0]==score
 assert text[c['start']:c['end']]==c['excerpt'];assert c['value'].lower()!='none'

def test_screenshot_failure_is_corrected_without_invented_occupancy():
 text="I'm so scared right now. My husband has a gun and is going to shoot me. I'm really hungry. I need food. I'm really sad right now. I'm really itchy. I think I'm going to kill myself."
 raw={'facts':[fact('people_inside','Occupancy inside unknown','My husband has a gun and is going to shoot me.',assertion='uncertain'),fact('hazard','gun threat','My husband has a gun and is going to shoot me.'),fact('request','food','I need food.'),fact('observation','none',"I think I'm going to kill myself.",assertion='uncertain')]}
 out=validate_extraction(text,raw);claims=out['claims']
 assert [c['kind'] for c in claims[:2]]==['violence','self_harm']
 assert not any(c['kind']=='people_inside' for c in claims)
 assert out['triage']['score']==100 and all(c['count'] is None for c in claims)
 assert out['warnings']

def test_missed_critical_clause_is_recovered_even_when_model_only_returns_food():
 text='I need food. I am going to kill myself.'
 out=validate_extraction(text,{'facts':[fact('basic_need','Food','I need food.')]})
 assert out['claims'][0]['kind']=='self_harm' and out['triage']['score']==100

def test_no_suicidal_intent_inferred_from_sadness():
 out=validate_extraction('I am sad.',{'facts':[fact('observation','Sad','I am sad.')]})
 assert out['triage']['score']==20 and not any(c['kind']=='self_harm' for c in out['claims'])

def test_new_kinds_roundtrip_in_wire_protocol(tmp_path):
 from server.domain import Domain
 d=Domain(tmp_path);s=d.create_session('Synthetic threat');text='I am going to kill myself at City Hall.'
 dr=d.manual_draft(s['endpoint_id'],s['id'],text,[fact('self_harm','Self harm intent',text,'City Hall')]);m=d.send_report(dr)
 assert decode(un64(m['body']))['payload']['claims'][0]['kind']=='self_harm'

def test_critical_case_reassigns_only_unstarted_lower_priority_unit(tmp_path):
 from server.domain import Domain
 from server.transport import un64
 import time
 d=Domain(tmp_path)
 # Two lower priority medical incidents exhaust both medical units.
 for _ in range(2):city_report(d,1)
 before=[a for a in d.store.list('assignment') if a['capability']=='medical'];assert len(before)==2
 s=d.create_session('Synthetic critical');text='I am going to kill myself at City Hall.';dr=d.manual_draft(s['endpoint_id'],s['id'],text,[fact('self_harm','Self harm intent',text,'City Hall')]);m=d.send_report(dr)
 with d.store.transaction():
  for frame in m['frames']:d.transport.receive_frame(un64(frame),m['origin'],m['destination'],time.time())
 # Injured reports also score98: a critical case must NOT steal from comparable priority.
 assert not any(a['report_id']==m['id'] and a['state']!='released' for a in d.store.list('assignment'))
 assert d.store.get(m['id'],'plan')['state']=='resource_needed'

def test_denied_self_harm_cannot_negate_a_separate_active_weapon_threat():
 text='I am not going to kill myself. He has a gun and is going to shoot me.'
 out=validate_extraction(text,{'facts':[fact('self_harm','Combined model mistake',text,assertion='negated')]})
 assert out['claims'][0]['kind']=='violence' and out['triage']['score']==100
 assert any(c['kind']=='self_harm' and c['assertion']=='negated' for c in out['claims'])

def test_no_gun_threat_stays_negated_even_when_model_omits_polarity():
 text='There is no gun threat.';out=validate_extraction(text,{'facts':[fact('violence','Gun threat',text)]})
 assert out['triage']['score']==0 and out['claims'][0]['assertion']=='negated'

def test_medical_reclassification_retains_explicit_count_and_plain_summary():
 text='One person is injured at Union Station.';out=validate_extraction(text,{'facts':[fact('observation','One injured person',text,'Union Station',count=1)]})
 assert out['claims'][0]['kind']=='medical' and out['claims'][0]['count']==1 and out['summary']=='One injured person'

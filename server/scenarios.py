"""Explicitly annotated synthetic fixtures. These never pretend to be model output."""
from .domain import OPERATOR
from .store import now
from .models import validate_extraction

SMOKE="I'm by the east warehouse, the loading side. There's smoke coming out of the electrical room. Two people are outside. I don't know if anyone is still inside. The north gate is blocked."

def fact(kind,value,excerpt,place='',role='event',assertion='asserted',count=-1):
 return {'kind':kind,'value':value,'excerpt':excerpt,'location_text':place,'location_role':role,'assertion':assertion,'count':count}
SCENARIOS=[
 ('Alex Rivera',SMOKE,[
  fact('reporter_location','By the east loading side',"I'm by the east warehouse, the loading side.",'east warehouse, the loading side','reporter'),
  fact('smoke','Smoke from the electrical room',"There's smoke coming out of the electrical room.",'electrical room'),
  fact('people_outside','2 people outside','Two people are outside.','east warehouse',count=2),
  fact('people_inside','Occupancy inside unknown',"I don't know if anyone is still inside.",'east warehouse',assertion='uncertain'),
  fact('access','North gate blocked','The north gate is blocked.','north gate','access')]),
 ('Jordan Chen',"I'm at the north gate now. The north gate is open and clear.",[
  fact('reporter_location','At North Gate',"I'm at the north gate now.",'north gate','reporter'),
  fact('access','North gate is open and clear','The north gate is open and clear.','north gate','access')]),
 ('Sam Okafor',"I'm at the warehouse loading side. I need someone here.",[
  fact('reporter_location','Warehouse loading side unclear',"I'm at the warehouse loading side.",'warehouse loading side','reporter'),
  fact('request','Needs someone at the warehouse','I need someone here.','warehouse loading side')]),
 ('Taylor Brooks','The loading door at the west warehouse will not close. Two deliveries are waiting.',[
  fact('observation','Loading door will not close','The loading door at the west warehouse will not close.','west warehouse'),
  fact('observation','2 deliveries waiting','Two deliveries are waiting.','west warehouse',count=2)]),
]

def seed_scenario(d):
 if d.store.list('report'):raise ValueError('A run already contains reports. Use the existing run or explicitly reset it first.')
 result=[]
 # Domain creation methods own their transactions. Source content is marked as manual annotation.
 for name,text,claims in SCENARIOS:
  s=d.create_session(name)
  draft=d.manual_draft(s['endpoint_id'],s['id'],text,claims)
  with d.store.transaction():
   draft['origin_label']='annotated synthetic fixture';d.store.put('draft',s['endpoint_id'],draft)
  m=d.send_report(d.store.get(draft['id'],'draft'))
  result.append({'session_id':s['id'],'message_id':m['id']})
 return {'queued':result,'label':'Annotated synthetic reports; AI was not run. Every report still traverses the active transport.'}

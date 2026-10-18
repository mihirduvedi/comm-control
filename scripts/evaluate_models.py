#!/usr/bin/env python3
"""Frozen synthetic text evaluation. Real hosted inference; no simulated answers.

Use --run for 40 calls paced within free-tier limits; --failed reruns only failed cases.
ASR is measured separately: these are transcript/extraction and outgoing fidelity cases.
"""
import asyncio,json,time,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server.models import extraction,outgoing
ROOT=Path(__file__).resolve().parents[1]
CASES=[
 ('C01','The north gate is blocked.','access','asserted',None,'north-gate'),
 ('C02','At the west warehouse, two people are outside.','people_outside','asserted',2,'west-warehouse'),
 ('C03','Smoke is coming from the east warehouse.','smoke','asserted',None,'east-warehouse'),
 ('C04','Three people are inside the west warehouse.','people_inside','asserted',3,'west-warehouse'),
 ('C05','There is no fire at the east warehouse.','fire','negated',None,'east-warehouse'),
 ('C06','The south gate is blocked by a truck.','access','asserted',None,'south-gate'),
 ('C07','I need a technician at the operations office.','request','asserted',None,'operations'),
 ('C08','At the east warehouse, five people are outside.','people_outside','asserted',5,'east-warehouse'),
 ('C09','The north gate is open and clear.','access','asserted',None,'north-gate'),
 ('C10','The door at the west warehouse will not close.','observation','asserted',None,'west-warehouse'),
 ('C11','Two people are inside the east warehouse.','people_inside','asserted',2,'east-warehouse'),
 ('C12','Smoke is visible at the central yard.','smoke','asserted',None,'yard'),
 ('C13','Four people are outside the operations office.','people_outside','asserted',4,'operations'),
 ('C14','Please send maintenance to the west warehouse.','request','asserted',None,'west-warehouse'),
 ('C15','The south gate is open.','access','asserted',None,'south-gate'),
 ('C16','At the east warehouse, I do not know how many people are inside.','people_inside','uncertain',None,'east-warehouse'),
 ('C17','Six people are outside the east warehouse.','people_outside','asserted',6,'east-warehouse'),
 ('C18','The north gate is blocked. The south gate is clear.','access','asserted',None,'north-gate'),
 ('C19','Can someone come to the operations office?','request','asserted',None,'operations'),
 ('C20','At the west warehouse, the loading door is stuck.','observation','asserted',None,'west-warehouse'),
 ('H01',"I am at the warehouse loading side. I need somebody here.",'request','asserted',None,None),
 ('H02',"At the east warehouse, I don't know if anyone is still inside.",'people_inside','uncertain',None,'east-warehouse'),
 ('H03','Someone told me there is smoke at the west warehouse. I have not seen it.','smoke','hearsay',None,'west-warehouse'),
 ('H04','If there were a fire at the east warehouse, the drill would stop.','fire','hypothetical',None,'east-warehouse'),
 ('H05','There are three, sorry, two people outside the east warehouse.','people_outside','asserted',2,'east-warehouse'),
 ('H06','I am at the east warehouse. Smoke is coming from the west warehouse.','smoke','asserted',None,'west-warehouse'),
 ('H07','The gate is blocked. I cannot tell which gate.','access','asserted',None,None),
 ('H08','There may be people inside the east warehouse. I am not certain.','people_inside','uncertain',None,'east-warehouse'),
 ('H09','At the north gate, I can see no smoke.','smoke','negated',None,'north-gate'),
 ('H10','There is smoke coming from an electrical room. I do not know which building.','smoke','asserted',None,None),
]
OUT=[
 'Do not use the north gate. Stay outside.',
 'At the east warehouse, stay outside. Ask whether anyone is still inside.',
 'Wait five minutes at the operations office. Do not enter the east warehouse.',
 'If smoke increases, report it. Do not use the north gate.',
 'Do not move the two containers until the operator replies.',
 'Ask if they can follow this instruction. Stay outside the west warehouse.',
 'At 10:30 PM, check in from the south gate. Do not open it.',
 'Use the south gate only when the supervisor confirms. Do not use the north gate.',
 'Report whether the west warehouse door will close. Keep four people outside.',
 'Do not enter. Is anyone still inside the east warehouse?',
]

def cases():
 return [{'id':id,'source':text,'expected':{'kind':kind,'assertion':assertion,'count':count,'feature':feature},'category':'clean' if id[0]=='C' else 'difficult'} for id,text,kind,assertion,count,feature in CASES]+[{'id':f'O{i+1:02d}','source':text,'category':'outgoing'} for i,text in enumerate(OUT)]

async def main():
 frozen=ROOT/'fixtures/evaluation-cases.json'
 if not frozen.exists():frozen.write_text(json.dumps({'proof':'synthetic transcript-level cases; not field audio','cases':cases()},indent=2))
 if '--run' not in sys.argv:return print('Frozen 40 inference cases. Run with --run to use the configured Free-tier API. Domain/state checks are separate tests.')
 selected=json.loads(frozen.read_text())['cases'];resultfile=ROOT/'evidence/model-evaluation.json'
 old=json.loads(resultfile.read_text()).get('cases',[]) if resultfile.exists() else []
 if '--failed' in sys.argv:selected=[c for c in selected if not next((r.get('pass',False) for r in old if r['id']==c['id']),False)]
 results=[r for r in old if r['id'] not in {c['id'] for c in selected}]
 for case in selected:
  start=time.monotonic();entry={'id':case['id'],'category':case['category'],'source':case['source']}
  try:
   if case['category']=='outgoing':
    value=await outgoing(case['source']);passed=not value['issues'];entry['output']=value
   else:
    value=await extraction(case['source']);expected=case['expected'];matches=[f for f in value['claims'] if f['kind']==expected['kind'] or expected['kind']=='request' and f['kind']=='question']
    passed=any(f['assertion']==expected['assertion'] and (expected['count'] is None or f['count']==expected['count']) and f['location']['feature_id']==expected['feature'] for f in matches)
    entry.update(output=value,expected=expected)
   entry.update({'pass':passed,'seconds':round(time.monotonic()-start,3)})
  except Exception as e:entry.update({'pass':False,'error':str(e),'seconds':round(time.monotonic()-start,3)})
  results.append(entry);resultfile.write_text(json.dumps({'method':'Real Groq calls on frozen synthetic transcripts; not ASR or operational-safety validation','cases':results,'passed':sum(r['pass'] for r in results),'total':len(results)},indent=2))
  print(case['id'],'PASS' if entry['pass'] else 'FAIL',entry.get('error',''),flush=True)
  await asyncio.sleep(max(0,20-(time.monotonic()-start)))
 print('Finished:',sum(r['pass'] for r in results),'/',len(results),flush=True)
if __name__=='__main__':asyncio.run(main())

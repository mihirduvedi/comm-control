#!/usr/bin/env python3
"""Small frozen hosted extraction+guard evaluation on synthetic text only.
Not weight training, ASR testing, or clinical/field validation. --run makes API calls.
"""
import asyncio,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from server.models import extraction,CHAT_MODEL
from server.threats import POLICY
CASES=[
 ('T01',"I'm scared. My husband has a gun and is going to shoot me. I need food. I think I'm going to kill myself.",{'violence','self_harm'},90),
 ('T02','There is a person unconscious at Union Station. Please send medical help.',{'medical'},90),
 ('T03','I am hungry and need food at Grand Park.',{'basic_need'},0),
 ('T04','I am not going to kill myself. I need food at City Hall.',{'self_harm','basic_need'},0),
 ('T05','In the movie he has a gun and is going to shoot me. I am discussing a film.',{'violence'},0),
 ('T06','I am sad today. I need a meal at Grand Park.',{'basic_need'},0),
 ('T07','Someone told me shots fired near Union Station. I have not seen it.',{'violence'},90),
 ('T08','A train hit a person near Union Station. They are not breathing.',{'medical'},90),
 ('T09','I am at City Hall. There is smoke at Union Station.',{'smoke'},40),
 ('T10','No fire at City Hall. I am going to kill myself.',{'self_harm'},90),
]
async def main():
 if '--run' not in sys.argv:print('Use --run to evaluate 10 synthetic cases against '+CHAT_MODEL);return
 path=ROOT/'evidence/v6-hosted-threats.json';rows=[]
 for id,text,kinds,minscore in CASES:
  started=time.monotonic()
  try:
   out=await extraction(text);claims=out['claims'];score=out['triage']['score'];found={c['kind'] for c in claims}
   checks={'kinds':kinds<=found,'priority':score>=minscore if minscore else score<40,'no_spurious_occupancy':not any(c['kind']=='people_inside' for c in claims),'literal_evidence':all(text[c['start']:c['end']]==c['excerpt'] for c in claims),'no_none_value':not any(c['value'].lower()=='none' for c in claims)}
   if id=='T09':checks['event_not_caller']=any(c['kind']=='smoke' and c['location'].get('geo',{}).get('label')=='Union Station' for c in claims)
   rows.append({'id':id,'source':text,'checks':checks,'passed':all(checks.values()),'score':score,'claims':claims,'elapsed_s':round(time.monotonic()-started,2)})
  except Exception as e:rows.append({'id':id,'source':text,'passed':False,'error':str(e)})
  path.write_text(json.dumps({'model':CHAT_MODEL,'policy':POLICY,'scope':'Hosted extraction plus semantic guards, synthetic text. No ASR or field validation.','passed':sum(r['passed'] for r in rows),'total':len(rows),'cases':rows},indent=2));print(id,'PASS' if rows[-1]['passed'] else 'FAIL',flush=True)
  await asyncio.sleep(3)
asyncio.run(main())

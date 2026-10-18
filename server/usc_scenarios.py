"""Explicitly fictional facilities reports at real USC buildings."""
from .scenarios import fact
SCENARIOS=[
 ('Morgan Lee','The demo nitrogen tank in SGM reads 145 psi. This is a routine pressure check.',[fact('observation','Demo nitrogen tank at 145 psi','The demo nitrogen tank in SGM reads 145 psi.','SGM')]),
 ('Priya Shah','The same demo nitrogen tank in SGM now reads 220 psi. Please have lab safety review it.',[fact('observation','Demo tank pressure now 220 psi','The same demo nitrogen tank in SGM now reads 220 psi.','SGM'),fact('request','Lab safety review requested','Please have lab safety review it.','SGM')]),
 ('Noah Kim','There is a possible gas leak at the Michelson Center. I smell gas near the lab door.',[fact('hazard','Possible gas leak reported','There is a possible gas leak at the Michelson Center.','Michelson Center',assertion='uncertain'),fact('hazard','Gas odor reported','I smell gas near the lab door.','Michelson Center')]),
 ('Riley Chen','A smoke alarm is sounding in Leavey Library. I cannot see any smoke.',[fact('hazard','Smoke alarm sounding','A smoke alarm is sounding in Leavey Library.','Leavey Library'),fact('smoke','No visible smoke','I cannot see any smoke.','Leavey Library',assertion='negated')]),
 ('Casey Patel','The service door at Tutor Campus Center will not latch. Please send maintenance.',[fact('observation','Service door will not latch','The service door at Tutor Campus Center will not latch.','Tutor Campus Center'),fact('request','Maintenance requested','Please send maintenance.','Tutor Campus Center')]),
 ('Sam Rivera','A light is flickering in Kaprielian Hall. No smoke or gas smell.',[fact('observation','Light flickering','A light is flickering in Kaprielian Hall.','Kaprielian Hall'),fact('smoke','No smoke or gas smell','No smoke or gas smell.','Kaprielian Hall',assertion='negated')])]
def seed_usc(d):
 from .worlds import report_world,session_world
 if any(report_world(r)=='usc' and str(c['location'].get('feature_id','')).startswith('usc-') for r in d.store.list('report') for c in r['claims']):raise ValueError('USC reports already exist. Use New test for a clean facilities run.')
 if sum(session_world(d,s)=='usc' for s in d.store.list('session'))+len(SCENARIOS)>100:raise ValueError('Six campus session slots are needed. Use an existing campus run or start a new test.')
 # Stage only pristine available demo teams. Never move an operator's active or previously used team.
 from .usc_ops import bootstrap
 from .usc_atlas import atlas
 bootstrap(d)
 staging={'Facilities 01':'usc-hughes','Facilities 02':'usc-bovard','Lab Safety 01':'usc-bovard','Lab Safety 02':'usc-leavey','Alarm Technician 01':'usc-tutor','Access Team 01':'usc-kaprielian'}
 buildings={b['id']:b for b in atlas()['buildings']}
 for team in d.store.list('usc_team'):
  if team['status']=='available' and not team.get('ticket_id') and team['version']==1 and team['name'] in staging:
   base=buildings[staging[team['name']]]
   team.update(position=base['center'],demo_staging={'building_id':base['id'],'note':'Simulated starting position for the USC demonstration; not a real team base.'})
   d.store.put('usc_team','operator',team,event='usc_demo_team_staged')
 result=[]
 for name,text,claims in SCENARIOS:
  s=d.create_session(name,'usc');draft=d.manual_draft(s['endpoint_id'],s['id'],text,claims);m=d.send_report(draft);result.append(m['id'])
 return {'label':'Six simulated USC facilities reports queued through the demo link.','message_ids':result}

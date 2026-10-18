"""Independent operating contexts without copying or deleting original evidence."""
def validate(world):
 if world not in [None,'city','usc']:raise ValueError('Choose Downtown LA or USC campus.')
 return world

def report_world(report):
 if report.get('world') in ['city','usc']:return report['world']
 # Old sources predate workspace selection. Infer their context without rewriting them.
 locations=[c['location'] for c in report.get('claims',[]) if c['location']['role']!='reporter']
 confirmed=[l for l in locations if l.get('status')=='operator_confirmed']
 if confirmed:locations=confirmed
 return 'usc' if any(str(l.get('feature_id','')).startswith('usc-') for l in locations) else 'city'

def session_world(d,session):
 if session.get('world') in ['city','usc']:return session['world']
 worlds={report_world(r) for r in d.store.list('report','operator') if r['session_id']==session['id']}
 return 'usc' if worlds=={'usc'} else 'city'

def scope_snapshot(d,snapshot,world):
 validate(world)
 if world is None:return snapshot
 reports=[r for r in snapshot['reports'] if report_world(r)==world];ids={r['id'] for r in reports}
 sessions=[s for s in snapshot['sessions'] if session_world(d,s)==world];sids={s['id'] for s in sessions}
 op=dict(snapshot['operations'])
 for key in ['plans','assignments','actions','announcements']:
  op[key]=[v for v in op[key] if v.get('report_id') in ids]
 if world=='usc':op.update(units=[],closures=[])
 return {**snapshot,'world':world,'reports':[{**r,'world':report_world(r)} for r in reports],'sessions':sessions,'operations':op,
  'messages':[m for m in snapshot['messages'] if m['session_id'] in sids],
  'incidents':[{**i,'report_ids':[id for id in i['report_ids'] if id in ids]} for i in snapshot['incidents'] if any(id in ids for id in i['report_ids'])],
  'conflicts':[c for c in snapshot['conflicts'] if any(id in ids for id in c.get('report_ids',[]))],
  'pending_corrections':[c for c in snapshot['pending_corrections'] if c.get('packet',{}).get('session_id') in sids]}

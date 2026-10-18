"""Versioned fictional site vocabulary. Coordinates are self-authored synthetic geometry."""
import re
SITE_ID='b62036d6-b87d-4e19-b9c1-f243fdf82572'
SITE_VERSION=1
FEATURES=[
 {'id':'east-warehouse','name':'East Warehouse','kind':'building','x':580,'y':210,'w':240,'h':150,'aliases':['east warehouse','eastern warehouse','warehouse east']},
 {'id':'west-warehouse','name':'West Warehouse','kind':'building','x':190,'y':290,'w':220,'h':165,'aliases':['west warehouse','western warehouse','warehouse west']},
 {'id':'north-gate','name':'North Gate','kind':'gate','x':480,'y':90,'w':70,'h':24,'aliases':['north gate','northern gate']},
 {'id':'south-gate','name':'South Gate','kind':'gate','x':480,'y':625,'w':70,'h':24,'aliases':['south gate','southern gate']},
 {'id':'yard','name':'Central Yard','kind':'zone','x':465,'y':380,'w':320,'h':180,'aliases':['central yard','the yard','yard']},
 {'id':'operations','name':'Operations Office','kind':'building','x':180,'y':130,'w':190,'h':95,'aliases':['operations office','ops office','operations','office']},
 {'id':'east-loading','name':'East loading side','kind':'subarea','parent':'east-warehouse','x':580,'y':365,'w':240,'h':28,'aliases':['east loading side','east loading dock']},
 {'id':'west-loading','name':'West loading side','kind':'subarea','parent':'west-warehouse','x':190,'y':462,'w':220,'h':28,'aliases':['west loading side','west loading dock']},
]
BY_ID={f['id']:f for f in FEATURES}
# Retain legacy source vocabulary; new campus choices use only real USC buildings.
from .usc_atlas import atlas as usc_atlas
BY_ID.update({b['id']:{**b,'kind':'building'} for b in usc_atlas()['buildings']})

def sitepack():
 return {'id':SITE_ID,'version':SITE_VERSION,'name':'Harbor Campus','timezone':'America/Los_Angeles','synthetic':True,'license':'CC0-1.0, self-authored synthetic geometry','features':FEATURES}

def normalize(s): return re.sub(r'[^a-z0-9 ]',' ',s.lower()).strip()

def resolve(raw, context='', role='event'):
 text=normalize(raw); whole=normalize(context)
 result={'raw_text':raw,'role':role,'status':'unlocated','feature_id':None,'candidate_ids':[],'precision':'unknown','geometry_status':'unmapped','site_pack_version':SITE_VERSION,'derivation':'explicit'}
 if not text or text in ['unknown','not stated','none','null']: return result
 from .usc_atlas import resolve as usc_resolve
 usc=usc_resolve(raw)
 if len(usc)==1:
  b=usc[0];result.update(status='proposed_match',feature_id=b['id'],precision='building',geometry_status='mapped',named_subarea=b['name']);return result
 if len(usc)>1:result.update(status='ambiguous',candidate_ids=[b['id'] for b in usc]);return result
 from .geography import atlas
 real=atlas().resolve(raw,context)
 if real.get('geo') or real.get('candidate_places'):
  result.update(real,precision=real['geo']['accuracy'] if real.get('geo') else 'unknown',geometry_status='mapped' if real.get('geo') else 'unmapped');return result
 # A room has no geometry. Parent association is proposed, not invented room precision.
 if 'electrical room' in text:
  names=[x for x in ['east warehouse','west warehouse'] if x in text] or [x for x in ['east warehouse','west warehouse'] if x in whole]
  result.update(status='proposed_match',feature_id=names[0].replace(' ','-') if len(names)==1 else None,precision='building',geometry_status='parent_only',named_subarea='Electrical room',derivation='discourse_context')
  if result['feature_id'] is None: result.update(status='ambiguous',candidate_ids=['east-warehouse','west-warehouse'],precision='unknown')
  return result
 matches=[f['id'] for f in FEATURES if any(re.search(r'\b'+re.escape(a)+r'\b',text) for a in f['aliases'])]
 if 'loading' in text:
  if 'east-warehouse' in matches and 'west-warehouse' not in matches:matches=['east-loading']
  elif 'west-warehouse' in matches and 'east-warehouse' not in matches:matches=['west-loading']
  elif 'east warehouse' in whole and 'west warehouse' not in whole:matches=['east-loading']
  elif 'west warehouse' in whole and 'east warehouse' not in whole:matches=['west-loading']
  elif not matches: matches=['east-loading','west-loading']
 if not matches and 'warehouse' in text:
  # Within-turn unique explicit context can resolve a later mention; never another session.
  if 'east warehouse' in whole and 'west warehouse' not in whole: matches=['east-warehouse'];result['derivation']='discourse_context'
  elif 'west warehouse' in whole and 'east warehouse' not in whole: matches=['west-warehouse'];result['derivation']='discourse_context'
  else: matches=['east-warehouse','west-warehouse']
 matches=list(dict.fromkeys(matches))
 if len(matches)==1:
  f=BY_ID[matches[0]];result.update(status='proposed_match',feature_id=f['id'],precision='subarea' if f['kind']=='subarea' else 'building' if f['kind']=='building' else 'zone',geometry_status='mapped')
 elif matches: result.update(status='ambiguous',candidate_ids=matches)
 return result


def urgency(claims, urgent=False):
 from .threats import assess
 a=assess(claims,urgent)
 return a['urgency'],a['reasons'],a['needs_review']

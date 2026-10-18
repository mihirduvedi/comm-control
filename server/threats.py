"""Versioned demo triage policy. Evidence-linked review priority, not a clinical dispatch protocol."""
import re
POLICY='threat-review-3'
CRITICAL_VIOLENCE=r'\b(?:shoot(?:ing)? (?:me|us|him|her|them|someone)|(?:gun|firearm|knife|weapon)\b.{0,75}\b(?:shoot|kill|threat|attack)|(?:going to|gonna|will|wants? to|trying to) (?:shoot|kill|stab) (?:me|us|him|her|them)|(?:active shooter|shots fired|being attacked|being assaulted))\b'
SELF_HARM=r'\b(?:(?:kill|hurt|harm) myself|end my life|take my (?:own )?life|(?:attempted|attempting|commit|committing|considering) suicide|suicidal|want to die)\b'
MEDICAL=r'\b(?:not breathing|cannot breathe|can.t breathe|unconscious|unresponsive|severe bleeding|bleeding heavily|overdos(?:e|ed|ing)|chest pain|heart attack|stroke|seizure|trapped|injured)\b'
NEGATION=r'\b(?:not|never|no longer|don.t|do not|won.t|will not|didn.t|did not|isn.t|is not|wasn.t|was not)\b'
FICTION=r'\b(?:hypothetical(?:ly)?|in (?:a|the) (?:movie|film|novel|game)|fictional (?:scene|story)|training scenario)\b'

def signals(text):
 result=[]
 if re.search(CRITICAL_VIOLENCE,text,re.I):result.append(('violence','Threat of serious violence',100,'safety'))
 if re.search(SELF_HARM,text,re.I):result.append(('self_harm','Suicidal or self-harm intent',100,'medical'))
 if re.search(MEDICAL,text,re.I):result.append(('medical','Urgent medical report',98,'medical'))
 return result

def assertion_for(text,assertion='asserted'):
 if re.search(FICTION,text,re.I):return 'hypothetical'
 # Scope negation to the threat; “not safe” and “don’t know” are not denials.
 denial=r"\b(?:no|without) (?:gun|firearm|weapon|suicidal|suicide|injury|injuries|violence)\b|\b(?:not|never|no longer)\s+(?:(?:going|planning|trying|about) to |gonna |actively )?(?:shoot|kill|hurt|harm|stab|suicidal|injured|bleeding|trapped|unconscious)|\b(?:don.t|do not|won.t|will not|didn.t|did not|isn.t|is not|wasn.t|was not)\s+(?:want to |intend to |plan to |have a gun and )?(?:shoot|kill|hurt|harm|stab|die|attack)|\b(?:don.t|do not) want to die\b"
 if re.search(denial,text,re.I):return 'negated'
 if re.search(r'\bif (?:I|he|she|someone|they) (?:were to |was going to |had a gun)',text,re.I):return 'hypothetical'
 if re.search(r'\b(?:someone told me|I heard|they said|reportedly)\b',text,re.I):return 'hearsay'
 return assertion

def claim_priority(c):
 t=c.get('excerpt','');assertion=c.get('assertion','uncertain');k=c.get('kind','observation')
 if assertion in ['negated','hypothetical']:return 0,'Not an active threat',None
 detected=signals(t)
 if detected:
  kind,label,score,cap=next((x for x in detected if x[0]==k),detected[0])
  if assertion=='hearsay':score=92;label+=' (secondhand, confirm)'
  if assertion=='uncertain':score=94;label+=' (needs confirmation)'
  return score,label,cap
 if k in ['violence','self_harm','medical']:return 75,'Serious concern needs clarification',{'violence':'safety','self_harm':'medical','medical':'medical'}[k]
 if k=='fire':return 92 if assertion=='asserted' else 82,'Fire reported' if assertion=='asserted' else 'Possible fire, confirm','fire'
 if k=='smoke':return 72,'Smoke reported','fire'
 if k=='people_inside' and assertion in ['uncertain','hearsay']:return 65,'Occupancy needs confirmation',None
 if re.search(r'\b(?:going to|gonna|will) die\b',t,re.I):return 85,'Possible immediate danger, clarify details','safety'
 if k=='hazard':
  if re.search(r'\b(?:gas leak|electrical|live wire|collapse|flood|danger|die|hit by|collision|crash)\b',t,re.I):return 85,'Potential immediate hazard, clarify details','safety'
  return 55,'Hazard details need clarification',None
 if k=='access':return 45,'Road or access restriction','traffic'
 if k=='basic_need' or re.search(r'\b(?:hungry|need food|need water|shelter|itchy)\b',t,re.I):return 25,'Basic assistance need','general'
 if k in ['request','question','observation']:return 20,'Routine assistance or observation','general'
 return 5,'Context or location',None

def assess(claims,urgent=False):
 ranked=sorted([{'claim_id':c.get('id'),'score':claim_priority(c)[0],'label':claim_priority(c)[1],'capability':claim_priority(c)[2],'excerpt':c.get('excerpt',''),'assertion':c.get('assertion'),'kind':c.get('kind')} for c in claims],key=lambda x:-x['score'])
 score=100 if urgent else ranked[0]['score'] if ranked else 0
 serious=any(c.get('assertion') in ['uncertain','hearsay'] and claim_priority(c)[0]>=60 for c in claims)
 urgency='critical' if score>=90 else 'elevated' if score>=40 else 'routine'
 if serious and score<90 and not any(c.get('assertion')=='asserted' and c.get('kind') in ['smoke','fire','hazard','access'] for c in claims):urgency='unknown'
 reasons=['Reporter requested immediate assistance'] if urgent else [x['excerpt'] for x in ranked if x['score']>=40][:4]
 return {'policy':POLICY,'score':score,'urgency':urgency,'reasons':reasons,'needs_review':serious or any(x['score']>=85 for x in ranked),'threats':ranked,'label':'Immediate threat' if score>=90 else 'Urgent review' if score>=65 else 'Attention' if score>=40 else 'Routine'}

def rank_claims(claims):return sorted(claims,key=lambda c:-claim_priority(c)[0])

def guard_facts(text,raw):
 """Reject semantic category mismatches and retain literal missed critical clauses."""
 facts=[];warnings=[];items=[]
 for original in raw.get('facts',[]):
  parts=[m.group(0).strip() for m in re.finditer(r'[^.!?\n]+[.!?]?',original.get('excerpt',''))]
  if len(parts)>1 and signals(original.get('excerpt','')):
   for part in parts:
    if signals(part):items.append({**original,'excerpt':part})
   warnings.append('A combined threat excerpt was separated to preserve each statement’s polarity.')
  else:items.append(original)
 for item in items:
  f=dict(item);excerpt=f.get('excerpt','');kind=f.get('kind')
  if kind in ['people_inside','people_outside'] and not re.search(r'\b'+('inside|indoors|occupancy' if kind=='people_inside' else 'outside|outdoors')+r'\b',excerpt,re.I):
   warnings.append('A people-status label without matching source words was rejected.');continue
  if kind in ['event_location','reporter_location'] and re.search(r'\b(?:there is|there.s|I see|coming from)\b.{0,35}\bsmoke\b',excerpt,re.I):f['kind']='smoke';f['value']='Smoke reported';f['location_role']='event'
  detected=signals(excerpt)
  if detected:
   # One clause may describe both violence and self-harm; each gets its own source-linked fact below.
   f['kind']=detected[0][0]
   if f['kind']=='medical' and str(f.get('value','')).strip().lower() not in ['', 'none','null','unknown']:pass
   else:f['value']=detected[0][1]
   if f['kind']!='medical':f['count']=-1
   prior=f.get('assertion','asserted')
   f['assertion']=assertion_for(excerpt,prior if prior in ['uncertain','hearsay','asserted'] else 'asserted')
   if f['assertion']=='uncertain' and re.search(r"\b(?:I think I(?:'m| am)|going to|gonna)\b",excerpt,re.I):f['assertion']='asserted'
  if kind=='basic_need' and not f.get('value'):f['value']='Basic assistance requested'
  if str(f.get('value','')).strip().lower() in ['', 'none','null','unknown']:f['value']=excerpt.strip()[:160]
  facts.append(f)
 for match in re.finditer(r'[^.!?\n]+[.!?]?',text):
  clause=match.group(0).strip()
  for kind,label,_,_ in signals(clause):
   if any(f.get('kind')==kind and (clause in f.get('excerpt','') or f.get('excerpt','') in clause) for f in facts):continue
   facts.append({'kind':kind,'value':label,'count':-1,'assertion':assertion_for(clause),'excerpt':clause,'location_text':'','location_role':'event'})
 return {**raw,'facts':facts},warnings


def assess_report(report):
 result=assess(report['claims'],report.get('urgent_attention',False) or any(c.get('excerpt')=='Reporter requests immediate assistance' for c in report['claims']))
 override=report.get('priority_override')
 if override:
  level=override['urgency'];result.update(urgency=level,score={'critical':100,'elevated':70,'routine':20,'unknown':65}[level],label='Operator priority',reasons=[override['reason']],operator_override=override)
 return result

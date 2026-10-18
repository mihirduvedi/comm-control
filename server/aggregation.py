"""Conservative incident grouping; received source reports remain separate evidence."""
import time
from .store import uid,now
from .geography import distance,point

def location(report):
 for c in report['claims']:
  loc=c['location']
  if loc['role']=='reporter' or loc.get('status')=='needs_confirmation' or c['assertion'] in ['negated','hypothetical']:continue
  if loc.get('geo'):return {'geo':loc['geo']}
  if loc.get('feature_id') and not loc.get('candidate_ids'):return {'site':loc['feature_id']}
 return None

def compatible(a,b):
 from .worlds import report_world
 if report_world(a)!=report_world(b):return False
 if a.get('category')!=b.get('category') or a.get('category') not in ['fire','access']:return False
 la,lb=location(a),location(b)
 if not la or not lb:return False
 ta=a.get('observed_at') or a.get('captured_at') or time.time();tb=b.get('observed_at') or b.get('captured_at') or time.time()
 if abs(ta-tb)>1800:return False
 if la.get('site') or lb.get('site'):return bool(la.get('site') and la.get('site')==lb.get('site'))
 return distance(point(la['geo']),point(lb['geo']))<=80

def group_report(d,report):
 if report.get('incident_id') or report.get('aggregation_hold') or report['status'] in ['resolved','superseded'] or not location(report):return report
 if report.get('category') not in ['fire','access']:return report
 candidates=[r for r in d.store.list('report','operator') if r['id']!=report['id'] and r['status'] not in ['resolved','superseded'] and not r.get('aggregation_hold') and compatible(report,r)]
 incident=None
 for other in reversed(candidates):
  obj=d.store.get(other.get('incident_id',''),'incident')
  if obj and obj['status']!='resolved':incident=obj;break
 if not incident:incident={'id':uid(),'title':report['category_label'] if 'category_label' in report else report['summary'],'report_ids':[r['id'] for r in candidates if not r.get('incident_id')],'status':'open','owner':None,'created_at':now(),'automatic':True,'grouping_rule':'Same incident type, confirmed/proposed event place within 80 m, source times within 30 minutes.'}
 if report['id'] not in incident['report_ids']:incident['report_ids'].append(report['id'])
 for rid in incident['report_ids']:
  old=d.store.get(rid,'report')
  if old and old.get('incident_id')!=incident['id']:old['incident_id']=incident['id'];d.store.put('report','operator',old,event='existing_report_grouped')
 incident['updated_at']=now();d.store.put('incident','operator',incident,event='received_report_grouped');report['incident_id']=incident['id'];return d.store.put('report','operator',report,event='report_incident_associated')

def members(d,report):
 obj=d.store.get(report.get('incident_id',''),'incident')
 from .worlds import report_world
 return [r for id in obj['report_ids'] if (r:=d.store.get(id,'report')) and r['status'] not in ['resolved','superseded'] and report_world(r)==report_world(report)] if obj else [report]

def register_aggregation(app,d,operator,json_body,idem):
 from fastapi import Depends,Request
 @app.post('/api/incidents/{id}/link')
 async def link(id,request:Request,a=Depends(operator)):
  body=await json_body(request)
  if not body.get('reason'):raise ValueError('Explain why these reports belong together.')
  def change():
   with d.store.transaction():
    incident=d.store.get(id,'incident');r=d.store.get(body.get('report_id',''),'report')
    if not incident or not r:raise ValueError('Choose a received report and incident.')
    from .worlds import report_world
    if any(report_world(d.store.get(rid,'report'))!=report_world(r) for rid in incident['report_ids']):raise ValueError('Reports from different workspaces cannot be linked.')
    if incident['version']!=body.get('version'):raise ValueError('The incident changed. Reopen this view.')
    old=d.store.get(r.get('incident_id',''),'incident')
    if old and old['id']!=id:old['report_ids']=[x for x in old['report_ids'] if x!=r['id']];d.store.put('incident','operator',old,event='report_manually_moved')
    incident['report_ids']=list(dict.fromkeys(incident['report_ids']+[r['id']]));d.store.put('incident','operator',incident,event='reports_manually_aggregated')
    r.update(incident_id=id,aggregation_hold=False,grouping_reason=body['reason']);r=d.store.put('report','operator',r,event='report_manually_linked');d.operations.on_report(r);return d.store.get(id,'incident')
  return idem(request,a,body,change)
 @app.post('/api/reports/{id}/separate')
 async def separate(id,request:Request,a=Depends(operator)):
  body=await json_body(request)
  if not body.get('reason'):raise ValueError('Explain why this report is a separate incident.')
  def change():
   with d.store.transaction():
    r=d.store.get(id,'report')
    if not r or r['version']!=body.get('version'):raise ValueError('The report changed. Reopen this view.')
    incident=d.store.get(r.get('incident_id',''),'incident')
    if incident:incident['report_ids']=[x for x in incident['report_ids'] if x!=id];d.store.put('incident','operator',incident,event='report_separated')
    r.update(incident_id=None,aggregation_hold=True,grouping_reason=body['reason']);r=d.store.put('report','operator',r,event='report_separate_incident');d.operations.on_report(r);return d.store.get(id,'report')
  return idem(request,a,body,change)

import copy
from test_api import env
from test_operations import city_report
from server.store import uid,now
from server.domain import OPERATOR


def hs(h):return {**h,'Idempotency-Key':uid()}


def test_more_than_ten_sessions_can_be_created_and_world_limits_are_explicit(env):
 c,d,h=env
 for i in range(12):
  result=c.post('/api/sessions',headers=hs(h),json={'name':'City test '+str(i),'world':'city'});assert result.status_code==200,result.text
 snapshot=c.get('/api/control/snapshot?world=city',headers=h).json();assert len(snapshot['sessions'])==12 and snapshot['limits']['sessions_per_world']==100


def test_remove_and_restore_keeps_evidence_and_closures(env):
 c,d,h=env;r=city_report(d,2);sources=copy.deepcopy(d.store.list('source'));closures=copy.deepcopy(d.store.list('closure'))
 case=c.get('/api/reports/'+r['id']+'/case',headers=h).json();body={'version':case['report']['version'],'action':'archive','note':'Remove this synthetic test incident.','acknowledge_open_items':True,'report_versions':{x['id']:x['version'] for x in case['incident_reports']}}
 result=c.post('/api/reports/'+r['id']+'/case',headers=hs(h),json=body);assert result.status_code==200,result.text
 archived=result.json();assert archived['report']['archived_at'] and archived['report']['status']=='resolved'
 assert d.store.list('source')==sources and d.store.list('closure')==closures
 assert all(a['state']=='released' for a in d.store.list('assignment') if a['report_id']==r['id'])
 denied=c.post('/api/reports/'+r['id']+'/case',headers=hs(h),json={'version':archived['report']['version'],'action':'reopen','note':'Reopen without restoring.'});assert denied.status_code==422
 result=c.post('/api/reports/'+r['id']+'/case',headers=hs(h),json={'version':archived['report']['version'],'action':'restore','note':'Restore the saved incident.','report_versions':{x['id']:x['version'] for x in archived['incident_reports']}});assert result.status_code==200,result.text
 assert not result.json()['report'].get('archived_at') and result.json()['report']['status']=='resolved'


def test_linked_incident_removal_is_atomic_and_requires_all_current_versions(env):
 c,d,h=env;a=city_report(d);b=city_report(d);case=c.get('/api/reports/'+a['id']+'/case',headers=h).json();assert len(case['incident_reports'])==2
 body={'version':case['report']['version'],'action':'archive','note':'Remove grouped demo reports.','acknowledge_open_items':True}
 assert c.post('/api/reports/'+a['id']+'/case',headers=hs(h),json=body).status_code==409
 assert not d.store.get(a['id'],'report').get('archived_at') and not d.store.get(b['id'],'report').get('archived_at')
 body['report_versions']={x['id']:x['version'] for x in case['incident_reports']}
 result=c.post('/api/reports/'+a['id']+'/case',headers=hs(h),json=body);assert result.status_code==200,result.text
 assert all(d.store.get(x['id'],'report').get('archived_at') for x in [a,b])


def test_fresh_voice_start_ends_old_intake_without_deleting_transcript_or_other_world(env):
 c,d,h=env
 for world in ['city','usc']:
  d.store.put('intake',OPERATOR,{'id':world+'-old-call','state':'review','world':world,'created_at':now(),'transcript':'Prior synthetic transcript in '+world,'places':[],'source_ids':[]})
 old=copy.deepcopy(d.store.get('city-old-call','intake'))
 result=c.post('/api/demo/intake/new',headers=hs(h),json={'world':'city'});assert result.status_code==200,result.text
 assert c.get('/api/demo/intake/current?world=city',headers=h).json()['intake'] is None
 assert d.store.get('city-old-call','intake')['transcript']==old['transcript']
 assert d.store.get('city-old-call','intake')['state']=='cancelled'
 assert c.get('/api/demo/intake/current?world=usc',headers=h).json()['intake']['transcript'].startswith('Prior synthetic')
 result=c.post('/api/demo/intake',headers=hs(h),json={'world':'city'});assert result.status_code==200 and result.json()['transcript']==''

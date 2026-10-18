from test_api import env,field_session
from test_operations import city_report
from server.store import uid
from server.cases import case_snapshot


def update(c,h,r,**body):
 return c.post('/api/reports/'+r['id']+'/case',headers={**h,'Idempotency-Key':uid()},json={'version':r['version'],'note':'Checked source with next operator','action':'note',**body})


def test_case_permissions_and_received_sources_only(env):
 c,d,h=env;r=city_report(d);_,fh=field_session(d)
 assert c.get('/api/reports/'+r['id']+'/case',headers=fh).status_code==403
 assert update(c,fh,r).status_code==403
 case=c.get('/api/reports/'+r['id']+'/case',headers=h).json()
 assert case['report']['claims']==r['claims']
 assert 'audio_path' not in str(case) and 'operator_token' not in str(case)


def test_close_requires_review_and_releases_then_reopens(env):
 c,d,h=env;r=city_report(d);plan=d.store.get(r['id'],'plan')
 assert case_snapshot(d,r['id'])['checks']
 assert update(c,h,r,action='close').status_code==422
 assert d.store.get(r['id'],'report')['status']=='open'
 result=update(c,h,r,action='close',acknowledge_open_items=True,owner='Mihir')
 assert result.status_code==200,result.text
 case=result.json();r=case['report']
 assert r['status']=='resolved' and r['owner']=='Mihir'
 assert case['plan']['state']=='closed' and case['checks']
 assert all(a['state']=='released' for a in case['assignments'])
 assert case['entries'][0]['outstanding_items']==r['closeout']['outstanding_items']
 assert all(t['state']==next(x for x in plan['tasks'] if x['id']==t['id'])['state'] for t in case['plan']['tasks'])
 reopened=update(c,h,r,action='reopen').json()
 assert reopened['report']['status']=='open'
 assert any(a['state']=='assigned' for a in reopened['assignments'])
 assert len(reopened['entries'])==2


def test_close_keeps_road_reports_and_claims(env):
 c,d,h=env;r=city_report(d,2);before=case_snapshot(d,r['id'])
 result=update(c,h,r,action='close',acknowledge_open_items=True).json()
 assert result['closures']==before['closures'] and result['report']['claims']==r['claims']
 assert result['report']['closeout']['retained_closure_ids']==[x['id'] for x in before['closures']]
 assert c.patch('/api/reports/'+r['id'],headers=h,json={'version':result['report']['version'],'status':'open','reason':'Skip closeout'}).status_code==422


def test_case_version_validation_atomicity_and_idempotency(env):
 c,d,h=env;r=city_report(d);before=d.store.last_event()
 assert update(c,h,r,version=999,action='close',acknowledge_open_items=True).status_code==409
 assert d.store.last_event()==before
 for body in [{'note':''},{'owner':22},{'action':'invented'},{'note':'x'*2001}]:assert update(c,h,r,**body).status_code==422
 headers={**h,'Idempotency-Key':uid()};path='/api/reports/'+r['id']+'/case';body={'version':r['version'],'action':'note','note':'A saved handover','owner':'Desk A'}
 first=c.post(path,headers=headers,json=body)
 assert first.status_code==200
 assert c.post(path,headers=headers,json=body).json()==first.json()
 assert len(d.store.list('case_entry'))==1
 assert update(c,h,r,action='close',acknowledge_open_items=True).status_code==409
 current=d.store.get(r['id'],'report');closed=update(c,h,current,action='close',acknowledge_open_items=True).json()['report']
 assert update(c,h,closed,action='monitor').status_code==422


def test_legacy_status_cannot_bypass_closeout(env):
 c,d,h=env;r=city_report(d)
 assert c.patch('/api/reports/'+r['id'],headers=h,json={'version':r['version'],'status':'resolved','reason':'Bypass'}).status_code==422
 assert not d.store.list('case_entry')

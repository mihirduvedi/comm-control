from test_api import env,field_session
from test_operations import city_report
from server.store import uid
import pytest

def fresh(h):return {**h,'Idempotency-Key':uid()}

def test_fresh_run_is_operator_only_confirmed_recoverable_and_restores_defaults(env):
 c,d,h=env;r=city_report(d);_,fh=field_session(d)
 cfg=d.operations.config()
 c.patch('/api/operations/config',headers=h,json={'version':cfg['version'],'enabled':False,'auto_assign':False})
 c.post('/api/demo/network',headers=h,json={'enabled':False,'loss':1,'paused_endpoints':['demo']})
 assert c.post('/api/demo/fresh-run',headers=fh,json={'confirmation':'START NEW TEST'}).status_code==403
 assert c.get('/api/demo/runs',headers=fh).status_code==403
 assert c.post('/api/demo/fresh-run',headers=fresh(h),json={'confirmation':'yes'}).status_code==422
 headers=fresh(h);body={'confirmation':'START NEW TEST','scenario':'empty'}
 result=c.post('/api/demo/fresh-run',headers=headers,json=body);assert result.status_code==200,result.text;saved=result.json()['saved_run']
 assert c.post('/api/demo/fresh-run',headers=headers,json=body).json()['saved_run']['id']==saved['id']
 assert not d.store.list('report') and len(d.store.list('unit'))==7
 assert d.operations.config()['auto_assign'] and d.operations.config()['enabled']
 assert d.transport.config()['enabled'] and d.transport.config()['mode']=='direct' and d.transport.config()['loss']==0 and d.transport.config()['paused_endpoints']==[]
 files=list((d.dir/'saved-runs').glob('*.json'));assert len(files)==1 and files[0].stat().st_mode&0o777==0o600
 public=c.get('/api/demo/runs',headers=h).json();assert public['saved'][0]['reports']==1 and 'token' not in str(public) and 'claims' not in str(public)
 assert c.post('/api/demo/runs/'+saved['id']+'/restore',headers=fresh(h),json={'confirmation':'no'}).status_code==422
 loaded=c.post('/api/demo/runs/'+saved['id']+'/restore',headers=fresh(h),json={'confirmation':'RESTORE SAVED TEST'});assert loaded.status_code==200,loaded.text
 assert d.store.get(r['id'],'report') and not d.operations.config()['enabled'] and d.transport.config()['loss']==1
 assert d.store.get(r['id'],'report')['version']>r['version']
 assert len(c.get('/api/demo/runs',headers=h).json()['saved'])==2

def test_default_city_reset_queues_real_packets_and_keeps_source_files(env):
 c,d,h=env;r=city_report(d);folder=d.dir/'origins';folder.mkdir(exist_ok=True);audio=folder/'original.wav';audio.write_bytes(b'private original audio')
 result=c.post('/api/demo/fresh-run',headers=fresh(h),json={'confirmation':'START NEW TEST','scenario':'city'});assert result.status_code==200,result.text
 assert audio.read_bytes()==b'private original audio' and len(d.store.list('session'))==4 and len(d.store.list('message'))==4
 # Default events follow the receiver; reset does not create fake received reports.
 assert not d.store.list('report') and not d.store.list('assignment')
 from test_core import deliver
 deliver(d);assert len(d.store.list('report'))==4 and len(d.store.list('assignment'))==4

def test_reset_refuses_inflight_ai_and_does_not_archive_or_clear(env):
 c,d,h=env;r=city_report(d)
 with d.store.transaction():d.store.put('job','operator',{'id':uid(),'state':'extracting'})
 result=c.post('/api/demo/fresh-run',headers=fresh(h),json={'confirmation':'START NEW TEST','scenario':'empty'})
 assert result.status_code==409 and d.store.get(r['id'],'report') and not list((d.dir/'saved-runs').glob('*.json'))


def test_compat_reset_restores_city_roster_synchronously_even_when_tick_is_throttled(env):
 import time
 c,d,h=env
 d.operations.last_tick=time.time()
 result=c.post('/api/demo/reset',headers=h,json={'confirmation':'RESET SYNTHETIC RUN'})
 assert result.status_code==200
 assert len(d.store.list('unit'))==7
 assert all(u['status']=='available' and u['assignment_id'] is None for u in d.store.list('unit'))
 assert d.operations.last_tick==0

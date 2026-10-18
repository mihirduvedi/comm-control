import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from uuid import uuid4
import httpx
import pytest
from fastapi.testclient import TestClient
from server import demo_budget,models
from server.demo_budget import DemoBudget,DemoLimit,Limits
from scripts.public_demo import create_public_app

def generous(**kw):return replace(Limits(per_minute=1000,per_hour=1000,per_day=1000,lifetime=1000,visitor_hour=1000,visitor_day=1000),**kw)

def test_persistent_global_cap_survives_restarts_and_concurrent_visitors(tmp_path):
 path=tmp_path/'budget.db';limits=generous(lifetime=4)
 a=DemoBudget(path,limits);b=DemoBudget(path,limits)
 def reserve(i):
  try:(a if i%2 else b).reserve('visitor-'+str(i));return True
  except DemoLimit:return False
 with ThreadPoolExecutor(max_workers=8) as pool:assert sum(pool.map(reserve,range(20)))==4
 with pytest.raises(DemoLimit,match='budget is used up'):DemoBudget(path,limits).reserve('fresh-visitor')

def test_visitor_and_global_limits(tmp_path):
 stamp=[10000.];b=DemoBudget(tmp_path/'b',generous(visitor_hour=2,per_hour=3),lambda:stamp[0])
 b.reserve('same-IP-hash');b.reserve('same-IP-hash')
 with pytest.raises(DemoLimit):b.reserve('same-IP-hash')
 b.reserve('different-IP')
 with pytest.raises(DemoLimit,match='shared hourly'):b.reserve('another-IP')
 stamp[0]+=3601;b.reserve('same-IP-hash')

def test_burst_daily_expiry_and_missing_identity_fail_closed(tmp_path):
 stamp=[10000.];b=DemoBudget(tmp_path/'burst',generous(per_minute=1,per_day=2),lambda:stamp[0])
 with pytest.raises(DemoLimit):b.reserve(None)
 b.reserve('a')
 with pytest.raises(DemoLimit,match='busy'):b.reserve('b')
 stamp[0]+=61;b.reserve('b');stamp[0]+=3601
 with pytest.raises(DemoLimit,match='daily'):b.reserve('c')
 stamp[0]+=86400
 with pytest.raises(DemoLimit,match='expired'):b.reserve('d')

@pytest.fixture
def public(tmp_path,monkeypatch):
 monkeypatch.setattr(demo_budget,'active_budget',None)
 monkeypatch.setattr(models,'provider_key',lambda:'private-test-key')
 monkeypatch.setattr(models,'free_tier_confirmed',lambda:True)
 monkeypatch.setenv('COMM_PUBLIC_FREE_VERIFIED','yes')
 monkeypatch.setenv('COMM_PROVIDER_USAGE_FILE',str(tmp_path/'provider-usage.json'))
 budget=DemoBudget(tmp_path/'budget.sqlite',generous(visitor_hour=2))
 app=create_public_app(tmp_path/'run',workers=False,voice_enabled=True,budget=budget)
 with TestClient(app,base_url='https://demo.example') as client:yield client,app.state.domain,budget

def headers(ip='198.51.100.1'):
 return {'CF-Connecting-IP':ip,'Origin':'https://demo.example','Idempotency-Key':str(uuid4())}

def test_queued_extraction_charges_original_visitor_and_stops_before_http(public,monkeypatch):
 c,d,b=public;seen=[];original=httpx.AsyncClient
 def handler(request):
  seen.append(str(request.url))
  return httpx.Response(200,json={'choices':[{'message':{'content':json.dumps({'event_type':'maintenance','facts':[{'kind':'request','value':'Maintenance requested','count':-1,'assertion':'asserted','excerpt':'Please send maintenance to City Hall.','location_text':'City Hall','location_role':'event'}]})}}]})
 monkeypatch.setattr(models.httpx,'AsyncClient',lambda **kw:original(**kw,transport=httpx.MockTransport(handler)))
 for i in range(2):
  created=c.post('/api/demo/intake',headers=headers(),json={'world':'city'})
  assert created.status_code==200,created.text
  call=created.json()
  response=c.post('/api/demo/intake/'+call['id']+'/revise',headers=headers(),json={'version':call['version'],'text':'Please send maintenance to City Hall.','reason':'Fictional test'})
  assert response.status_code==200,response.text
  assert asyncio.run(d.process_next())
  assert d.store.get(response.json()['job_id'],'job')['state']=='ready',d.store.get(response.json()['job_id'],'job').get('error')
  c.post('/api/demo/intake/'+call['id']+'/cancel',headers=headers(),json={})
 assert len(seen)==2
 status=c.get('/api/public-demo/status',headers=headers()).json()
 assert status['voice_enabled'] is False and status['visitor_hour_remaining']==0
 for path in ['/api/utterances','/api/utterances/text','/api/jobs/fake/retry','/api/sources/fake/text','/api/inbox/fake/listen','/api/demo/intake/fake/audio']:
  assert c.post(path,headers=headers(),json={}).status_code==429
 assert len(seen)==2
 assert c.get('/api/control/snapshot',headers=headers()).status_code==200
 reset=c.post('/api/demo/reset',headers=headers(),json={'confirmation':'RESET SYNTHETIC RUN'})
 assert reset.status_code==200,reset.text
 assert c.get('/api/public-demo/status',headers=headers()).json()['visitor_hour_remaining']==0
 assert c.get('/api/public-demo/status',headers=headers('198.51.100.2')).json()['visitor_hour_remaining']==2
 assert demo_budget.visitor.get() is None

def test_worker_cannot_call_provider_without_attribution(public):
 c,d,b=public
 with pytest.raises(DemoLimit):models.reserve_request()
 assert b.status('test')['total_remaining']==1000

def test_upload_size_and_cross_origin_rejected_before_work(public):
 c,d,b=public
 assert c.post('/api/utterances',headers=headers(),content=b'x'*(2*1024*1024+1)).status_code==413
 h=headers();h['Origin']='https://unrelated.example'
 assert c.post('/api/demo/intake',headers=h,json={}).status_code==403
 assert b.status('test')['total_remaining']==1000

def test_owner_free_tier_verification_required(tmp_path,monkeypatch):
 monkeypatch.setattr(models,'provider_key',lambda:'private-test-key')
 monkeypatch.setattr(models,'free_tier_confirmed',lambda:True)
 monkeypatch.delenv('COMM_PUBLIC_FREE_VERIFIED',raising=False)
 with pytest.raises(RuntimeError,match='owner verification'):create_public_app(tmp_path,workers=False,voice_enabled=True)


def test_public_live_updates_work_without_disclosing_an_operator_key(public):
 c,d,b=public
 with c.websocket_connect('wss://demo.example/api/live',headers={'Origin':'https://demo.example'}) as ws:
  ws.send_json({'token':'','after':0})
  result=ws.receive_json()
  assert 'events' in result or 'heartbeat' in result
  assert d.secrets['operator_token'] not in json.dumps(result)

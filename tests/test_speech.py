import asyncio,io,wave
import pytest
from test_api import env
from server import speech


def clip():
 b=io.BytesIO()
 with wave.open(b,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(b'\x01\x00'*240)
 return b.getvalue()


def test_chunking_preserves_exact_text_and_limit():
 text='Stay 200 feet away. Do not enter City Hall. Is anyone still inside? '*12
 parts=speech.chunks(text)
 assert ''.join(parts)==text and all(0<len(p)<=200 for p in parts)
 for text in ['','[laugh] Stay outside.','x'*4001]:
  with pytest.raises(ValueError):speech.chunks(text)


def test_natural_voice_exact_payload_cache_and_failure(tmp_path,monkeypatch):
 calls=[];budget=[]
 monkeypatch.setattr(speech.models,'provider_key',lambda:'test-only')
 monkeypatch.setattr(speech.models,'reserve_request',lambda:budget.append(1))
 class Response:status_code=200;content=clip()
 class Client:
  def __init__(self,**kw):pass
  async def __aenter__(self):return self
  async def __aexit__(self,*a):pass
  async def post(self,url,**kw):calls.append(kw['json']);return Response()
 monkeypatch.setattr(speech.httpx,'AsyncClient',Client)
 text='Do not enter City Hall. Stay 200 feet away. '*8
 async def run():
  a,b=await asyncio.gather(speech.render_speech(text,tmp_path),speech.render_speech(text,tmp_path))
  assert a==b
  assert ''.join(x['input'] for x in calls)==text
  assert len(budget)==len(calls)==len(speech.chunks(text))
  with wave.open(str(a)) as w:assert w.getnframes()==240*len(calls)
  Response.status_code=429
  with pytest.raises(ValueError,match='provider 429'):await speech.render_speech('Retry text',tmp_path)
  assert len(list(tmp_path.glob('*.wav')))==1
  Response.status_code=200;Response.content=b'bad'
  with pytest.raises(ValueError,match='invalid audio'):await speech.render_speech('Invalid clip',tmp_path)
 asyncio.run(run())


def test_listen_authorization_expiry_and_voice_route(env,tmp_path,monkeypatch):
 from test_api import field_session
 from server.store import uid
 import time
 c,d,h=env;s,fh=field_session(d);_,other=field_session(d,'Other caller');id=uid();audio=tmp_path/'preview.wav';audio.write_bytes(clip());calls=[]
 d.store.put('inbox',s['endpoint_id'],{'id':id,'endpoint':s['endpoint_id'],'text':'Do not enter.','body_hash':'test','expires_at':time.time()+300})
 async def render(text,folder,voice):calls.append((text,voice));return audio
 monkeypatch.setattr(speech,'render_speech',render)
 assert c.post('/api/inbox/'+id+'/listen',headers=h).status_code==403
 assert c.post('/api/inbox/'+id+'/listen',headers=other).status_code==403
 response=c.post('/api/inbox/'+id+'/listen?voice=troy',headers=fh)
 assert response.status_code==200 and response.content==clip() and calls==[('Do not enter.','hannah')]
 inbox=d.store.get(id,'inbox');inbox['expires_at']=time.time()-1;d.store.put('inbox',s['endpoint_id'],inbox)
 assert c.post('/api/inbox/'+id+'/listen',headers=fh).status_code==422
 assert len(calls)==1


def test_budget_failure_is_explained_before_network(tmp_path,monkeypatch):
 monkeypatch.setattr(speech.models,'provider_key',lambda:'test-only')
 def cap():raise RuntimeError('App demo budget reached')
 monkeypatch.setattr(speech.models,'reserve_request',cap)
 with pytest.raises(ValueError,match='App demo budget reached'):asyncio.run(speech.render_speech('Stay outside.',tmp_path))
 assert not list(tmp_path.glob('*.wav'))


def test_speaker_identity_is_stable_and_persisted(env):
 from server.speakers import caller_voice,OPERATOR_VOICE
 from server.domain import Domain
 c,d,h=env
 alex=d.create_session('Alex Rivera');again=d.create_session('Alex Rivera');jamie=d.create_session('Jamie Chen')
 assert alex['demo_voice']==again['demo_voice']==caller_voice(' alex  RIVERA ')
 assert jamie['demo_voice']!=alex['demo_voice'] and OPERATOR_VOICE=='hannah'
 restored=Domain(d.dir)
 assert restored.session(alex['id'])['demo_voice']==alex['demo_voice']
 # Pre-existing sessions receive a one-time assignment without changing their identity or token.
 old=d.session(jamie['id']);old.pop('demo_voice');d.store.put('session','operator',old)
 restored=Domain(d.dir);migrated=restored.session(jamie['id'])
 assert migrated['demo_voice']==jamie['demo_voice'] and migrated['token']==jamie['token']

import asyncio,wave,array
from pathlib import Path
import pytest,httpx
from server import models
from server.domain import Domain
from server.scenarios import fact
from test_core import configure,deliver

@pytest.mark.parametrize('status,phrase',[(401,'rejected the API key'),(429,'rate limit'),(503,'failed (503)')])
def test_provider_failures_are_recoverable(status,phrase):
 with pytest.raises(RuntimeError,match=__import__('re').escape(phrase)):models.check_provider(httpx.Response(status))

@pytest.mark.parametrize('case',['silent','corrupt','too_long'])
def test_bad_audio_never_invents_text(tmp_path,monkeypatch,case):
 monkeypatch.setattr(models,'provider_key',lambda:'test-key');monkeypatch.setattr(models,'reserve_request',lambda:None)
 p=tmp_path/'source.wav'
 if case=='corrupt':p.write_bytes(b'not an audio file')
 else:
  with wave.open(str(p),'wb') as w:
   w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes(array.array('h',[0 if case=='silent' else 100]*int(16000*(1 if case=='silent' else 61))).tobytes())
 with pytest.raises(ValueError):asyncio.run(models.transcribe(p))
 assert p.exists()

def test_model_failure_keeps_source_and_job_error(tmp_path,monkeypatch):
 d=Domain(tmp_path);s=d.create_session('A');j=d.new_job(s['endpoint_id'],s['id'],'inbound',text='The north gate is blocked.')
 async def fail(text):raise RuntimeError('Provider unavailable; retry')
 monkeypatch.setattr(models,'extraction',fail);asyncio.run(d.process_next())
 assert d.store.get(j['id'],'job')['state']=='failed'
 assert d.store.get(j['source_id'],'source')['text']=='The north gate is blocked.'
 assert not d.store.list('report')

def test_question_is_in_actual_recipient_text(monkeypatch):
 async def chat(*args,**kwargs):return {'text':'At the east warehouse, stay outside. Do not use the north gate.','questions':['Ask whether anyone is still inside.']}
 monkeypatch.setattr(models,'local_chat',chat)
 result=asyncio.run(models.outgoing('At the east warehouse, stay outside. Do not use the north gate. Ask whether anyone is still inside.'))
 assert 'Is anyone still inside?' in result['text'] and not result['issues']

def test_twenty_turns_across_ten_sessions(tmp_path):
 d=Domain(tmp_path);configure(d)
 for i in range(10):
  s=d.create_session('Reporter '+str(i))
  for turn in range(2):
   text=f'At the south gate, report {i} turn {turn}.'
   dr=d.manual_draft(s['endpoint_id'],s['id'],text,[fact('observation',f'{i}:{turn}',text,'south gate')]);d.send_report(dr)
 deliver(d,4000);reports=d.operator_snapshot()['reports']
 assert len(reports)==20 and len({r['session_id'] for r in reports})==10
 assert all(sum(r['session_id']==s['id'] for r in reports)==2 for s in d.store.list('session'))

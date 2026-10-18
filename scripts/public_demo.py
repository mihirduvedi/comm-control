"""Explicit public sample workspace with an optional, bounded Free-tier voice demo."""
import hashlib
import hmac
import os
import json
import re
from pathlib import Path
from starlette.responses import HTMLResponse,JSONResponse
from server import demo_budget,models
from server.main import create_app

AI_PATH=re.compile(r'/api/(?:utterances(?:/text)?|jobs/[^/]+/retry|sources/[^/]+/text|demo/intake/[^/]+/(?:audio|revise)|inbox/[^/]+/listen)$')
MAX_BODY=2*1024*1024


def create_public_app(data_dir=None,workers=True,voice_enabled=None,budget=None):
 data_dir=Path(data_dir or os.environ['COMM_PUBLIC_DEMO_DATA'])
 enabled=(os.environ.get('COMM_PUBLIC_VOICE')=='yes') if voice_enabled is None else voice_enabled
 if enabled and not (models.provider_key() and models.free_tier_confirmed() and os.environ.get('COMM_PUBLIC_FREE_VERIFIED')=='yes'):
  raise RuntimeError('Public voice requires a privately configured key, confirmed Free tier and an explicit owner verification.')
 inner=create_app(str(data_dir),workers=workers);domain=inner.state.domain
 ledger=budget or demo_budget.DemoBudget(data_dir/'public-voice-budget.sqlite3')
 demo_budget.active_budget=ledger if enabled else None
 if not domain.store.list('report','operator'):
  from server.city_scenarios import seed_city
  seed_city(domain)

 class PublicDemo:
  state=inner.state
  async def __call__(self,scope,receive,send):
   if scope['type']=='websocket':
    incoming=dict(scope['headers']);origin=incoming.get(b'origin')
    if origin and origin!=b'https://'+incoming.get(b'host',b''):
     return await send({'type':'websocket.close','code':1008})
    headers=[(k,v) for k,v in scope['headers'] if k not in [b'host',b'origin',b'cookie']]+[(b'host',b'127.0.0.1:8765'),(b'origin',b'http://127.0.0.1:8765')]
    authenticated=False
    async def public_socket_receive():
     nonlocal authenticated
     event=await receive()
     if event['type']=='websocket.receive' and not authenticated:
      authenticated=True
      try:
       value=json.loads(event.get('text','{}'))
       if not value.get('token'):value['token']=domain.secrets['operator_token']
       event={**event,'text':json.dumps(value)}
      except (ValueError,TypeError,AttributeError):pass
     return event
    return await inner({**scope,'headers':headers},public_socket_receive,send)
   if scope['type']!='http':return await inner(scope,receive,send)
   path=scope['path'];headers_in=dict(scope['headers'])
   # Cloudflare overwrites this header at the edge; only the loopback listener is exposed through the tunnel.
   ip=headers_in.get(b'cf-connecting-ip') or str((scope.get('client') or ('local',0))[0]).encode()
   who=hmac.new(domain.secrets['key'].encode(),ip,hashlib.sha256).hexdigest()
   status=ledger.status(who);status['voice_enabled']=enabled and status['voice_enabled']
   if not enabled:status['message']='Hosted voice AI is disabled on this instance.'
   if path=='/api/public-demo/status':return await JSONResponse(status)(scope,receive,send)
   if path=='/':
    mode='Voice processing uses the host’s Free-tier Groq account. Your audio is sent to Groq. Each network (IP address) has 15 model calls per hour; a report uses several calls. Shared caps are 60 calls per hour, 100 per day and 150 total, with access expiring after 24 hours. Limits stop processing; there is no paid fallback.' if enabled else 'Hosted voice AI is disabled here. Run the repository locally with your own key to use voice intake.'
    page='''<!doctype html><html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Comm Control Live Demo</title><body style="font-family:system-ui;max-width:720px;margin:70px auto;padding:24px;color:#193d5b;background:#f0f7fc"><h1>Comm Control</h1><h2>From a spoken report to a coordinated response.</h2><p>A shared, interactive sample workspace with fictional incidents and teams. Explore the map, response plans, resources and queues.</p><p><strong>Public demo:</strong> changes and reports are visible to other visitors. Use fictional information only.</p><p>'''+mode+'''</p><p>Record up to 30 seconds. Your key is never requested or exposed.</p><p><a style="display:inline-block;padding:16px 24px;background:#2874bf;color:white;border-radius:12px;text-decoration:none" href="/control">Open interactive demo →</a></p><p><a href="https://github.com/mihirduvedi/comm-control">Source code and local setup</a></p><p>Temporary link: requires the host laptop to remain running. No real dispatch, live GPS or live traffic.</p></body></html>'''
    return await HTMLResponse(page)(scope,receive,send)
   origin=headers_in.get(b'origin')
   expected=b'https://'+headers_in.get(b'host',b'')
   if origin and origin not in [expected,b'http://127.0.0.1:8877',b'http://localhost:8877']:
    return await JSONResponse({'message':'Open this action from the Comm Control demo.'},status_code=403)(scope,receive,send)
   if scope['method'] not in ['GET','HEAD','OPTIONS']:
    if AI_PATH.fullmatch(path):
     if not enabled:return await JSONResponse({'message':'Hosted voice AI is disabled on this instance.'},status_code=403)(scope,receive,send)
     try:ledger.check(who)
     except demo_budget.DemoLimit as error:
      return await JSONResponse({'message':str(error)},status_code=429,headers={'Retry-After':str(error.retry_after)})(scope,receive,send)
    # Bound uploads even if Content-Length is omitted or forged. Read before model work.
    body=bytearray()
    while True:
     event=await receive()
     if event['type']=='http.disconnect':return
     body.extend(event.get('body',b''))
     if len(body)>MAX_BODY:return await JSONResponse({'message':'Public demo uploads must be under 2 MB and recordings no longer than 30 seconds.'},status_code=413)(scope,receive,send)
     if not event.get('more_body'):break
    delivered=False
    async def bounded_receive():
     nonlocal delivered
     if not delivered:delivered=True;return {'type':'http.request','body':bytes(body),'more_body':False}
     return await receive()
    forwarded_receive=bounded_receive
   else:forwarded_receive=receive
   headers=[(k,v) for k,v in scope['headers'] if k.lower() not in [b'host',b'origin',b'cookie']]
   headers.append((b'host',b'127.0.0.1:8765'))
   if scope['method'] not in ['GET','HEAD']:headers.append((b'origin',b'http://127.0.0.1:8765'))
   if not any(k.lower()==b'authorization' for k,v in headers):headers.append((b'authorization',('Bearer '+domain.secrets['operator_token']).encode()))
   context=demo_budget.visitor.set(who)
   try:return await inner({**scope,'headers':headers,'server':('127.0.0.1',8877),'scheme':'http'},forwarded_receive,send)
   finally:demo_budget.visitor.reset(context)
 return PublicDemo()

app=create_public_app() if os.environ.get('COMM_PUBLIC_DEMO_DATA') else None

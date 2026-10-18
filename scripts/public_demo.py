"""Explicit public sample workspace, separate from private operator data."""
import os
from starlette.responses import HTMLResponse,JSONResponse
from server.main import create_app
inner=create_app(os.environ['COMM_PUBLIC_DEMO_DATA']);d=inner.state.domain
if not d.store.list('report','operator'):
 from server.city_scenarios import seed_city
 seed_city(d)
class PublicDemo:
 async def __call__(self,scope,receive,send):
  if scope['type']!='http':return await inner(scope,receive,send)
  path=scope['path']
  if path=='/':
   return await HTMLResponse('''<!doctype html><html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Comm Control Live Demo</title><body style="font-family:system-ui;max-width:720px;margin:70px auto;padding:24px;color:#193d5b;background:#f0f7fc"><h1>Comm Control</h1><h2>From a spoken report to a coordinated response.</h2><p>A shared, interactive sample workspace with fictional incidents and teams. Explore the map, response plans, resources and queues.</p><p><strong>Public demo:</strong> changes are visible to other visitors. Use fictional information only. Hosted voice AI is disabled here. Run the repository locally with your own key to use voice intake.</p><p><a style="display:inline-block;padding:16px 24px;background:#2874bf;color:white;border-radius:12px;text-decoration:none" href="/control">Open interactive demo →</a></p><p><a href="https://github.com/mihirduvedi/comm-control">Source code and local voice setup</a></p><p>Temporary link: requires the host laptop to remain running. No real dispatch, live GPS or live traffic.</p></body></html>''')(scope,receive,send)
  if scope['method']!='GET' and any(x in path for x in ['/utterances/','/intake/','/process','/speech','/transcribe']):
   return await JSONResponse({'message':'Hosted voice AI is disabled in this public demo. Use the local setup for voice intake.'},status_code=403)(scope,receive,send)
  headers=[(k,v) for k,v in scope['headers'] if k.lower() not in [b'host',b'origin',b'cookie']]
  headers.append((b'host',b'127.0.0.1:8877'))
  if scope['method'] not in ['GET','HEAD']:headers.append((b'origin',b'http://127.0.0.1:8877'))
  if not any(k.lower()==b'authorization' for k,v in headers):headers.append((b'authorization',('Bearer '+d.secrets['operator_token']).encode()))
  return await inner({**scope,'headers':headers,'server':('127.0.0.1',8877),'scheme':'http'},receive,send)
app=PublicDemo()

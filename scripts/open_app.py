#!/usr/bin/env python3
import argparse,json,webbrowser
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import URLError
from urllib.parse import urlsplit,urlunsplit,parse_qsl,urlencode
parser=argparse.ArgumentParser(description='Open Comm Control with a one-use demo link.')
parser.add_argument('--live',action='store_true',help='Open the live-call panel instead of the workspace.')
parser.add_argument('--link',action='store_true',help='Print a temporary, one-use link for opening in another browser.')
args=parser.parse_args()
p=Path(__file__).resolve().parents[1]/'.data/run.json'
if not p.exists():raise SystemExit('Start scripts/start.sh first.')
token=json.loads(p.read_text())['operator_token']
request=Request('http://127.0.0.1:8765/api/operator/launch',data=b'{}',headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'},method='POST')
try:
 with urlopen(request,timeout=10) as response:link='http://127.0.0.1:8765'+json.load(response)['url']
except URLError:raise SystemExit('Could not open the demo. Start or restart scripts/start.sh, then try again.')
if not args.live:
 parts=urlsplit(link);query=urlencode([(k,v) for k,v in parse_qsl(parts.query) if k!='live']);link=urlunsplit((parts.scheme,parts.netloc,parts.path,query,parts.fragment))
if args.link:print(link)
else:
 webbrowser.open(link)
 print('Opened Comm Control. This browser can reopen the demo for eight hours.')

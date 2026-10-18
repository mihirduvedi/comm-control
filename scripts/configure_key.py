#!/usr/bin/env python3
"""Save a user-provided key without echoing it or writing it to shell history."""
import getpass
import os
from pathlib import Path
root=Path(__file__).resolve().parents[1]
print('Use a Groq account on the Free tier. Do not add a payment method or upgrade.')
answer=input('Confirm this key belongs to a Free-tier account (yes/no): ').strip().lower()
if answer!='yes':
 print('No changes made. Keep the account on Free tier before configuring the app.');raise SystemExit(1)
key=getpass.getpass('Paste your Groq API key (hidden), then press Return: ').strip()
if not key.startswith('gsk_') or len(key)<20:
 print('That does not look like a Groq key. No changes made.');raise SystemExit(1)
p=root/'.env'
lines=p.read_text().splitlines() if p.exists() else []
lines=[l for l in lines if not l.startswith(('GROQ_API_KEY=','COMM_FREE_TIER_CONFIRMED='))]
lines+=['GROQ_API_KEY='+key,'COMM_FREE_TIER_CONFIRMED=yes']
fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
with os.fdopen(fd,'w') as f:f.write('\n'.join(lines)+'\n')
os.chmod(p,0o600)
print('Key saved privately in .env. The application will detect it automatically. No model downloaded and no paid service provisioned.')

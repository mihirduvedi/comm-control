"""One-use local launch links and revocable, expiring browser sessions.

Only hashes are stored. Neither link redemption nor the session-status response
returns the durable operator capability to browser JavaScript.
"""
import hashlib
import secrets
import time

from .domain import OPERATOR

COOKIE = 'comm_operator_session'
LINK_SECONDS = 30 * 60
SESSION_SECONDS = 8 * 60 * 60


class BrowserAccess:
 def __init__(self, domain):
  self.domain = domain
  self.store = domain.store
  self.store.db.executescript('''
   CREATE TABLE IF NOT EXISTS browser_access (
    hash TEXT PRIMARY KEY, kind TEXT NOT NULL, expires REAL NOT NULL);
  ''')

 def digest(self, kind, value):
  if not isinstance(value, str) or len(value) > 150:
   return ''
  return hashlib.sha256((kind + ':' + value).encode()).hexdigest()

 def issue_link(self):
  ticket = secrets.token_urlsafe(32)
  stamp = time.time()
  with self.store.transaction():
   self.store.db.execute('DELETE FROM browser_access WHERE expires<=?', (stamp,))
   count = self.store.db.execute("SELECT count(*) FROM browser_access WHERE kind='link'").fetchone()[0]
   if count >= 25:
    raise OverflowError('There are already 25 unused demo links. Use one or wait for it to expire.')
   self.store.db.execute('INSERT INTO browser_access VALUES(?,?,?)', (self.digest('link', ticket), 'link', stamp + LINK_SECONDS))
  return ticket

 def exchange(self, ticket):
  stamp = time.time()
  with self.store.transaction():
   row = self.store.db.execute("SELECT * FROM browser_access WHERE hash=? AND kind='link' AND expires>?", (self.digest('link', ticket), stamp)).fetchone()
   if not row:
    raise PermissionError('This demo link expired or was already used. Open a fresh link with the local launcher.')
   self.store.db.execute('DELETE FROM browser_access WHERE hash=?', (row['hash'],))
   self.store.db.execute('DELETE FROM browser_access WHERE expires<=?', (stamp,))
   # Bound retained sessions without revoking an active browser silently.
   count = self.store.db.execute("SELECT count(*) FROM browser_access WHERE kind='session'").fetchone()[0]
   if count >= 100:
    raise OverflowError('Too many demo browsers are connected. Wait for an existing session to expire.')
   session = secrets.token_urlsafe(32)
   self.store.db.execute('INSERT INTO browser_access VALUES(?,?,?)', (self.digest('session', session), 'session', stamp + SESSION_SECONDS))
  return session

 def cookie_actor(self, request):
  cookie = request.cookies.get(COOKIE, '')
  with self.store.lock:
   row = self.store.db.execute("SELECT 1 FROM browser_access WHERE hash=? AND kind='session' AND expires>?", (self.digest('session', cookie), time.time())).fetchone()
  if not cookie or not row:
   raise PermissionError('Open a fresh demo link with the local launcher.')
  return {'id': OPERATOR, 'role': 'operator'}

 def same_origin(self, request):
  # Ports matter. Another localhost service is not this application's origin.
  expected = 'http://' + request.headers.get('host', '')
  if request.headers.get('origin') != expected or request.headers.get('sec-fetch-site') not in [None, 'same-origin']:
   raise PermissionError('Open this action from the Comm Control demo page.')

 def actor(self, request):
  authorization = request.headers.get('authorization')
  if authorization is not None:
   # An explicit field/invalid bearer never falls back to operator cookies.
   return self.domain.actor(authorization.removeprefix('Bearer '))
  actor = self.cookie_actor(request)
  if request.method not in ['GET', 'HEAD', 'OPTIONS']:
   self.same_origin(request)
  return actor

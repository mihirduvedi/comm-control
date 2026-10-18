"""Persistent, fail-closed provider-call limits for the optional public demo."""
from contextvars import ContextVar
from dataclasses import dataclass
import sqlite3
import threading
import time
from pathlib import Path

visitor = ContextVar('comm_public_visitor', default=None)
active_budget = None


class DemoLimit(RuntimeError):
 def __init__(self,message,retry_after=60):
  super().__init__(message);self.retry_after=max(1,int(retry_after))


@dataclass(frozen=True)
class Limits:
 per_minute:int=8
 per_hour:int=60
 per_day:int=100
 lifetime:int=150
 visitor_hour:int=15
 visitor_day:int=30
 enabled_seconds:int=86400


class DemoBudget:
 def __init__(self,path,limits=None,clock=time.time):
  self.limits=limits or Limits();self.clock=clock;self.lock=threading.RLock()
  Path(path).parent.mkdir(parents=True,exist_ok=True)
  self.db=sqlite3.connect(str(path),check_same_thread=False,isolation_level=None)
  self.db.execute('PRAGMA busy_timeout=5000')
  self.db.executescript('CREATE TABLE IF NOT EXISTS calls(at REAL NOT NULL, visitor TEXT NOT NULL);CREATE INDEX IF NOT EXISTS calls_at ON calls(at);CREATE TABLE IF NOT EXISTS state(id INTEGER PRIMARY KEY, enabled_at REAL NOT NULL);')
  self.db.execute('INSERT OR IGNORE INTO state VALUES(1,?)',(clock(),))

 def _check(self,who,stamp):
  if not who:raise DemoLimit('Public voice processing needs a visitor identity. Please reopen the demo.')
  enabled=self.db.execute('SELECT enabled_at FROM state WHERE id=1').fetchone()[0]
  if stamp>=enabled+self.limits.enabled_seconds:raise DemoLimit('Public voice access has expired. The owner must re-enable it; sample incidents still work.',86400)
  checks=[(self.limits.lifetime,0,None,'The shared voice demo budget is used up. The owner must re-enable it; sample incidents still work.',86400),
   (self.limits.per_minute,60,None,'The shared voice demo is busy. Wait a minute, then retry.',60),
   (self.limits.per_hour,3600,None,'The shared hourly voice limit is reached. Try again later; sample incidents still work.',3600),
   (self.limits.per_day,86400,None,'The shared daily voice limit is reached. Sample incidents still work.',86400),
   (self.limits.visitor_hour,3600,who,'You have reached 15 model calls this hour. A voice report can use several calls. Try again later.',3600),
   (self.limits.visitor_day,86400,who,'You have reached the daily voice allowance. Sample incidents still work.',86400)]
  for limit,window,person,message,retry in checks:
   sql='SELECT count(*) FROM calls WHERE at>?';args=[stamp-window if window else -1]
   if person:sql+=' AND visitor=?';args.append(person)
   if self.db.execute(sql,args).fetchone()[0]>=limit:raise DemoLimit(message,retry)

 def check(self,who):
  with self.lock:self._check(who,self.clock())

 def reserve(self,who):
  # BEGIN IMMEDIATE also serializes reservations across processes/restarts.
  with self.lock:
   self.db.execute('BEGIN IMMEDIATE')
   try:
    stamp=self.clock();self._check(who,stamp)
    self.db.execute('INSERT INTO calls VALUES(?,?)',(stamp,who));self.db.execute('COMMIT')
   except BaseException:self.db.execute('ROLLBACK');raise

 def status(self,who):
  with self.lock:
   stamp=self.clock();enabled=self.db.execute('SELECT enabled_at FROM state WHERE id=1').fetchone()[0]
   total=self.db.execute('SELECT count(*) FROM calls').fetchone()[0]
   used=self.db.execute('SELECT count(*) FROM calls WHERE visitor=? AND at>?',(who,stamp-3600)).fetchone()[0]
   try:self._check(who,stamp);available=True;message='Voice demo available'
   except DemoLimit as error:available=False;message=str(error)
   return {'public_demo':True,'voice_enabled':available,'message':message,'visitor_hour_remaining':max(0,self.limits.visitor_hour-used),'visitor_hour_limit':self.limits.visitor_hour,'global_hour_limit':self.limits.per_hour,'global_day_limit':self.limits.per_day,'total_limit':self.limits.lifetime,'total_remaining':max(0,self.limits.lifetime-total),'expires_at':enabled+self.limits.enabled_seconds,'max_recording_seconds':30}

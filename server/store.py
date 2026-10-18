"""Single-host transactional document store and immutable event journal."""
import json
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone


def uid(): return str(uuid4())
def now(): return datetime.now(timezone.utc).isoformat()
def dump(v): return json.dumps(v, ensure_ascii=False, separators=(',', ':'), sort_keys=True)


class Conflict(Exception): pass


class Store:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path), check_same_thread=False, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.lock = threading.RLock()
        self.db.executescript('''
          PRAGMA journal_mode=WAL;
          PRAGMA foreign_keys=ON;
          CREATE TABLE IF NOT EXISTS objects (
            id TEXT NOT NULL, kind TEXT NOT NULL, scope TEXT NOT NULL,
            version INTEGER NOT NULL, data TEXT NOT NULL, PRIMARY KEY(kind,id));
          CREATE INDEX IF NOT EXISTS objects_scope ON objects(kind,scope);
          CREATE TABLE IF NOT EXISTS events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT, scope TEXT NOT NULL,
            aggregate_id TEXT NOT NULL, type TEXT NOT NULL, at TEXT NOT NULL, data TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS idempotency (
            scope TEXT, key TEXT, hash TEXT, result TEXT, PRIMARY KEY(scope,key));
          PRAGMA user_version=1;
        ''')

        # v2 permits message/report projections with the same correlation ID.
        columns={r['name']:r['pk'] for r in self.db.execute('PRAGMA table_info(objects)')}
        if not columns.get('kind'):
            self.db.executescript('ALTER TABLE objects RENAME TO objects_v1; CREATE TABLE objects (id TEXT NOT NULL,kind TEXT NOT NULL,scope TEXT NOT NULL,version INTEGER NOT NULL,data TEXT NOT NULL,PRIMARY KEY(kind,id)); INSERT INTO objects SELECT * FROM objects_v1; DROP TABLE objects_v1; CREATE INDEX IF NOT EXISTS objects_scope ON objects(kind,scope); PRAGMA user_version=2;')

    @contextmanager
    def transaction(self):
        with self.lock:
            self.db.execute('BEGIN IMMEDIATE')
            try:
                yield
                self.db.execute('COMMIT')
            except BaseException:
                self.db.execute('ROLLBACK')
                raise

    def get(self, id, kind=None):
        with self.lock:
            row = self.db.execute('SELECT * FROM objects WHERE id=? AND kind=?', (id,kind)).fetchone() if kind else self.db.execute("SELECT * FROM objects WHERE id=? ORDER BY CASE kind WHEN 'message' THEN 0 ELSE 1 END LIMIT 1", (id,)).fetchone()
            if not row or (kind and row['kind'] != kind): return None
            return json.loads(row['data'])

    def list(self, kind, scope=None):
        with self.lock:
            if scope is None: rows=self.db.execute('SELECT data FROM objects WHERE kind=? ORDER BY rowid', (kind,)).fetchall()
            else: rows=self.db.execute('SELECT data FROM objects WHERE kind=? AND scope=? ORDER BY rowid', (kind,scope)).fetchall()
            return [json.loads(r[0]) for r in rows]

    def put(self, kind, scope, obj, expected=None, event=None):
        # Caller owns transaction for coordinated changes. SQLite autocommit is used only at initialization.
        old=self.get(obj['id'],kind)
        if expected is not None and (not old or old['version'] != expected): raise Conflict('This item changed. Reload and review the current revision.')
        obj={**obj, 'version': (old.get('version',0) if old else 0)+1}
        self.db.execute('INSERT INTO objects VALUES (?,?,?,?,?) ON CONFLICT(kind,id) DO UPDATE SET version=excluded.version,data=excluded.data',
                        (obj['id'],kind,scope,obj['version'],dump(obj)))
        if event: self.event(scope,obj['id'],event,{'version':obj['version']})
        return obj

    def event(self, scope, id, type, data):
        self.db.execute('INSERT INTO events(scope,aggregate_id,type,at,data) VALUES(?,?,?,?,?)',(scope,id,type,now(),dump(data)))

    def events(self, after=0, scope=None, limit=100):
        with self.lock:
            if scope: rows=self.db.execute('SELECT * FROM events WHERE event_id>? AND scope=? ORDER BY event_id LIMIT ?', (after,scope,limit)).fetchall()
            else: rows=self.db.execute('SELECT * FROM events WHERE event_id>? ORDER BY event_id LIMIT ?', (after,limit)).fetchall()
            return [{**dict(r),'data':json.loads(r['data'])} for r in rows]

    def last_event(self):
        with self.lock: return self.db.execute('SELECT coalesce(max(event_id),0) FROM events').fetchone()[0]

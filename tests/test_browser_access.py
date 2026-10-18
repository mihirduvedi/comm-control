import time

import pytest
from fastapi.testclient import TestClient

from server.browser_access import COOKIE, LINK_SECONDS, SESSION_SECONDS
from server.main import create_app

ORIGIN = {'Origin': 'http://127.0.0.1:8765'}


@pytest.fixture
def env(tmp_path):
 app = create_app(tmp_path, workers=False)
 with TestClient(app, base_url='http://127.0.0.1:8765') as client:
  yield client, app.state.domain, tmp_path


def issue(client, domain):
 response = client.post('/api/operator/launch', headers={'Authorization': 'Bearer ' + domain.secrets['operator_token']})
 assert response.status_code == 200
 assert response.json()['expires_in'] == LINK_SECONDS
 return response.json()['url'].split('#launch=')[1]


def redeem(client, ticket, headers=None):
 return client.post('/api/operator/launch/exchange', json={'ticket': ticket}, headers=ORIGIN if headers is None else headers)


def test_launch_requires_operator_and_does_not_return_durable_token(env):
 c, d, _ = env
 assert c.post('/api/operator/launch').status_code == 403
 session = d.create_session('Private caller')
 assert c.post('/api/operator/launch', headers={'Authorization': 'Bearer ' + session['token']}).status_code == 403
 ticket = issue(c, d)
 assert ticket != d.secrets['operator_token']
 assert d.secrets['operator_token'] not in ticket
 row = d.store.db.execute("SELECT * FROM browser_access WHERE kind='link'").fetchone()
 assert ticket not in str(dict(row))


def test_one_use_exchange_and_cookie_allow_new_tabs_without_bearer(env):
 c, d, _ = env
 ticket = issue(c, d)
 response = redeem(c, ticket)
 assert response.status_code == 200 and response.json() == {'authenticated': True}
 cookie = response.headers['set-cookie']
 assert 'HttpOnly' in cookie and 'SameSite=strict' in cookie and f'Max-Age={SESSION_SECONDS}' in cookie
 assert d.secrets['operator_token'] not in cookie
 assert c.get('/api/operator/session').json() == {'authenticated': True}
 assert c.get('/api/control/snapshot').status_code == 200
 assert redeem(c, ticket).status_code == 403
 assert c.get('/control?live=1').status_code == 200
 assert c.get('/control').headers['x-frame-options'] == 'DENY'


def test_cookie_mutations_require_exact_origin_bearer_rules_unchanged(env):
 c, d, _ = env
 assert redeem(c, issue(c, d)).status_code == 200
 body = {'name': 'Cookie-origin check'}
 headers = {'Idempotency-Key': 'browser-session-check'}
 assert c.post('/api/sessions', json=body, headers=headers).status_code == 403
 assert c.post('/api/sessions', json=body, headers=headers | {'Origin': 'http://localhost:5173'}).status_code == 403
 assert c.post('/api/sessions', json=body, headers=headers | ORIGIN).status_code == 200
 assert c.get('/api/control/snapshot', headers={'Authorization': 'Bearer invalid'}).status_code == 403


def test_private_field_role_is_not_promoted_by_operator_cookie(env):
 c, d, _ = env
 session = d.create_session('Private caller')
 assert redeem(c, issue(c, d)).status_code == 200
 field = {'Authorization': 'Bearer ' + session['token']}
 assert c.get('/api/control/snapshot', headers=field).status_code == 403
 assert c.get('/api/field/snapshot', headers=field).status_code == 200
 assert c.get('/api/field/snapshot').status_code == 403


@pytest.mark.parametrize('headers', [{}, {'Origin': 'https://untrusted.example'}, {'Origin': 'http://localhost:5173'}, ORIGIN | {'Sec-Fetch-Site': 'cross-site'}])
def test_exchange_rejects_missing_cross_site_and_other_port_origins(env, headers):
 c, d, _ = env
 ticket = issue(c, d)
 assert redeem(c, ticket, headers).status_code == 403
 # A rejected request never consumes the legitimate link.
 assert redeem(c, ticket).status_code == 200


def test_expired_links_and_sessions_are_rejected(env):
 c, d, _ = env
 ticket = issue(c, d)
 d.store.db.execute("UPDATE browser_access SET expires=? WHERE kind='link'", (time.time() - 1,))
 assert redeem(c, ticket).status_code == 403
 assert redeem(c, issue(c, d)).status_code == 200
 d.store.db.execute("UPDATE browser_access SET expires=? WHERE kind='session'", (time.time() - 1,))
 assert c.get('/api/control/snapshot').status_code == 403


def test_session_survives_restart_without_exposing_auth_in_export(env):
 c, d, path = env
 ticket = issue(c, d)
 assert redeem(c, ticket).status_code == 200
 cookie = c.cookies.get(COOKIE)
 exported = c.get('/api/export').text
 assert cookie not in exported and ticket not in exported
 with TestClient(create_app(path, workers=False), base_url='http://127.0.0.1:8765') as fresh:
  fresh.cookies.set(COOKIE, cookie)
  assert fresh.get('/api/operator/session').status_code == 200
  assert fresh.get('/api/control/snapshot').status_code == 200


def test_cookie_websocket_uses_same_session_and_enforces_origin(env):
 c, d, _ = env
 assert redeem(c, issue(c, d)).status_code == 200
 with c.websocket_connect('ws://127.0.0.1:8765/api/live', headers=ORIGIN) as ws:
  ws.send_json({'token': '', 'after': 0})
  assert 'last_event_id' in ws.receive_json()


def test_exchange_requires_json_and_unknown_links_do_not_authorize(env):
 c, d, _ = env
 ticket = issue(c, d)
 assert c.post('/api/operator/launch/exchange', data={'ticket': ticket}, headers=ORIGIN).status_code == 422
 assert redeem(c, 'unknown').status_code == 403
 assert redeem(c, None).status_code == 403
 assert c.get('/api/control/snapshot').status_code == 403

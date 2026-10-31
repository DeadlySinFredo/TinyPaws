"""Twitch EventSub (WebSocket) for events IRC can't see: Hype Train, follows.

Login: OAuth Device Code flow with the user's own public Client ID — the user
confirms a code on twitch.tv, TinyPaws never sees a password. Tokens live only
in the desktop secret store (Secret Service via secret-tool), never in files.
All networking is async on the Qt event loop.
"""
import json
import re
import shutil
import subprocess
import sys

from PySide6.QtCore import QByteArray, QObject, QTimer, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWebSockets import QWebSocket

ID = 'https://id.twitch.tv/oauth2/'
HELIX = 'https://api.twitch.tv/helix/'
WS_URL = 'wss://eventsub.wss.twitch.tv/ws'
SCOPES = 'channel:read:hype_train moderator:read:followers channel:read:subscriptions bits:read'
CLIENT_ID_RE = re.compile(r'^[a-z0-9]{20,40}$')
# (type, version, condition-builder)
SUBSCRIPTIONS = [
    ('channel.hype_train.begin', '2', lambda u: {'broadcaster_user_id': u}),
    ('channel.hype_train.progress', '2', lambda u: {'broadcaster_user_id': u}),
    ('channel.hype_train.end', '2', lambda u: {'broadcaster_user_id': u}),
    ('channel.follow', '2', lambda u: {'broadcaster_user_id': u, 'moderator_user_id': u}),
    ('channel.subscribe', '1', lambda u: {'broadcaster_user_id': u}),
    ('channel.subscription.gift', '1', lambda u: {'broadcaster_user_id': u}),
    ('channel.cheer', '1', lambda u: {'broadcaster_user_id': u}),
    ('channel.raid', '1', lambda u: {'to_broadcaster_user_id': u}),
]


def valid_client_id(cid):
    return bool(CLIENT_ID_RE.match(cid or ''))


def map_notification(sub_type, ev, state):
    """EventSub notification -> unified TinyPaws events. state: dict kept across calls (hype level)."""
    name = lambda k='user_name': str(ev.get(k) or ev.get('user_login') or '')[:25]  # noqa: E731
    if sub_type == 'channel.hype_train.begin':
        state['level'] = int(ev.get('level', 1) or 1)
        names = [str(c.get('user_name', ''))[:20] for c in ev.get('top_contributions') or [] if c.get('user_name')]
        return [{'type': 'hype_train', 'level': state['level'], 'names': names}]
    if sub_type == 'channel.hype_train.progress':
        lvl = int(ev.get('level', 1) or 1)
        if lvl > state.get('level', 1):
            state['level'] = lvl
            return [{'type': 'hype_level', 'level': lvl}]
        return []
    if sub_type == 'channel.hype_train.end':
        state.pop('level', None)
        return [{'type': 'hype_end', 'level': int(ev.get('level', 1) or 1)}]
    if sub_type == 'channel.follow':
        return [{'type': 'follow', 'user': name()}]
    if sub_type == 'channel.subscribe':
        return [] if ev.get('is_gift') else [{'type': 'sub', 'user': name()}]  # gifts arrive as .gift
    if sub_type == 'channel.subscription.gift':
        return [{'type': 'gift_sub', 'user': 'Anonym' if ev.get('is_anonymous') else name()}]
    if sub_type == 'channel.cheer':
        return [{'type': 'bits', 'user': 'Anonym' if ev.get('is_anonymous') else name(), 'amount': ev.get('bits', 0)}]
    if sub_type == 'channel.raid':
        return [{'type': 'raid', 'user': name('from_broadcaster_user_name')}]
    return []


# ---------------------------------------------------------------- token store
_SECRET = ['service', 'tinypaws', 'account', 'twitch']


def load_token():
    if not shutil.which('secret-tool'):
        return None
    try:
        out = subprocess.run(['secret-tool', 'lookup', *_SECRET], capture_output=True, text=True, timeout=10)
        return json.loads(out.stdout) if out.returncode == 0 and out.stdout.strip() else None
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None


def save_token(tok):
    """Store in the secret service; without one the token is kept in memory only (re-login next start)."""
    if not shutil.which('secret-tool'):
        return False
    try:
        return subprocess.run(['secret-tool', 'store', '--label=TinyPaws Twitch', *_SECRET],
                              input=json.dumps(tok), text=True, timeout=10).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def clear_token():
    if shutil.which('secret-tool'):
        subprocess.run(['secret-tool', 'clear', *_SECRET], timeout=10)


# ---------------------------------------------------------------- client
class TwitchEventSub(QObject):
    code = Signal(str, str)      # user_code, verification_uri  -> show to the user
    status = Signal(str)         # human-readable state for UI

    def __init__(self, client_id):
        super().__init__()
        self.cid, self.net = client_id, QNetworkAccessManager(self)
        self.events, self.state, self.tok, self.user_id, self.user_login = [], {}, None, None, None
        self.ws = QWebSocket()
        self.ws.textMessageReceived.connect(self._msg)
        self.ws.disconnected.connect(self._dropped)
        self.alive = QTimer(self)  # Twitch sends keepalives; silence -> reconnect
        self.alive.setSingleShot(True)
        self.alive.timeout.connect(self._reconnect)
        self.backoff, self.closing = 1, False

    # -- http helpers
    def _req(self, method, url, cb, form=None, body=None, auth=True):
        r = QNetworkRequest(QUrl(url))
        if auth and self.tok:
            r.setRawHeader(b'Authorization', ('Bearer ' + self.tok['access_token']).encode())
            r.setRawHeader(b'Client-Id', self.cid.encode())
        if form is not None:
            r.setHeader(QNetworkRequest.ContentTypeHeader, 'application/x-www-form-urlencoded')
            data = QByteArray('&'.join('%s=%s' % (k, QUrl.toPercentEncoding(str(v)).data().decode())
                                       for k, v in form.items()).encode())
        elif body is not None:
            r.setHeader(QNetworkRequest.ContentTypeHeader, 'application/json')
            data = QByteArray(json.dumps(body).encode())
        else:
            data = None
        reply = self.net.get(r) if method == 'GET' else self.net.post(r, data)

        def done():
            code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) or 0
            try:
                js = json.loads(bytes(reply.readAll()).decode() or '{}')
            except ValueError:
                js = {}
            reply.deleteLater()
            cb(code, js)
        reply.finished.connect(done)

    # -- login
    def start(self):
        """Use a stored token if any; otherwise wait for login()."""
        self.tok = load_token()
        if self.tok:
            self._validate()
        else:
            self.status.emit('nicht verbunden')

    def login(self):
        self._req('POST', ID + 'device', self._device, form={'client_id': self.cid, 'scopes': SCOPES}, auth=False)

    def logout(self):
        clear_token()
        self.tok = None
        self.closing = True
        self.ws.close()
        self.status.emit('abgemeldet')

    def _device(self, code, js):
        if code != 200 or 'device_code' not in js:
            self.status.emit('Login fehlgeschlagen (%s): Client-ID prüfen' % code)
            return
        self.device = js
        self.code.emit(js['user_code'], js['verification_uri'])
        self.poll_left = int(js.get('expires_in', 1800))
        QTimer.singleShot(int(js.get('interval', 5)) * 1000, self._poll)

    def _poll(self):
        self._req('POST', ID + 'token', self._polled, auth=False, form={
            'client_id': self.cid, 'scopes': SCOPES, 'device_code': self.device['device_code'],
            'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'})

    def _polled(self, code, js):
        if code == 200 and 'access_token' in js:
            self._got_token(js)
            return
        iv = int(self.device.get('interval', 5))
        self.poll_left -= iv
        if js.get('message') == 'authorization_pending' and self.poll_left > 0:
            QTimer.singleShot(iv * 1000, self._poll)
        else:
            self.status.emit('Login abgebrochen oder abgelaufen')

    def _got_token(self, js):
        self.tok = {'access_token': js['access_token'], 'refresh_token': js.get('refresh_token', '')}
        if not save_token(self.tok):
            print('tinypaws: no secret store, Twitch token kept in memory only', file=sys.stderr)
        self._validate()

    def _refresh(self):
        if not self.tok or not self.tok.get('refresh_token'):
            self.status.emit('Login abgelaufen – bitte neu verbinden')
            return
        self._req('POST', ID + 'token', self._refreshed, auth=False, form={
            'client_id': self.cid, 'grant_type': 'refresh_token', 'refresh_token': self.tok['refresh_token']})

    def _refreshed(self, code, js):
        if code == 200 and 'access_token' in js:
            self._got_token(js)
        else:
            clear_token()
            self.tok = None
            self.status.emit('Login abgelaufen – bitte neu verbinden')

    def _validate(self):
        r = QNetworkRequest(QUrl(ID + 'validate'))
        r.setRawHeader(b'Authorization', ('OAuth ' + self.tok['access_token']).encode())
        reply = self.net.get(r)

        def done():
            code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) or 0
            try:
                js = json.loads(bytes(reply.readAll()).decode() or '{}')
            except ValueError:
                js = {}
            reply.deleteLater()
            if code == 200 and js.get('user_id'):
                self.user_id, self.user_login = js['user_id'], js.get('login', '')
                self.status.emit('verbunden als %s' % self.user_login)
                self.closing = False
                self.ws.open(QUrl(WS_URL))
            elif code == 401:
                self._refresh()
            else:
                self.status.emit('Twitch nicht erreichbar (%s)' % code)
                QTimer.singleShot(30000, self._validate)
        reply.finished.connect(done)

    # -- websocket
    def _msg(self, text):
        try:
            m = json.loads(text)
        except ValueError:
            return
        kind = m.get('metadata', {}).get('message_type')
        p = m.get('payload', {})
        if kind == 'session_welcome':
            sess = p.get('session', {})
            self.alive.start((int(sess.get('keepalive_timeout_seconds') or 10) + 5) * 1000)
            self.backoff = 1
            if not getattr(self, 'migrating', False):
                for typ, ver, cond in SUBSCRIPTIONS:
                    self._subscribe(typ, ver, cond(self.user_id), sess['id'])
            self.migrating = False
        elif kind == 'session_keepalive':
            self.alive.start()
        elif kind == 'notification':
            self.alive.start()
            self.events.extend(map_notification(p.get('subscription', {}).get('type'), p.get('event', {}), self.state))
            del self.events[:-50]  # bounded
        elif kind == 'session_reconnect':
            url = p.get('session', {}).get('reconnect_url', '')
            if url.startswith('wss://eventsub.wss.twitch.tv/'):  # only follow Twitch's own host
                self.migrating, self.closing = True, True
                self.ws.close()
                self.closing = False
                self.ws.open(QUrl(url))

    def _subscribe(self, typ, ver, cond, session_id):
        def done(code, js):
            if code == 202:
                return
            if ver == '2' and typ.startswith('channel.hype_train'):
                self._subscribe(typ, '1', cond, session_id)  # older API fallback
            else:
                print('tinypaws: EventSub %s failed (%s): %s' % (typ, code, js.get('message', '')), file=sys.stderr)
        self._req('POST', HELIX + 'eventsub/subscriptions', done, body={
            'type': typ, 'version': ver, 'condition': cond,
            'transport': {'method': 'websocket', 'session_id': session_id}})

    def _dropped(self):
        if not self.closing:
            self._reconnect()

    def _reconnect(self):
        if self.closing or not self.tok:
            return
        self.status.emit('Verbindung verloren, neuer Versuch in %ds' % self.backoff)
        self.closing = True
        self.ws.abort()
        self.closing = False
        QTimer.singleShot(self.backoff * 1000, self._validate)
        self.backoff = min(self.backoff * 2, 120)

    def close(self):
        self.closing = True
        self.alive.stop()
        self.ws.close()

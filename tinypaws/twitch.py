"""Twitch chat connector: anonymous, read-only IRC (no token needed).

Delivers unified events (see brain.handle_event) for chat, sub, gift_sub, bits, raid.
Hype Train needs EventSub + OAuth -> not available anonymously (see ROADMAP).
"""
import queue
import random
import re
import socket
import ssl
import threading
import time

HOST, PORT = 'irc.chat.twitch.tv', 6697
CHANNEL_RE = re.compile(r'^[a-z0-9_]{3,25}$')
_UNESCAPE = {'\\s': ' ', '\\:': ';', '\\\\': '\\', '\\r': '\r', '\\n': '\n'}


def valid_channel(name):
    return bool(CHANNEL_RE.match(name.strip().lstrip('#').lower()))


def _tags(raw):
    out = {}
    for kv in raw.split(';'):
        k, _, v = kv.partition('=')
        out[k] = re.sub(r'\\[s:\\rn]', lambda m: _UNESCAPE[m.group()], v)
    return out


def parse(line):
    """One IRC line -> event dict or None."""
    tags = {}
    if line.startswith('@'):
        raw, _, line = line.partition(' ')
        tags = _tags(raw[1:])
    prefix = ''
    if line.startswith(':'):
        prefix, _, line = line[1:].partition(' ')
    cmd, _, rest = line.partition(' ')
    text = rest.partition(' :')[2] if ' :' in rest else ''
    user = tags.get('display-name') or prefix.partition('!')[0]
    if cmd == 'PRIVMSG':
        if tags.get('bits', '').isdigit():
            return {'type': 'bits', 'user': user, 'text': text, 'amount': int(tags['bits'])}
        return {'type': 'chat', 'user': user, 'text': text}
    if cmd == 'USERNOTICE':
        mid = tags.get('msg-id', '')
        user = tags.get('msg-param-displayName') if mid == 'raid' else (tags.get('display-name') or tags.get('login', ''))
        kind = {'sub': 'sub', 'resub': 'sub', 'subgift': 'gift_sub', 'submysterygift': 'gift_sub',
                'raid': 'raid'}.get(mid)
        return {'type': kind, 'user': user or '', 'text': text} if kind else None
    return None


class TwitchChat:
    def __init__(self, channel, events=None):
        channel = channel.strip().lstrip('#').lower()
        if not valid_channel(channel):
            raise ValueError('invalid Twitch channel: %r' % channel)
        self.channel = channel
        self.events = events or queue.Queue(maxsize=200)
        self.status, self._stop, self._sock = 'connecting', threading.Event(), None
        threading.Thread(target=self._run, daemon=True).start()

    def _put(self, ev):
        try:
            self.events.put_nowait(ev)
        except queue.Full:
            pass  # chat flood: drop, the pet reacts only occasionally anyway

    def _run(self):
        backoff = 1
        while not self._stop.is_set():
            try:
                self._session()
                backoff = 1
            except OSError as e:
                self.status = 'error: %s' % e
            if self._stop.wait(backoff):
                break
            backoff = min(backoff * 2, 60)  # reconnect with exponential backoff

    def _session(self):
        raw = socket.create_connection((HOST, PORT), timeout=10)
        sock = self._sock = ssl.create_default_context().wrap_socket(raw, server_hostname=HOST)
        sock.settimeout(360)  # Twitch pings every ~5 min
        nick = 'justinfan%d' % random.randint(10000, 99999)
        sock.sendall(('CAP REQ :twitch.tv/tags twitch.tv/commands\r\nPASS SCHMOOPIIE\r\nNICK %s\r\n'
                      'JOIN #%s\r\n' % (nick, self.channel)).encode())
        buf = b''
        try:
            while not self._stop.is_set():
                data = sock.recv(4096)
                if not data:
                    raise ConnectionResetError('closed by server')
                buf += data
                *lines, buf = buf.split(b'\r\n')
                for b in lines:
                    line = b.decode('utf-8', 'replace')
                    if line.startswith('PING'):
                        sock.sendall(('PONG' + line[4:] + '\r\n').encode())
                    elif ' RECONNECT' in line:
                        raise ConnectionResetError('server asked to reconnect')
                    elif ' JOIN #' in line:
                        self.status = 'connected'
                    else:
                        ev = parse(line)
                        if ev:
                            self._put(ev)
        finally:
            sock.close()

    def close(self):
        self._stop.set()
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass

"""Store small secrets (the Twitch token) in the OS credential store – never in files or logs.

Linux: Secret Service via `secret-tool` (KWallet/GNOME Keyring). macOS: login keychain via `security`.
Windows: Credential Manager via advapi32 (ctypes). No backend -> nothing is stored (memory only).
"""
import json
import shutil
import subprocess
import sys

SERVICE = 'tinypaws'


def _linux(op, account, value=None):
    if not shutil.which('secret-tool'):
        return None
    attrs = ['service', SERVICE, 'account', account]
    if op == 'get':
        r = subprocess.run(['secret-tool', 'lookup', *attrs], capture_output=True, text=True, timeout=10)
        return r.stdout if r.returncode == 0 and r.stdout.strip() else None
    if op == 'set':
        return subprocess.run(['secret-tool', 'store', '--label=TinyPaws %s' % account, *attrs], input=value,
                              text=True, timeout=10).returncode == 0
    return subprocess.run(['secret-tool', 'clear', *attrs], timeout=10).returncode == 0


def _macos(op, account, value=None):
    if not shutil.which('security'):
        return None
    base = ['-s', SERVICE, '-a', account]
    if op == 'get':
        r = subprocess.run(['security', 'find-generic-password', *base, '-w'], capture_output=True, text=True, timeout=10)
        return r.stdout.rstrip('\n') if r.returncode == 0 and r.stdout.strip() else None
    if op == 'set':
        # shortcut: the value is passed as an argument (briefly visible to local `ps`); fine for a refreshable token
        return subprocess.run(['security', 'add-generic-password', '-U', *base, '-w', value],
                              capture_output=True, timeout=10).returncode == 0
    return subprocess.run(['security', 'delete-generic-password', *base], capture_output=True, timeout=10).returncode == 0


def _windows(op, account, value=None):
    import ctypes
    from ctypes import wintypes

    class CREDENTIAL(ctypes.Structure):
        _fields_ = [('Flags', wintypes.DWORD), ('Type', wintypes.DWORD), ('TargetName', wintypes.LPWSTR),
                    ('Comment', wintypes.LPWSTR), ('LastWritten', wintypes.FILETIME),
                    ('CredentialBlobSize', wintypes.DWORD), ('CredentialBlob', ctypes.POINTER(ctypes.c_ubyte)),
                    ('Persist', wintypes.DWORD), ('AttributeCount', wintypes.DWORD), ('Attributes', ctypes.c_void_p),
                    ('TargetAlias', wintypes.LPWSTR), ('UserName', wintypes.LPWSTR)]

    adv = ctypes.WinDLL('advapi32', use_last_error=True)
    target = '%s:%s' % (SERVICE, account)
    CRED_TYPE_GENERIC, CRED_PERSIST_LOCAL_MACHINE = 1, 2
    if op == 'get':
        p = ctypes.POINTER(CREDENTIAL)()
        if not adv.CredReadW(target, CRED_TYPE_GENERIC, 0, ctypes.byref(p)):
            return None
        try:
            c = p.contents
            return bytes(c.CredentialBlob[:c.CredentialBlobSize]).decode('utf-8')
        finally:
            adv.CredFree(p)
    if op == 'set':
        blob = value.encode('utf-8')
        buf = (ctypes.c_ubyte * len(blob)).from_buffer_copy(blob)
        c = CREDENTIAL(Type=CRED_TYPE_GENERIC, TargetName=target, CredentialBlobSize=len(blob),
                       CredentialBlob=ctypes.cast(buf, ctypes.POINTER(ctypes.c_ubyte)),
                       Persist=CRED_PERSIST_LOCAL_MACHINE, UserName=account)
        return bool(adv.CredWriteW(ctypes.byref(c), 0))
    return bool(adv.CredDeleteW(target, CRED_TYPE_GENERIC, 0))


def _backend():
    return {'win32': _windows, 'darwin': _macos}.get(sys.platform, _linux)


def get(account):
    try:
        return _backend()('get', account)
    except (OSError, subprocess.TimeoutExpired):
        return None


def put(account, value):
    """True if stored; False/None means it stays in memory only."""
    try:
        return bool(_backend()('set', account, value))
    except (OSError, subprocess.TimeoutExpired):
        return False


def delete(account):
    try:
        return bool(_backend()('delete', account))
    except (OSError, subprocess.TimeoutExpired):
        return False


def get_json(account):
    raw = get(account)
    try:
        return json.loads(raw) if raw else None
    except ValueError:
        return None


def put_json(account, obj):
    return put(account, json.dumps(obj))

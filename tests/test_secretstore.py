"""Token storage (issue #3): OS credential store per platform; login lifecycle without network."""
import os
import sys
import unittest
import uuid

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QCoreApplication  # noqa: E402

APP = QCoreApplication.instance() or QCoreApplication([])

from tinypaws import eventsub, secretstore  # noqa: E402

# the real round trip writes to the OS store: only on throw-away GitHub-hosted runners (or locally on
# request) – never on self-hosted runners, which are someone's real computer
LIVE = os.environ.get('RUNNER_ENVIRONMENT') == 'github-hosted' or os.environ.get('TINYPAWS_KEYRING_TEST') == '1'


@unittest.skipUnless(LIVE, 'set TINYPAWS_KEYRING_TEST=1 to touch the real credential store')
class RealStore(unittest.TestCase):
    def test_round_trip(self):
        acct = 'test-%s' % uuid.uuid4().hex[:8]
        if not secretstore.put_json(acct, {'access_token': 'a' * 30, 'refresh_token': 'r'}):
            if sys.platform.startswith('linux'):
                self.skipTest('no Secret Service on this machine')
            if sys.platform == 'darwin':
                self.skipTest('keychain locked on this runner')
            self.fail('Windows Credential Manager refused the write')
        try:
            self.assertEqual(secretstore.get_json(acct)['access_token'], 'a' * 30)
            self.assertTrue(secretstore.put_json(acct, {'access_token': 'b'}))  # overwrite
            self.assertEqual(secretstore.get_json(acct)['access_token'], 'b')
        finally:
            self.assertTrue(secretstore.delete(acct))
        self.assertIsNone(secretstore.get(acct))


class Lifecycle(unittest.TestCase):
    """Login/refresh/logout against an in-memory store and fake HTTP answers."""

    def setUp(self):
        self.store = {}
        self.orig = (secretstore.get, secretstore.put, secretstore.delete)
        secretstore.get = lambda a: self.store.get(a)
        secretstore.put = lambda a, v: self.store.__setitem__(a, v) or True
        secretstore.delete = lambda a: self.store.pop(a, None) is not None
        self.es = eventsub.TwitchEventSub('abcdefghij0123456789abcdefghij')
        self.status = []
        self.es.status.connect(self.status.append)
        self.validated = []
        self.es._validate = lambda: self.validated.append(self.es.tok['access_token'])

    def tearDown(self):
        secretstore.get, secretstore.put, secretstore.delete = self.orig
        self.es.close()

    def test_new_token_is_stored_not_logged(self):
        self.es._got_token({'access_token': 'tok1', 'refresh_token': 'ref1'})
        self.assertIn('tok1', self.store['twitch'])
        self.assertEqual(eventsub.load_token()['refresh_token'], 'ref1')
        self.assertFalse(any('tok1' in s for s in self.status))

    def test_refresh_success_and_revoked(self):
        self.es._got_token({'access_token': 'old', 'refresh_token': 'ref'})
        self.es._refreshed(200, {'access_token': 'new', 'refresh_token': 'ref2'})
        self.assertEqual(eventsub.load_token()['access_token'], 'new')
        self.assertEqual(self.validated[-1], 'new')
        self.es._refreshed(400, {'message': 'Invalid refresh token'})  # revoked on twitch.tv
        self.assertIsNone(self.es.tok)
        self.assertNotIn('twitch', self.store)
        self.assertIn('neu verbinden', self.status[-1])

    def test_logout_clears_store(self):
        self.es._got_token({'access_token': 't', 'refresh_token': 'r'})
        self.es.logout()
        self.assertNotIn('twitch', self.store)
        self.assertIsNone(self.es.tok)

    def test_device_flow_errors_are_reported(self):
        self.es._device(400, {'message': 'invalid client'})
        self.assertIn('Client-ID', self.status[-1])
        self.es.device = {'device_code': 'x', 'interval': 5}
        self.es.poll_left = 0
        self.es._polled(400, {'message': 'expired_token'})
        self.assertIn('abgelaufen', self.status[-1])


if __name__ == '__main__':
    unittest.main()

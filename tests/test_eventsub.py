import unittest

from tinypaws.eventsub import map_notification, valid_client_id


class Mapping(unittest.TestCase):
    def test_hype_train_lifecycle(self):
        st = {}
        ev = map_notification('channel.hype_train.begin', {
            'level': 2, 'top_contributions': [{'user_name': 'Keksi', 'type': 'bits', 'total': 500},
                                              {'user_name': 'Mausi', 'type': 'subscription', 'total': 1}]}, st)
        self.assertEqual(ev, [{'type': 'hype_train', 'level': 2, 'names': ['Keksi', 'Mausi']}])
        self.assertEqual(map_notification('channel.hype_train.progress', {'level': 2}, st), [])
        self.assertEqual(map_notification('channel.hype_train.progress', {'level': 3}, st),
                         [{'type': 'hype_level', 'level': 3}])
        self.assertEqual(map_notification('channel.hype_train.end', {'level': 4}, st),
                         [{'type': 'hype_end', 'level': 4}])
        self.assertEqual(st, {})

    def test_other_events(self):
        st = {}
        self.assertEqual(map_notification('channel.follow', {'user_name': 'Neu'}, st), [{'type': 'follow', 'user': 'Neu'}])
        self.assertEqual(map_notification('channel.subscribe', {'user_name': 'A', 'is_gift': True}, st), [])
        self.assertEqual(map_notification('channel.subscribe', {'user_name': 'A', 'is_gift': False}, st)[0]['type'], 'sub')
        self.assertEqual(map_notification('channel.subscription.gift', {'is_anonymous': True}, st)[0]['user'], 'Anonym')
        self.assertEqual(map_notification('channel.cheer', {'user_name': 'B', 'bits': 100}, st)[0]['type'], 'bits')
        self.assertEqual(map_notification('channel.raid', {'from_broadcaster_user_name': 'Raider'}, st),
                         [{'type': 'raid', 'user': 'Raider'}])
        self.assertEqual(map_notification('channel.unknown', {}, st), [])

    def test_client_id(self):
        self.assertTrue(valid_client_id('abcdefghij0123456789abcdefghij'))
        for bad in ('', 'short', 'UPPER_and spaces', 'x' * 50, None):
            self.assertFalse(valid_client_id(bad))


if __name__ == '__main__':
    unittest.main()

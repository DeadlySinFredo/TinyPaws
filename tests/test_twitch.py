import queue
import unittest

from tinypaws import twitch


class Parse(unittest.TestCase):
    def test_chat(self):
        ev = twitch.parse('@badge-info=;display-name=PixelFuchs92;color= :pixelfuchs92!pixelfuchs92@pixelfuchs92'
                          '.tmi.twitch.tv PRIVMSG #chan :Wo ist meine Pizza?')
        self.assertEqual(ev, {'type': 'chat', 'user': 'PixelFuchs92', 'text': 'Wo ist meine Pizza?'})

    def test_no_tags_and_colon_in_text(self):
        ev = twitch.parse(':bob!bob@bob.tmi.twitch.tv PRIVMSG #chan :a: b :c')
        self.assertEqual((ev['user'], ev['text']), ('bob', 'a: b :c'))

    def test_bits_sub_gift_raid(self):
        self.assertEqual(twitch.parse('@bits=100;display-name=A :a!a@a PRIVMSG #c :Cheer100')['type'], 'bits')
        self.assertEqual(twitch.parse('@msg-id=resub;display-name=B :tmi.twitch.tv USERNOTICE #c :hi')['type'], 'sub')
        self.assertEqual(twitch.parse('@msg-id=subgift;display-name=C :tmi.twitch.tv USERNOTICE #c')['type'], 'gift_sub')
        ev = twitch.parse('@msg-id=raid;msg-param-displayName=Raider\\sX;display-name=raiderx :tmi.twitch.tv USERNOTICE #c')
        self.assertEqual((ev['type'], ev['user']), ('raid', 'Raider X'))

    def test_ignored(self):
        for line in ('PING :tmi.twitch.tv', ':tmi.twitch.tv 001 justinfan1 :Welcome',
                     '@msg-id=announcement :tmi.twitch.tv USERNOTICE #c :x', ''):
            self.assertIsNone(twitch.parse(line))

    def test_channel_validation(self):
        self.assertTrue(twitch.valid_channel('#Some_Streamer'))
        for bad in ('', 'a', 'x y', 'evil\r\nPRIVMSG', 'a' * 30):
            self.assertFalse(twitch.valid_channel(bad))
        with self.assertRaises(ValueError):
            twitch.TwitchChat('bad name\r\nQUIT')

    def test_queue_bounded(self):
        q = queue.Queue(maxsize=2)
        c = twitch.TwitchChat.__new__(twitch.TwitchChat)
        c.events = q
        for _ in range(5):
            c._put({'type': 'chat'})
        self.assertEqual(q.qsize(), 2)


if __name__ == '__main__':
    unittest.main()

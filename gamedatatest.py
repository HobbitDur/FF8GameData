import unittest

from gamedata import GameData

class TestGameData(unittest.TestCase):

    def setUp(self):
        self.game_data = GameData()
        self.game_data.load_all()

    def test_sysfnt(self):
        ff8_str = "This {in}"
        ff8_list = self.game_data.translate_str_to_hex(ff8_str)
        ff8_hex = bytearray(ff8_list)
        self.assertEqual(len(ff8_hex), 6)
        self.assertEqual(ff8_hex, b'Xfgq \xe8')
        ff8_re_str = self.game_data.translate_hex_to_str(ff8_hex)
        self.assertEqual(ff8_re_str, ff8_str)

    def test_card_img(self):
        for el in self.game_data.card_data_json["card_type"]:
            self.assertNotEqual(el['img'], None)
        for el in self.game_data.card_data_json["card_info"]:
            self.assertNotEqual(el['img'], None)

if __name__ == '__main__':
    unittest.main()
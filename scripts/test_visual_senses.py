"""Regression checks for homographs that have different meanings across decks."""
import unittest
from pathlib import Path
from card_visuals import visual_lookup, select_visual

class VisualSenses(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.general, cls.senses = visual_lookup(Path(__file__).resolve().parents[1] / 'assets/card-visuals')

    def test_arrival_does_not_inherit_light(self):
        arrive = select_visual(self.general, self.senses, ['つく', 'つく', 'to arrive; reach'])
        light = select_visual(self.general, self.senses, ['つく', 'つく', '(something) turns on (〜が)'])
        self.assertNotEqual(arrive['image'], light['image'])
        self.assertIn('arriv', arrive['alt'])
        self.assertIn('turns on', light['alt'])

    def test_do_does_not_replace_decide_on(self):
        do = select_visual(self.general, self.senses, ['する', 'する', 'to do'])
        choose = select_visual(self.general, self.senses, ['する', 'する', 'to decide on (an item) (item に)'])
        self.assertNotEqual(do['image'], choose['image'])

    def test_unrelated_words_keep_catalog(self):
        for key, entry in self.general.items():
            self.assertEqual(select_visual(self.general, self.senses, [*key, '__unmatched_sense__']), entry)

    def test_override_sources_exist(self):
        root = Path(__file__).resolve().parents[1] / 'assets/card-visuals/images'
        for entry in self.senses.values():
            self.assertTrue((root / entry['image']).is_file())

if __name__ == '__main__': unittest.main()

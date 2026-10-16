import copy
import json
import unittest
from pathlib import Path
from tools.generate_keymap import generated,CODES
from diagnostics.model import EXPECTED


class KeymapTests(unittest.TestCase):
    def setUp(self):
        self.report=json.loads(Path('docs/verified-report.json').read_text())

    def test_generated_map_matches_measured_report(self):
        self.assertEqual(generated(self.report),Path('firmware/keymap.c').read_text())
        self.assertEqual(set(CODES),set(EXPECTED))
        self.assertEqual(len(set(CODES.values())),84)

    def test_unverified_or_crossed_keys_rejected(self):
        for mode in ('status','pair'):
            report=copy.deepcopy(self.report)
            if mode=='status': report['keys']['A']['status']='untested'
            else: report['keys']['A']['observed']=[[11,12]]
            with self.assertRaises(ValueError): generated(report)

    def test_simulation_cannot_generate_production_map(self):
        self.report['metadata']['mode']='simulation'
        with self.assertRaises(ValueError): generated(self.report)

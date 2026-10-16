import json
import tempfile
import unittest
from pathlib import Path
from diagnostics.model import Session, Guide, EXPECTED, ORDER, WIRING, parse_pairs
from diagnostics.mouse import MouseState


class MappingTests(unittest.TestCase):
    def session(self, key='Esc'):
        s=Session(); s.feed(set()); s.arm(key)
        return s

    def test_every_key_press_release(self):
        self.assertEqual(len(EXPECTED),84)
        self.assertEqual(set(ORDER),set(EXPECTED))
        self.assertEqual(len(set(EXPECTED.values())),84)
        for key,pair in EXPECTED.items():
            s=self.session(key)
            self.assertIsNone(s.feed({pair}))
            self.assertNotIn(key,s.results)
            self.assertEqual(s.feed(set()),(key,'pass'))

    def test_no_live_baseline_or_held_key_cannot_arm(self):
        s=Session()
        with self.assertRaises(ValueError): s.arm('Esc')
        s.feed({EXPECTED['A']})
        with self.assertRaises(ValueError): s.arm('Esc')

    def test_wrong_pair_is_mismatch(self):
        s=self.session(); s.feed({EXPECTED['A']})
        self.assertEqual(s.feed(set()),('Esc','mismatch'))

    def test_multiple_keys_never_pass_even_after_partial_release(self):
        s=self.session(); s.feed({EXPECTED['Esc'],EXPECTED['A']})
        s.feed({EXPECTED['Esc']})
        self.assertEqual(s.feed(set()),('Esc','ambiguous'))

    def test_pair_changes_without_release_are_ambiguous(self):
        s=self.session(); s.feed({EXPECTED['A']}); s.feed({EXPECTED['Esc']})
        self.assertEqual(s.feed(set()),('Esc','ambiguous'))

    def test_disconnect_cancels_pending_test(self):
        s=self.session(); s.feed({EXPECTED['Esc']}); s.cancel(); s.feed(set())
        self.assertFalse(s.results)

    def test_invalid_protocol_data(self):
        for value in (None,{},[[1,2]],[[11,11]],[[11,12,17]],[[True,12]],[['11',12]]):
            with self.assertRaises(ValueError): parse_pairs(value)
        self.assertEqual(parse_pairs([[34,29],[29,34]]),{(29,34)})

    def test_report_preserves_observed_and_untested(self):
        s=self.session(); s.feed({EXPECTED['A']}); s.feed(set())
        Path('build').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir='build') as directory:
            s.export(directory,{'mode':'simulation'})
            report=json.loads((Path(directory)/'report.json').read_text())
            self.assertEqual(report['keys']['Esc']['status'],'mismatch')
            self.assertEqual(report['keys']['Esc']['observed'],[list(EXPECTED['A'])])
            self.assertEqual(report['keys']['Fn']['status'],'untested')
            self.assertEqual(report['metadata']['mode'],'simulation')
            self.assertEqual(len(report['keys']),84)

    def test_document_and_firmware_agree_with_wiring(self):
        import re
        readme=Path('README.md').read_text(encoding='utf-8')
        rows=re.findall(r'\| [ABC]\d+ \| .*? \| (\d+) \| GP(\d+) \| \d+ \|',readme)
        self.assertEqual({int(a):int(b) for a,b in rows},WIRING)
        source=Path('main.c').read_text()
        arrays=[list(map(int,re.search(rf'{name}\[N\] = \{{(.*?)\}}',source)[1].split(','))) for name in ('fpc','gp')]
        self.assertEqual(dict(zip(*arrays)),WIRING)


class GuideTests(unittest.TestCase):
    def test_84_fast_keys_advance_without_timers(self):
        s=Session(); guide=Guide(s); guide.begin()
        result,key=guide.feed(set())
        self.assertEqual(key,ORDER[0])
        for index,key in enumerate(ORDER):
            self.assertEqual(s.target,key)
            guide.feed({EXPECTED[key]})
            result,next_key=guide.feed(set())
            self.assertEqual(result,(key,'pass'))
            self.assertEqual(next_key,ORDER[index+1] if index+1<len(ORDER) else None)
        self.assertEqual(len(s.results),84)

    def test_pending_advance_survives_held_key(self):
        s=Session(); guide=Guide(s); guide.begin()
        guide.feed({EXPECTED['A']})
        self.assertTrue(guide.pending)
        for _ in range(10): guide.feed({EXPECTED['A']})
        self.assertEqual(guide.feed(set())[1],'Esc')

    def test_pause_cancels_pending_advance(self):
        s=Session(); guide=Guide(s); guide.begin(); guide.cancel()
        self.assertIsNone(guide.feed(set())[1])

    def test_mismatch_does_not_silently_skip(self):
        s=Session(); guide=Guide(s); guide.begin(); guide.feed(set())
        guide.feed({EXPECTED['A']})
        result,key=guide.feed(set())
        self.assertEqual(result,('Esc','mismatch'))
        self.assertIsNone(key); self.assertFalse(guide.pending)


class MouseTests(unittest.TestCase):
    def test_movements_and_clicks_require_actual_events(self):
        mouse=MouseState()
        mouse.release('Left'); self.assertFalse(mouse.buttons)
        for position in [(50,50),(60,50),(40,50),(40,60),(40,40)]: mouse.move(*position)
        self.assertEqual(mouse.directions,{'Left','Right','Up','Down'})
        for button in ['Left','Middle','Right']:
            mouse.press(button)
            self.assertNotIn(button,mouse.buttons)
            mouse.release(button)
        self.assertEqual(mouse.buttons,{'Left','Middle','Right'})
        self.assertEqual(mouse.report()['t14_trackpoint'],'not connected')

    def test_pointer_reentry_does_not_count_a_jump(self):
        mouse=MouseState(); mouse.move(0,0); mouse.last=None; mouse.move(100,100)
        self.assertFalse(mouse.directions)

    def test_small_movements_accumulate(self):
        mouse=MouseState()
        for x in range(6): mouse.move(x,0)
        self.assertEqual(mouse.directions,{'Right'})


if __name__=='__main__': unittest.main()

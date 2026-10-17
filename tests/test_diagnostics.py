import json
import tempfile
import unittest
from pathlib import Path
from diagnostics.model import Session, Guide, EXPECTED, ORDER, WIRING, parse_pairs
from diagnostics.mouse import MouseState
EXPECTED_CONTACTS={c for pair in EXPECTED.values() for c in pair}


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

    def test_wiring_is_complete_and_unique(self):
        from diagnostics.model import FPC_WIRES, RIBBON_WIRES, BUTTONS, LEDS, TEENSY_LEFT, TEENSY_RIGHT
        pads=[pin for _,pin in FPC_WIRES.values()]+[pin for *_,pin in RIBBON_WIRES.values()]
        self.assertEqual(len(pads),len(set(pads)),'two wires share a Teensy pad')
        self.assertLessEqual(set(pads),set(TEENSY_LEFT+TEENSY_RIGHT))
        self.assertNotIn(13,pads)  # onboard LED pin
        self.assertEqual(sorted(fpc for fpc,_ in FPC_WIRES.values()),list(range(6,41)))
        self.assertEqual(len(WIRING),30)
        self.assertEqual({c for pair in BUTTONS.values() for c in pair}|set(LEDS.values())|{16},
                         {fpc for fpc,_ in FPC_WIRES.values()}-set(EXPECTED_CONTACTS))
        # Bundles A-C keep the FPC ends of the original Pico build.
        self.assertEqual([FPC_WIRES[f'{b}{i}'][0] for b,n in (('A',10),('B',10),('C',6)) for i in range(1,n+1)],
                         [11,12,*range(17,41)])

    def test_generated_files_are_current(self):
        from tools.generate import outputs
        for path,content in outputs().items():
            self.assertEqual(path.read_text(encoding='utf-8'),content,f'{path.name}: run python tools/generate.py')

    def test_mouse_buttons_are_scanned(self):
        from diagnostics.model import BUTTONS
        for pair in BUTTONS.values(): self.assertEqual(parse_pairs([list(pair)]),{pair})


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
    def test_trackpoint_directions_need_a_live_trackpoint(self):
        mouse=MouseState()
        mouse.move(50,0); self.assertFalse(mouse.directions)
        mouse.status('ready')
        for dx,dy in [(25,0),(-25,0),(0,25),(0,-25)]: mouse.move(dx,dy)
        self.assertEqual(mouse.directions,{'Left','Right','Up','Down'})
        self.assertEqual(mouse.report()['trackpoint'],'ready')

    def test_small_movements_accumulate(self):
        mouse=MouseState(); mouse.status('ready')
        for _ in range(4): mouse.move(5,0)
        self.assertEqual(mouse.directions,{'Right'})

    def test_buttons_pass_on_release_only(self):
        from diagnostics.model import BUTTONS
        mouse=MouseState()
        for name,pair in BUTTONS.items():
            mouse.feed({pair}); self.assertNotIn(name,mouse.buttons)
            mouse.feed(set()); self.assertIn(name,mouse.buttons)
        self.assertEqual(mouse.report()['buttons'],['Left','Middle','Right'])

    def test_stopping_does_not_pass_a_held_button(self):
        from diagnostics.model import BUTTONS
        mouse=MouseState(); mouse.feed({BUTTONS['Left']}); mouse.cancel(); mouse.feed(set())
        self.assertFalse(mouse.buttons)

    def test_failed_start_is_reported(self):
        mouse=MouseState(); mouse.status('starting'); mouse.status('no response')
        self.assertEqual(mouse.report()['trackpoint'],'no response')
        mouse.move(50,0); self.assertFalse(mouse.directions)


if __name__=='__main__': unittest.main()

"""Run with T14_GUI_TESTS=1 on a desktop with Tk and pyserial available."""
import os
import unittest
from unittest.mock import Mock


@unittest.skipUnless(os.environ.get('T14_GUI_TESTS')=='1','Requires a desktop display')
class GuiTests(unittest.TestCase):
    def setUp(self):
        import tkinter as tk
        from diagnostics.__main__ import App
        self.root=tk.Tk()
        self.app=App(self.root,autoconnect=False)
        self.app.save_session=Mock()
        self.app.send=Mock()
        self.root.update()

    def tearDown(self): self.app.close()

    def connect(self):
        # What the firmware says after the app finds the Teensy.
        self.app.handle({'type':'hello','protocol':2,'firmware':'t14-diagnostics','wiring':'t14-teensy41-v1'})
        self.app.handle({'type':'started'})
        self.app.handle({'type':'state','pairs':[]})

    def test_starts_by_itself(self):
        from diagnostics.model import WIRING_ID
        self.assertEqual(self.app.prompt.get(),'Plug in the Teensy')
        self.assertEqual(self.app.connection_text.get(),'Not connected')
        self.connect()
        self.assertEqual(self.app.connection_text.get(),'Connected')
        self.assertEqual(self.app.light.itemcget(self.app.dot,'fill'),'#4cc277')
        sent=[c.args[0] for c in self.app.send.call_args_list]
        self.assertEqual(sent[:2],['START '+WIRING_ID,'TRACKPOINT'])
        self.assertEqual(self.app.prompt.get(),'Press Esc')

    def test_fast_sequence_never_waits_for_a_timer(self):
        from diagnostics.model import ORDER,EXPECTED
        app=self.app; self.connect()
        for index,key in enumerate(ORDER):
            self.assertEqual(app.session.target,key)
            app.handle({'type':'state','pairs':[list(EXPECTED[key])]})
            app.handle({'type':'state','pairs':[]})
            self.assertEqual(app.session.target,ORDER[index+1] if index+1<len(ORDER) else None)
        self.assertEqual(app.prompt.get(),'All keys passed')
        self.assertEqual(app.save_session.call_count,84)

    def test_wrong_key_names_its_wires(self):
        from diagnostics.model import EXPECTED
        app=self.app; self.connect()
        app.handle({'type':'state','pairs':[list(EXPECTED['A'])]})
        app.handle({'type':'state','pairs':[]})
        self.assertEqual(app.prompt.get(),'Check Esc')
        self.assertIn('FPC 29 + 34',app.status.get())

    def test_nothing_is_cut_off(self):
        from diagnostics.keyboard import KEYS
        from diagnostics.model import EXPECTED
        self.assertEqual({r[0] for r in KEYS},set(EXPECTED))
        positions={r[0]:r[1:] for r in KEYS}
        self.assertEqual(positions['Home'][1],positions['F12'][1])
        self.assertGreater(positions['Left'][1],positions['Up'][1])
        board=self.app.keyboard
        for size in ('1120x640','820x520','1920x1080','1000x1000'):
            self.root.geometry(size); self.root.update()
            bottom=self.root.winfo_rooty()+self.root.winfo_height()
            self.assertLessEqual(board.winfo_rooty()+board.winfo_height(),bottom,size)
            items=[board.bbox(i) for i in board.find_all()]
            for x1,y1,x2,y2 in items:
                self.assertGreaterEqual(min(x1,y1),0,size)
                self.assertLessEqual(x2,board.winfo_width(),size)
                self.assertLessEqual(y2,board.winfo_height(),size)

    def test_trackpoint_and_buttons(self):
        from diagnostics.model import BUTTONS
        app=self.app; self.connect()
        app.handle({'type':'trackpoint','status':'ready'})
        self.assertEqual(app.metadata['mouse']['trackpoint'],'ready')
        for dx,dy in [(30,0),(-30,0),(0,30),(0,-30)]: app.handle({'type':'motion','dx':dx,'dy':dy})
        for pair in BUTTONS.values():
            app.handle({'type':'state','pairs':[list(pair)]})
            self.assertIsNone(app.session.results.get('Esc'))  # buttons never count as keys
            app.handle({'type':'state','pairs':[]})
        report=app.metadata['mouse']
        self.assertEqual(report['directions'],['Down','Left','Right','Up'])
        self.assertEqual(report['buttons'],['Left','Middle','Right'])

    def test_retry_only_when_trackpoint_fails(self):
        app=self.app; self.connect()
        app.handle({'type':'trackpoint','status':'no response'})
        self.assertTrue(app.mouse.retry.winfo_manager())
        app.mouse.retry.invoke()
        self.assertEqual(app.send.call_args.args[0],'TRACKPOINT')
        app.handle({'type':'trackpoint','status':'ready'})
        self.assertFalse(app.mouse.retry.winfo_manager())

    def test_lights_send_commands(self):
        app=self.app; self.connect()
        app.lights.leds['Caps Lock'].set(True); app.lights.apply_leds()
        app.lights.level.set(2); app.lights.apply_backlight()
        sent=[c.args[0] for c in app.send.call_args_list]
        self.assertIn('LED 1',sent); self.assertIn('BACKLIGHT 2',sent)

    def test_unplugging_turns_the_light_gray(self):
        self.connect(); self.app.handle({'type':'disconnected'})
        self.assertEqual(self.app.connection_text.get(),'Not connected')
        self.assertEqual(self.app.light.itemcget(self.app.dot,'fill'),'#6b7078')

    def test_restarts_after_a_fault(self):
        app=self.app; self.connect()
        app.handle({'type':'fault','fpc':12})
        self.assertEqual(app.prompt.get(),'Check the wiring')
        app.started_at=0; app.send.reset_mock(); app.poll()
        self.assertTrue(app.send.call_args_list[0].args[0].startswith('START'))

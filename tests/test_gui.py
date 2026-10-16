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
        self.app=App(self.root,demo=True)
        self.app.save_session=Mock()
        self.root.update()

    def tearDown(self): self.app.close()

    def test_fast_sequence_never_waits_for_a_timer(self):
        from diagnostics.model import ORDER,EXPECTED
        app=self.app
        app.start_scan()
        while not app.events.empty(): app.handle(app.events.get())
        for index,key in enumerate(ORDER):
            self.assertEqual(app.session.target,key)
            app.handle({'type':'state','pairs':[list(EXPECTED[key])]})
            app.handle({'type':'state','pairs':[]})
            self.assertEqual(app.session.target,ORDER[index+1] if index+1<len(ORDER) else None)
        self.assertEqual(app.prompt.get(),'All keys passed')
        self.assertEqual(app.save_session.call_count,84)

    def test_photo_layout_and_window_bounds(self):
        from diagnostics.keyboard import KEYS
        from diagnostics.model import EXPECTED
        self.assertEqual({r[0] for r in KEYS},set(EXPECTED))
        self.assertEqual(len(KEYS),84)
        positions={r[0]:r[1:] for r in KEYS}
        self.assertEqual(positions['Home'][1],positions['F12'][1])
        self.assertGreater(positions['Left'][1],positions['Up'][1])
        self.assertGreater(positions['Space'][2],positions['A'][2]*4)
        for size in ('1160x720','920x650'):
            self.root.geometry(size); self.root.update()
            self.assertLessEqual(self.app.start_button.winfo_rooty()+self.app.start_button.winfo_height(),self.root.winfo_rooty()+self.root.winfo_height())
            for key,(x1,y1,x2,y2) in self.app.keyboard.rectangles.items():
                self.assertGreaterEqual(x1,0,key); self.assertGreaterEqual(y1,0,key)
                self.assertLessEqual(x2,self.app.keyboard.winfo_width(),key)
                self.assertLessEqual(y2,self.app.keyboard.winfo_height(),key)

    def test_mouse_cannot_pass_disconnected_t14(self):
        self.app.mouse.start()
        self.assertEqual(self.app.metadata['mouse']['t14_trackpoint'],'not connected')
        self.assertEqual(self.app.metadata['mouse']['t14_buttons'],'not connected')

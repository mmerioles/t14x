"""Reference wiring and measured press/release results, independent of the GUI."""
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

BOARD = 'Teensy 4.1'
WIRING_ID = 't14-teensy41-v1'
COLORS = ['brown','red','orange','yellow','green','blue','purple','gray','white','black']
# 40-pin keyboard ribbon: wire ID -> (FPC contact, Teensy pin). Bundles A-C keep
# the FPC ends of the original Pico build; only their Teensy ends are new.
FPC_WIRES = {
    'A1':(11,3), 'A2':(12,4), 'A3':(17,5), 'A4':(18,6), 'A5':(19,7),
    'A6':(20,8), 'A7':(21,9), 'A8':(22,10), 'A9':(23,11), 'A10':(24,12),
    'B1':(25,23), 'B2':(26,22), 'B3':(27,21), 'B4':(28,20), 'B5':(29,19),
    'B6':(30,18), 'B7':(31,17), 'B8':(32,16), 'B9':(33,15), 'B10':(34,14),
    'C1':(35,41), 'C2':(36,40), 'C3':(37,39), 'C4':(38,38), 'C5':(39,37), 'C6':(40,36),
    'D1':(6,24), 'D2':(7,25), 'D3':(8,26), 'D4':(9,27),
    'D5':(10,28), 'D6':(13,29), 'D7':(14,30), 'D8':(15,31), 'D9':(16,'3V3_L'),
}
# T14 mouse buttons share FPC 9; LED cathodes share the FPC 16 anode.
BUTTONS = {'Left':(8,9), 'Middle':(6,9), 'Right':(7,9)}
LEDS = {'Caps Lock':10, 'Mic mute':13, 'Speaker mute':14, 'Fn Lock':15}
LED_RESISTOR = '330 Ω'
# 12-pin TrackPoint/backlight ribbon, wired by signal name: wire -> (signal, color, pad).
RIBBON_WIRES = {
    'T1':('TrackPoint Vcc','red','3V3_R'), 'T2':('TrackPoint GND','black','GND_L'),
    'T3':('TrackPoint CLK','yellow',0), 'T4':('TrackPoint DATA','green',1),
    'T5':('TrackPoint RST','blue',2), 'T6':('Backlight V+','orange','VIN'),
    'T7':('Backlight gate','purple',33), 'T8':('Backlight V−','gray','GND_R'),
}
# Teensy 4.1 edge pads, top to bottom with the USB socket at the top.
TEENSY_LEFT = ['GND_L', *range(13), '3V3_L', *range(24, 33)]
TEENSY_RIGHT = ['VIN', 'GND', '3V3_R', *range(23, 12, -1), 'GND_R', *range(41, 32, -1)]
PADS = {'GND_L':'GND (left, top corner)', '3V3_L':'3.3V (left, below pin 12)',
        'VIN':'VIN (5 V, right, top corner)', '3V3_R':'3.3V (right, 3rd from top)',
        'GND_R':'GND (right, below pin 13)'}
COLS = [29, 36, 32, 35, 40, 33, 39, 38, 11]
# Uncompressed matrix from delingren/thinkpad_keyboards/t14-v1.md.
ROWS = {
    34: ['Esc','A','`','1','Tab','Q',None,'Z'],
    28: [None,'S','F1','2','Caps Lock','W',None,'X'],
    30: ['F4','D','F2','3','F3','E',None,'C'],
    27: ['G','F','5','4','T','R','B','V'],
    31: ['H','J','6','7','Y','U','N','M'],
    24: ['F6','K','=','8',']','I',None,','],
    26: [None,'L','F8','9','F7','O',None,'.'],
    25: ["'",';','-','0','[','P','/',None],
    18: ['F5','\\','F9','F10','Backspace',None,'Space','Enter'],
    19: [None,None,'Delete','F11',None,None,'Down',None],
    20: ['Up',None,'Home','End',None,None,'Left',None],
    21: [None,None,'Insert','F12','Super',None,'Right',None],
    17: [None,None,'PgUp','PgDn'],
    37: [None,None,None,None,'LShift',None,None,'RShift'],
    23: [None,None,'LCtrl',None,None,None,None,'RCtrl'],
    22: ['LAlt',None,None,'PrtSc',None,None,'RAlt'],
    12: [None,None,None,None,None,None,None,None,'Fn'],
}
MATRIX = [*ROWS, *COLS]
# Contacts the diagnostic scanner checks pairwise: key matrix plus mouse buttons.
SCAN = sorted([*MATRIX, *{c for pair in BUTTONS.values() for c in pair}])
WIRING = {fpc: pin for fpc, pin in FPC_WIRES.values() if fpc in SCAN}
EXPECTED = {key: tuple(sorted((row, COLS[col])))
            for row, keys in ROWS.items() for col, key in enumerate(keys) if key}
LAYOUT = [
    ['Esc',*[f'F{i}' for i in range(1,13)],'Home','End','Insert','Delete'],
    ['`',*list('1234567890'),'-','=','Backspace'],
    ['Tab',*list('QWERTYUIOP'),'[',']','\\'],
    ['Caps Lock',*list('ASDFGHJKL'),';',"'",'Enter'],
    ['LShift',*list('ZXCVBNM'),',','.','/','RShift'],
    ['Fn','LCtrl','Super','LAlt','Space','RAlt','PrtSc','RCtrl','PgUp','Up','PgDn','Left','Down','Right'],
]
ORDER = [key for row in LAYOUT for key in row]


class Guide:
    """Progress only on fresh released snapshots, never on a one-shot timer."""
    def __init__(self, session):
        self.session = session
        self.pending = False

    def begin(self):
        self.pending = True

    def cancel(self):
        self.pending = False

    def advance(self):
        if not self.pending or not self.session.ready or self.session.target is not None:
            return None
        key = self.session.next_key()
        self.pending = False
        if key:
            self.session.arm(key)
        return key

    def feed(self, pairs):
        result = self.session.feed(pairs)
        if result:
            self.pending = result[1] == 'pass'
        # Arm immediately after a successful release, before the next queued press.
        return result, self.advance()


def parse_pairs(value):
    if not isinstance(value, list):
        raise ValueError('pairs must be a list')
    pairs = set()
    for pair in value:
        if (not isinstance(pair, list) or len(pair) != 2
                or any(type(p) is not int or p not in WIRING for p in pair)
                or pair[0] == pair[1]):
            raise ValueError('invalid connector pair')
        pairs.add(tuple(sorted(pair)))
    return pairs


class Session:
    def __init__(self):
        self.results = {}
        self.active = set()
        self.target = None
        self.seen = set()
        self.invalid = False
        self.ready = False

    def arm(self, key):
        if key not in EXPECTED:
            raise ValueError('unknown reference key')
        if self.active or not self.ready:
            raise ValueError('Wait for a live, all-released state before selecting a key.')
        self.target, self.seen, self.invalid = key, set(), False

    def cancel(self):
        self.target = None
        self.seen = set()
        self.invalid = False
        self.ready = False
        self.active = set()

    def feed(self, pairs):
        self.active = set(pairs)
        self.ready = not pairs
        if self.target is None:
            return None
        self.seen.update(pairs)
        if len(pairs) > 1 or len(self.seen) > 1:
            self.invalid = True
        if pairs or not self.seen:
            return None
        key, observed = self.target, sorted(self.seen)
        status = ('ambiguous' if self.invalid else
                  'pass' if observed == [EXPECTED[key]] else 'mismatch')
        self.results[key] = {'status': status, 'observed': observed}
        self.target = None
        return key, status

    def next_key(self):
        return next((k for k in ORDER if k not in self.results), None)

    def export(self, directory, metadata=None):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        report = {'created_utc': datetime.now(timezone.utc).isoformat(),
                  'reference': 'https://github.com/delingren/thinkpad_keyboards/blob/main/t14-v1.md',
                  'board': BOARD, 'wiring_id': WIRING_ID,
                  'wiring': WIRING, 'metadata': metadata or {}, 'keys': {}}
        lines = ['# T14 measured key diagnostics', '',
                 '**Mode: '+report['metadata'].get('mode','unspecified')+'**', '',
                 'Pass means the selected key produced its reference pair and was released.',
                 'Untested keys are not evidence of a hardware fault. Labels depend on the operator pressing the requested key.', '',
                 '| Key | Expected FPC pair | Teensy pins | Observed FPC pairs | Result |',
                 '| :--- | :--- | :--- | :--- | :--- |']
        with (directory/'keys.csv').open('w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['key','expected_fpc','teensy_pins','observed_fpc','result'])
            for key in ORDER:
                expected = EXPECTED[key]
                result = self.results.get(key, {'status':'untested','observed':[]})
                report['keys'][key] = {'expected': expected, **result}
                pair = '/'.join(map(str, expected))
                gp = '/'.join(str(WIRING[p]) for p in expected)
                observed = ', '.join('/'.join(map(str,p)) for p in result['observed']) or '—'
                writer.writerow([key,pair,gp,observed,result['status']])
                label = key.replace('\\','&#92;').replace('|','&#124;')
                lines.append(f'| {label} | {pair} | {gp} | {observed} | {result["status"]} |')
        (directory/'report.json').write_text(json.dumps(report,indent=2)+'\n', encoding='utf-8')
        mouse=report['metadata'].get('mouse')
        if mouse:
            lines.extend(['', '## TrackPoint and mouse buttons', '',
                          'TrackPoint: '+mouse['trackpoint']+'.',
                          'Directions: '+(', '.join(mouse['directions']) or 'untested')+'.',
                          'Buttons: '+(', '.join(mouse['buttons']) or 'untested')+'.'])
        (directory/'README.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
        return directory

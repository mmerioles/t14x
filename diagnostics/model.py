"""Reference wiring and measured press/release results, independent of the GUI."""
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

CONNECTORS = [11, 12, *range(17, 41)]
GPIOS = [*range(23), 26, 27, 28]
WIRING = dict(zip(CONNECTORS, GPIOS))
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
                  'wiring': WIRING, 'metadata': metadata or {}, 'keys': {}}
        lines = ['# T14 measured key diagnostics', '',
                 '**Mode: '+report['metadata'].get('mode','unspecified')+'**', '',
                 'Pass means the selected key produced its reference pair and was released.',
                 'Untested keys are not evidence of a hardware fault. Labels depend on the operator pressing the requested key.', '',
                 '| Key | Expected FPC pair | Expected GPIO pair | Observed FPC pairs | Result |',
                 '| :--- | :--- | :--- | :--- | :--- |']
        with (directory/'keys.csv').open('w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['key','expected_fpc','expected_gpio','observed_fpc','result'])
            for key in ORDER:
                expected = EXPECTED[key]
                result = self.results.get(key, {'status':'untested','observed':[]})
                report['keys'][key] = {'expected': expected, **result}
                pair = '/'.join(map(str, expected))
                gp = '/'.join(f'GP{WIRING[p]}' for p in expected)
                observed = ', '.join('/'.join(map(str,p)) for p in result['observed']) or '—'
                writer.writerow([key,pair,gp,observed,result['status']])
                label = key.replace('\\','&#92;').replace('|','&#124;')
                lines.append(f'| {label} | {pair} | {gp} | {observed} | {result["status"]} |')
        (directory/'report.json').write_text(json.dumps(report,indent=2)+'\n', encoding='utf-8')
        mouse=report['metadata'].get('mouse')
        if mouse:
            lines.extend(['', '## Mouse', '',
                          'Source: '+mouse['source']+'.',
                          'T14 TrackPoint: '+mouse['t14_trackpoint']+'.',
                          'T14 buttons: '+mouse['t14_buttons']+'.',
                          'Computer pointer directions: '+(', '.join(mouse['directions']) or 'untested')+'.',
                          'Computer pointer buttons: '+(', '.join(mouse['buttons']) or 'untested')+'.'])
        (directory/'README.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
        return directory

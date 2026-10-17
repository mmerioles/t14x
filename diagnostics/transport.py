"""Serial I/O runs off the Tk thread; closing the app stops the scanner."""
import json
import queue
import threading
import time
from .model import WIRING_ID


class Connection:
    def __init__(self, port, events):
        self.port, self.events = port, events
        self.commands = queue.Queue()
        self.closed = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)

    def start(self):
        self.thread.start()

    def send(self, command):
        self.commands.put(command)

    def close(self):
        self.closed.set()

    def run(self):
        import serial
        try:
            with serial.Serial(self.port,115200,timeout=0.05,write_timeout=0.5) as device:
                device.reset_input_buffer()
                device.write(b'STOP\nHELLO\n')
                next_ping, deadline = time.monotonic()+0.5, time.monotonic()+5
                identified = False
                buffer = bytearray()
                try:
                    while not self.closed.is_set():
                        now = time.monotonic()
                        if now > deadline:
                            raise RuntimeError('No diagnostic firmware response. Flash t14_diagnostics.hex or reconnect.')
                        if identified and now >= next_ping:
                            device.write(b'PING\n')
                            next_ping = now+0.5
                        while not self.commands.empty():
                            command = self.commands.get_nowait()
                            if identified:
                                device.write((command+'\n').encode('ascii'))
                        buffer.extend(device.read(max(1,min(device.in_waiting,4096))))
                        if len(buffer)>16384:
                            raise RuntimeError('Serial message exceeded protocol limit')
                        while b'\n' in buffer:
                            raw, _, rest = buffer.partition(b'\n')
                            buffer = bytearray(rest)
                            try:
                                event = json.loads(raw)
                            except (ValueError, UnicodeDecodeError):
                                continue
                            if not isinstance(event,dict):
                                continue
                            if event.get('type') == 'hello':
                                if (event.get('protocol') != 2 or event.get('firmware') != 't14-diagnostics'
                                        or event.get('wiring') != WIRING_ID):
                                    raise RuntimeError('Incompatible firmware or wiring version')
                                identified = True
                            if identified:
                                deadline = time.monotonic()+3
                                self.events.put(event)
                finally:
                    device.write(b'STOP\n')
        except Exception as exc:
            self.events.put({'type':'connection_error','message':str(exc)})
        finally:
            self.events.put({'type':'disconnected'})

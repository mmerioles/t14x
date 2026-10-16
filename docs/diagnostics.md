# Diagnostics

Flash `t14_diagnostics.uf2` to use this app. The everyday HID keyboard firmware has no serial port.
Run commands from the repository root.


Use Python 3.10 or newer with Tkinter. Windows and python.org macOS Python
installers normally include Tk; on Ubuntu/Debian install `python3-tk` if needed.
From the repository folder:

```sh
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m diagnostics
```

macOS/Linux:

```sh
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m diagnostics
```

Use `--demo` to try the interface without hardware. Simulation reports are
marked as such. Use `--port COM3` (or your OS's serial device path) to connect
automatically. On Linux, your account needs access to the serial device,
usually through the `dialout` group; reconnect/login after a group change.

### Test every key

1. Flash `build/t14_diagnostics.uf2` as described below. Select the Pico serial
   port and click **Connect**. The app checks firmware and wiring versions.
2. Release every key and click **Start**.
3. Press and release the key named at the top. The next key appears automatically.
   There is no timer or extra Next button. A held key waits for release.
4. **White outline:** next key. **Green:** passed. **Blue:** pressed.
   **Orange:** check that key. Click any key to retest it.
5. **Pause** stops the scan. **Start** resumes. **Details** shows pin information
   when needed. **Open results** loads an earlier saved report.
6. Click **Save** to save a timestamped folder with `report.json`,
   `keys.csv`, and a clean Markdown `README.md` containing expected and observed
   connector pairs. Each completed key test also autosaves those three files
   under `diagnostic-results/hardware-/<session timestamp>/` relative to the
   launch directory. Simulation results use a separate `simulation-` folder.
   Starting again after all keys pass creates a new session and keeps old reports.

### Mouse

The **Mouse** tab includes movement and left/middle/right click checks for the
computer's pointer. Click **Test computer mouse**, move inside the box, and
press and release each mouse button. Results explicitly identify the source
as the computer pointer; Tk cannot identify which physical mouse produced it.

**The T14 TrackPoint and its three buttons are not connected in our current
wiring and cannot be verified yet.** The smaller ribbon is still disconnected,
and the mouse-button lines on the 40-pin connector are not among our 26 matrix
wires. A PC mouse passing this optional test never marks the T14 mouse as passed.
Direct T14 mouse testing still requires verified wiring, spare I/O or a separate
controller, and a PS/2 firmware backend. The current firmware only scans keys.

The scanner intentionally tests one key at a time. Multiple simultaneous keys
can create indirect paths/ghosting in this undioded matrix and cannot establish
an individual key's wiring. An ambiguous cycle must be released and retested.
The app does not infer physical key labels: the operator must press the key
requested. Regional layouts may differ from the US reference.

If a requested key produces no activity, check seating, orientation, and
continuity of its two expected FPC lines. A consistently wrong pair suggests
crossed wires or a reference-layout difference. A connection that persists
with every key released suggests a short or stuck key. An idle scan alone
cannot distinguish correct wiring from an unplugged/open ribbon.

### Firmware behavior and serial protocol

The firmware starts with all matrix pins as inputs and pull resistors off.
Scanning begins only on an explicit start command. It pulls other lines up
weakly and drives exactly one GPIO **low** at a time, scanning both directions
to find connector pairs without assuming rows or columns. It never drives a
matrix line high. The debounce period is 20 ms; full state snapshots are sent
on changes and every 250 ms. USB disconnect or three seconds without a host
command stops scanning. The GUI also stops accepting tests when scan data is
stale. This is not protection against externally applied voltage or miswiring.

Commands are ASCII lines at USB serial baud setting 115200:

| Command | Meaning |
| :--- | :--- |
| `HELLO` | Return firmware, protocol version 1, and wiring ID `t14-fpc-v1` |
| `START t14-fpc-v1` | Start scanning the exact wiring table below |
| `PING` | Keep the scan alive; the app sends this every 500 ms |
| `STOP` | Stop scanning and disable pull resistors |

Responses are newline-delimited JSON, for example:

```json
{"type":"state","pairs":[[29,34]]}
```

That pair corresponds to Esc in the reference. An empty `pairs` array means
all keys are released. `fault`, `error`, and `stopped` messages explain failures.


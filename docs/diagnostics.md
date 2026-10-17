# Diagnostics

Checks every wire from the computer: all 84 keys, the TrackPoint, the three mouse buttons, the four indicator LEDs and the backlight. Flash **`t14_diagnostics.hex`** first (same steps as the [keyboard firmware](../README.md#1--flash-the-firmware)). The keyboard firmware has no serial port.

## Run the app

From the project folder, run `py run_diagnostics.py` on Windows or `python3 run_diagnostics.py` on macOS/Linux. The first run creates `.venv` and installs [requirements.txt](../requirements.txt); later runs start at once. If Python or Tk is missing, it tells you how to install it. The [README](../README.md#3--test-the-wiring) has step-by-step instructions.

The app finds the Teensy by itself. If it doesn’t, add `--port COM5` (or `/dev/ttyACM0`).

## Test

Plug in the Teensy. The app connects, checks the firmware and wiring versions, and starts testing by itself. There’s nothing to click.

| Tab | What to do | Pass |
| :--- | :--- | :--- |
| **Keyboard** | Press and release the key shown at the top. The next one appears by itself | Green outline. Orange means check that key; the app names its two wires. Click a key to test it again |
| **TrackPoint** | Push the stick up, down, left and right, then click each T14 button | Directions 4/4, Buttons 3/3 |
| **Lights** | Tick each LED and pick each backlight level | You see the matching light |

The next key has a white outline and a pressed key turns blue. Results save automatically to `diagnostic-results/` as `report.json`, `keys.csv` and a readable `README.md`. If the Teensy is unplugged or a wire faults, testing picks up again by itself once it’s fixed.

## When something fails

| Symptom | Likely cause |
| :--- | :--- |
| Key gives no activity | One of its two FPC wires: seating, orientation or continuity |
| Key always shows the same wrong pair | Two wires crossed |
| “FPC n is stuck low” on Start | That wire touches ground, or sits on the wrong FPC contact |
| TrackPoint “not responding” | CLK and DATA swapped, RST missing, or no 3.3 V or GND at the TrackPoint. Fix it, then click **Try again** |
| TrackPoint ready but a direction never passes | Push harder or longer; the threshold is 20 counts |
| Button never passes | D4 (FPC 9) or that button’s wire |
| No LED lights | D9 (FPC 16) to 3.3 V |
| One LED dark | Its resistor or wire, or it’s in backwards on the breakout |
| No backlight | T6 on VIN, T8 on GND, T7 on pin 33, or the ribbon order |

The scanner tests one key at a time. Several keys held together can make indirect paths in this matrix, so those tests read *ambiguous*; release and retry. A quiet scan can’t tell good wiring from an unplugged ribbon, so press keys to prove it.

## How the firmware scans

All matrix and button lines start as inputs with pulls off. When testing starts, each line gets a weak pull-up and exactly one line at a time is driven **low**, so pairs are found without assuming rows or columns. No matrix or button line is ever driven high. A change counts after 20 ms; full snapshots go out on change and every 250 ms. Unplugging USB, three seconds without a host message, a `STOP` command, a fault or an error switches off scanning, lights and the TrackPoint. That protects against mistakes in software, not against wrong voltages.

### Serial protocol (version 2)

ASCII command lines in; one JSON object per line out.

| Command | Reply |
| :--- | :--- |
| `HELLO` | `{"type":"hello","protocol":2,"firmware":"t14-diagnostics","board":"teensy41","wiring":"t14-teensy41-v1"}` |
| `START t14-teensy41-v1` | `started`, then `{"type":"state","pairs":[[29,34]]}` snapshots (FPC contact pairs) |
| `PING` | `pong`. The app sends one every 500 ms |
| `TRACKPOINT` | `trackpoint` with `starting`, then `ready` or `no response`; then `{"type":"motion","dx":3,"dy":-2}` (screen directions) |
| `LED 0`–`LED 15` | `leds`. Bits: 1 Caps Lock, 2 Mic mute, 4 Speaker mute, 8 Fn Lock |
| `BACKLIGHT 0`–`2` | `backlight`. Off, low, high |
| `STOP` | `stopped` |

`[29,34]` is Esc. Mouse buttons appear as `[8,9]` left, `[6,9]` middle and `[7,9]` right. `fault`, `error` and `stopped` explain anything that ends a test.

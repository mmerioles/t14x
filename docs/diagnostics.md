# Diagnostics

Tests all 84 keys, the TrackPoint, the mouse buttons, the LEDs and the backlight. Needs `t14_diagnostics.hex` on the Teensy ([how to flash](../README.md#2-flash)).

## Test

Run `py run_diagnostics.py` (Windows) or `python3 run_diagnostics.py` (macOS/Linux) in the project folder, then plug in the Teensy. Testing starts by itself. If the Teensy isn’t found, add `--port COM5` (or `/dev/ttyACM0`). On Linux, a permission error means running `sudo usermod -aG dialout $USER` and logging back in.

| Tab | What to do | Pass |
| :--- | :--- | :--- |
| **Keyboard** | Press and release the key shown at the top. The next one appears by itself | Green outline. Orange means check that key; the app names its two wires. Click a key to test it again |
| **TrackPoint** | Push the stick up, down, left and right, then click each T14 button | Directions 4/4, Buttons 3/3 |
| **Lights** | Tick each LED and pick each backlight level | You see the matching light |

Results save to `diagnostic-results/`.

## When something fails

| Symptom | Likely cause |
| :--- | :--- |
| Key gives no activity | One of its two FPC wires: seating, orientation or continuity |
| Key always shows the same wrong pair | Two wires crossed |
| “FPC n is stuck low” | That wire touches ground, or sits on the wrong FPC contact |
| TrackPoint “not responding” | CLK and DATA swapped, RST missing, or no 3.3 V or GND at the TrackPoint. Fix it, then click **Try again** |
| TrackPoint ready but a direction never passes | Push harder or longer; the threshold is 20 counts |
| Button never passes | D4 (FPC 9) or that button’s wire |
| No LED lights | D9 (FPC 16) to 3.3 V |
| One LED dark | Its resistor or wire, or it’s in backwards on the breakout |
| No backlight | T6 on VIN, T8 on GND, T7 on pin 33, or the ribbon order |

Press one key at a time; several at once read as *ambiguous*.

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

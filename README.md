# T14 Gen 1 USB keyboard · Teensy 4.1

Turns a ThinkPad T14 Gen 1 keyboard into a plug-in USB keyboard with a working TrackPoint, mouse buttons, indicator LEDs and backlight, using a **Teensy 4.1**.

| Part | Status |
| :--- | :--- |
| 84 keys | ✅ Matrix verified 84/84 on hardware ([report](docs/verified-report.json)); same FPC contacts carry over |
| Fn layer, media keys, Fn Lock | ✅ Unit-tested in firmware logic |
| TrackPoint, 3 mouse buttons | 🧪 New: firmware built and unit-tested, awaiting a hardware test |
| 4 indicator LEDs, backlight | 🧪 New: firmware built, awaiting a hardware test |

After wiring, [run the diagnostics](#3--test-the-wiring) to check every wire before everyday use.

## You need

- **Teensy 4.1** and a micro-USB **data** cable
- **40-pin 0.5 mm FPC breakout** (keys, mouse buttons, LEDs) and **12-pin 1.0 mm FPC breakout** (TrackPoint, backlight)
- **4 × 330 Ω resistors** (anything from 220 Ω to 1 kΩ works) for the indicator LEDs
- Hookup wire in the colors below, and a multimeter
- The free **[Teensy Loader](https://www.pjrc.com/teensy/loader.html)** app

## 1 · Flash the firmware

1. Install and open **Teensy Loader**. On Linux, also install PJRC’s [udev rules](https://www.pjrc.com/teensy/00-teensy.rules).
2. Download **[t14_keyboard.hex](https://github.com/mmerioles/t14x-/raw/refs/heads/main/downloads/t14_keyboard.hex)**.
3. Connect the Teensy over USB. In Teensy Loader choose **File ▸ Open HEX File** and pick the file.
4. Press the **white button** on the Teensy. The loader shows *Reboot OK*, and the Teensy restarts as **T14 USB Keyboard**.

It stays installed. [Checksums](downloads/SHA256SUMS.txt).

## 2 · Wire it

**Unplug USB before changing wires.** Exposed ribbon copper faces the connector contacts. The Teensy is **3.3 V only**: the one 5 V wire is **T6** (backlight V+, on VIN).

![Teensy 4.1 wiring diagram](docs/wiring.svg)

| Bundle | What | Notes |
| :--- | :--- | :--- |
| **A, B, C** | Key matrix, FPC 11, 12, 17–40 | Same FPC ends as the old Pico build; only the Teensy end moves |
| **D** | Mouse buttons, indicator LEDs, FPC 6–10, 13–16 | Put a **330 Ω resistor in line on D5–D8** |
| **T** | 12-pin ribbon: TrackPoint and backlight | Wired by signal; **check the pin order first** (below) |

Bundles A–D use colors in this order: brown, red, orange, yellow, green, blue, purple, gray, white, black. There, black is a signal wire. Bundle T has its own colors: red is 3.3 V and black is ground. Leave FPC 1–5 and the TrackPoint’s own M/R/L ribbon contacts unconnected; the buttons are read through D1–D4.

<!-- wiring-tables:start -->
| Wire | Color | FPC | Teensy | Function |
| :--- | :--- | ---: | :--- | :--- |
| A1 | ![Brown](docs/wire-colors/brown.svg) | 11 | pin 3 | Key column C8 |
| A2 | ![Red](docs/wire-colors/red.svg) | 12 | pin 4 | Key row R16 |
| A3 | ![Orange](docs/wire-colors/orange.svg) | 17 | pin 5 | Key row R12 |
| A4 | ![Yellow](docs/wire-colors/yellow.svg) | 18 | pin 6 | Key row R8 |
| A5 | ![Green](docs/wire-colors/green.svg) | 19 | pin 7 | Key row R9 |
| A6 | ![Blue](docs/wire-colors/blue.svg) | 20 | pin 8 | Key row R10 |
| A7 | ![Purple](docs/wire-colors/purple.svg) | 21 | pin 9 | Key row R11 |
| A8 | ![Gray](docs/wire-colors/gray.svg) | 22 | pin 10 | Key row R15 |
| A9 | ![White](docs/wire-colors/white.svg) | 23 | pin 11 | Key row R14 |
| A10 | ![Black](docs/wire-colors/black.svg) | 24 | pin 12 | Key row R5 |
| B1 | ![Brown](docs/wire-colors/brown.svg) | 25 | pin 23 | Key row R7 |
| B2 | ![Red](docs/wire-colors/red.svg) | 26 | pin 22 | Key row R6 |
| B3 | ![Orange](docs/wire-colors/orange.svg) | 27 | pin 21 | Key row R3 |
| B4 | ![Yellow](docs/wire-colors/yellow.svg) | 28 | pin 20 | Key row R1 |
| B5 | ![Green](docs/wire-colors/green.svg) | 29 | pin 19 | Key column C0 |
| B6 | ![Blue](docs/wire-colors/blue.svg) | 30 | pin 18 | Key row R2 |
| B7 | ![Purple](docs/wire-colors/purple.svg) | 31 | pin 17 | Key row R4 |
| B8 | ![Gray](docs/wire-colors/gray.svg) | 32 | pin 16 | Key column C2 |
| B9 | ![White](docs/wire-colors/white.svg) | 33 | pin 15 | Key column C5 |
| B10 | ![Black](docs/wire-colors/black.svg) | 34 | pin 14 | Key row R0 |
| C1 | ![Brown](docs/wire-colors/brown.svg) | 35 | pin 41 | Key column C3 |
| C2 | ![Red](docs/wire-colors/red.svg) | 36 | pin 40 | Key column C1 |
| C3 | ![Orange](docs/wire-colors/orange.svg) | 37 | pin 39 | Key row R13 |
| C4 | ![Yellow](docs/wire-colors/yellow.svg) | 38 | pin 38 | Key column C7 |
| C5 | ![Green](docs/wire-colors/green.svg) | 39 | pin 37 | Key column C6 |
| C6 | ![Blue](docs/wire-colors/blue.svg) | 40 | pin 36 | Key column C4 |
| D1 | ![Brown](docs/wire-colors/brown.svg) | 6 | pin 24 | Middle mouse button |
| D2 | ![Red](docs/wire-colors/red.svg) | 7 | pin 25 | Right mouse button |
| D3 | ![Orange](docs/wire-colors/orange.svg) | 8 | pin 26 | Left mouse button |
| D4 | ![Yellow](docs/wire-colors/yellow.svg) | 9 | pin 27 | Mouse button common |
| D5 | ![Green](docs/wire-colors/green.svg) | 10 | pin 28 | Caps Lock LED − (through 330 Ω) |
| D6 | ![Blue](docs/wire-colors/blue.svg) | 13 | pin 29 | Mic mute LED − (through 330 Ω) |
| D7 | ![Purple](docs/wire-colors/purple.svg) | 14 | pin 30 | Speaker mute LED − (through 330 Ω) |
| D8 | ![Gray](docs/wire-colors/gray.svg) | 15 | pin 31 | Fn Lock LED − (through 330 Ω) |
| D9 | ![White](docs/wire-colors/white.svg) | 16 | 3.3V (left, below pin 12) | Indicator LED common + |

| Wire | Color | Ribbon signal | Teensy | Notes |
| :--- | :--- | :--- | :--- | :--- |
| T1 | ![Red](docs/wire-colors/red.svg) | TrackPoint Vcc | 3.3V (right, 3rd from top) | 3.3 V only |
| T2 | ![Black](docs/wire-colors/black.svg) | TrackPoint GND | GND (left, top corner) | Black is ground here |
| T3 | ![Yellow](docs/wire-colors/yellow.svg) | TrackPoint CLK | pin 0 |  |
| T4 | ![Green](docs/wire-colors/green.svg) | TrackPoint DATA | pin 1 |  |
| T5 | ![Blue](docs/wire-colors/blue.svg) | TrackPoint RST | pin 2 |  |
| T6 | ![Orange](docs/wire-colors/orange.svg) | Backlight V+ | VIN (5 V, right, top corner) | 5 V from USB |
| T7 | ![Purple](docs/wire-colors/purple.svg) | Backlight gate | pin 33 | PWM brightness |
| T8 | ![Gray](docs/wire-colors/gray.svg) | Backlight V− | GND (right, below pin 13) |  |
<!-- wiring-tables:end -->

### Check the 12-pin ribbon before powering it

The T14 reference gives the TrackPoint signal order (**Vcc, DATA, RST, M, R, L, GND, CLK**) but not the exact contact numbers, nor which contacts carry the backlight. Confirm with a multimeter on continuity, keyboard unplugged:

| Find | How |
| :--- | :--- |
| GND | Beeps to a ground point on the TrackPoint board, such as the middle pin of its crystal |
| Vcc | The other extra-wide trace; never beeps to GND |
| DATA, RST, CLK | Follow the order above from Vcc; your measured GND must land in its slot |
| Backlight gate, V− | Beep to the **G** and **S** pads of the MOSFET on the backlight film |
| Backlight V+ | The third backlight contact; it doesn’t beep to the MOSFET |

If anything disagrees, wire by your measurements. The diagnostics TrackPoint test confirms CLK and DATA, since swapped lines simply get no response.

## 3 · Test the wiring

The diagnostics app checks every key, the TrackPoint, the mouse buttons, the LEDs and the backlight.

1. **Install Python** (3.9 or newer):
   - **Windows:** from [python.org](https://www.python.org/downloads/). Tick **Add python.exe to PATH** in the installer.
   - **macOS:** from [python.org](https://www.python.org/downloads/). Apple’s built-in Python freezes with this app.
   - **Linux:** `sudo apt install python3 python3-tk python3-venv`
2. **Flash [t14_diagnostics.hex](https://github.com/mmerioles/t14x-/raw/refs/heads/main/downloads/t14_diagnostics.hex)** the same way as in step 1.
3. **Get this project:** on GitHub, click **Code ▸ Download ZIP** and unzip it.
4. **Open a terminal in that folder:**
   - **Windows:** open the folder, type `cmd` in the address bar and press Enter.
   - **macOS:** right-click the folder and choose **New Terminal at Folder**.
   - **Linux:** right-click inside the folder and choose **Open in Terminal**.
5. **Start the app:**

   | Windows | macOS / Linux |
   | :--- | :--- |
   | `py run_diagnostics.py` | `python3 run_diagnostics.py` |

   The first start sets everything up, which takes about a minute. After that it opens at once.
6. **Plug in the Teensy.** The app finds it and starts by itself. Press each key it asks for, then use the **TrackPoint** and **Lights** tabs. [What each test means](docs/diagnostics.md).
7. When everything passes, flash **t14_keyboard.hex** again to use the keyboard.

**Teensy not found?** Add `--port COM5` (or `/dev/ttyACM0`). **Linux says permission denied?** Run `sudo usermod -aG dialout $USER`, then log out and back in.

## 4 · Use it

| Keys | Action |
| :--- | :--- |
| Fn + Esc | **Fn Lock**. LED on: F1–F12 are standard keys (default). LED off: they do the printed function without Fn |
| Fn + F1 / F2 / F3 | Mute / volume down / volume up |
| Fn + F4 | Mic mute (sent as F20, which Linux maps to mic mute; remap it on Windows/macOS) |
| Fn + F5 / F6 | Screen brightness down / up, when the host supports it |
| Fn + F7 / F9 | Display switch (Super + P) / Settings (Super + I) |
| Fn + Space | Backlight off → low → high |
| Fn + P / Fn + K | Pause / Scroll Lock |
| TrackPoint | Move the pointer. **Hold middle and push to scroll**; tap middle to middle-click |

- **LEDs:** Caps Lock follows the computer. Speaker and mic mute show the last key press, and a volume key clears speaker mute. The computer can’t report its real mute state, so these LEDs can drift out of sync. The Teensy’s orange LED also shows Caps Lock.
- **Remembered across unplugging:** Fn Lock and backlight level. The lights switch off while the computer sleeps.
- **Limits:** six keys plus modifiers per report; ghost-prone key combinations are suppressed. F8, F10–F12 have no portable USB function and stay F-keys. The keyboard can’t wake a sleeping computer.

### Key matrix

Each key joins one row and one column. For example, **A = R0 + C1 = FPC 34 + 36 = Teensy pins 14 + 40**. Empty cells have no key. [Every key with its pins and USB code](docs/verified-keymap.md).

| Row / FPC | C0 / 29 | C1 / 36 | C2 / 32 | C3 / 35 | C4 / 40 | C5 / 33 | C6 / 39 | C7 / 38 | C8 / 11 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| R0 / 34 | Esc | A | &#96; | 1 | Tab | Q | · | Z | · |
| R1 / 28 | · | S | F1 | 2 | Caps Lock | W | · | X | · |
| R2 / 30 | F4 | D | F2 | 3 | F3 | E | · | C | · |
| R3 / 27 | G | F | 5 | 4 | T | R | B | V | · |
| R4 / 31 | H | J | 6 | 7 | Y | U | N | M | · |
| R5 / 24 | F6 | K | = | 8 | ] | I | · | , | · |
| R6 / 26 | · | L | F8 | 9 | F7 | O | · | . | · |
| R7 / 25 | ' | ; | - | 0 | [ | P | / | · | · |
| R8 / 18 | F5 | &#92; | F9 | F10 | Backspace | · | Space | Enter | · |
| R9 / 19 | · | · | Delete | F11 | · | · | Down | · | · |
| R10 / 20 | Up | · | Home | End | · | · | Left | · | · |
| R11 / 21 | · | · | Insert | F12 | Super | · | Right | · | · |
| R12 / 17 | · | · | PgUp | PgDn | · | · | · | · | · |
| R13 / 37 | · | · | · | · | LShift | · | · | RShift | · |
| R14 / 23 | · | · | LCtrl | · | · | · | · | RCtrl | · |
| R15 / 22 | LAlt | · | · | PrtSc | · | · | RAlt | · | · |
| R16 / 12 | · | · | · | · | · | · | · | · | Fn |

`L`/`R` mean left/right modifiers. `Super` is Windows on Windows and Command on macOS. The computer’s keyboard layout decides which characters you get.

## Build from source

Needs Python 3.10+ and [PlatformIO](https://platformio.org/install/cli). Run from the repository root:

```sh
pio run                                   # both firmware builds
python tools/generate.py                  # after editing the wiring in diagnostics/model.py
python -m unittest discover -s tests -v   # Python tests, including generated-file drift
```

| Output | Use |
| :--- | :--- |
| `.pio/build/keyboard/firmware.hex` | Everyday keyboard and TrackPoint (`downloads/t14_keyboard.hex`) |
| `.pio/build/diagnostics/firmware.hex` | Serial wiring tester for the [diagnostics app](docs/diagnostics.md) |

The C logic also has native tests, which CI runs along with both builds:

```sh
cc -std=c11 -Ifirmware tests/keyboard_core_test.c firmware/keyboard_core.c firmware/keymap.c -o build/kb && build/kb
cc -std=c11 -Ifirmware tests/mouse_core_test.c firmware/mouse_core.c -o build/ms && build/ms
```

`diagnostics/model.py` is the one source of truth for wiring. `tools/generate.py` writes the firmware pin tables, the wiring tables above, the diagram and the key list from it. The key map is generated only if all 84 saved hardware results match. The firmware uses PJRC’s Teensyduino USB IDs, so it suits personal use but not a product.

## Reference

- [T14 keyboard reverse engineering](https://github.com/delingren/thinkpad_keyboards/blob/main/t14-v1.md) and [TrackPoint and backlight notes](https://github.com/delingren/thinkpad_keyboards#trackpoint) (delingren)
- [Teensy 4.1 pinout](https://www.pjrc.com/teensy/pinout.html)
- Firmware: [keyboard](firmware/keyboard_main.cpp), [diagnostics](firmware/diagnostics_main.cpp), [Fn layer](firmware/keyboard_core.c), [TrackPoint](firmware/ps2.cpp), [mouse logic](firmware/mouse_core.c)

# T14 Gen 1 USB keyboard

A ThinkPad T14 Gen 1 keyboard on an original Raspberry Pi Pico. **84/84 keys verified** against the [saved hardware measurements](docs/verified-report.json).

USB HID enumeration and real typing confirmed on Windows. Other operating systems and pre-boot/BIOS use have not been tested here.

## Install in 5 steps

For the **original RP2040 Raspberry Pi Pico**, wired exactly as shown below. No compiler, Python, diagnostic app, or driver installer is needed.

1. **[Download t14_keyboard.uf2](https://github.com/mmerioles/t14x-/raw/refs/heads/main/downloads/t14_keyboard.uf2)** and save it to your computer.
2. Unplug the Pico. **Hold BOOTSEL** while connecting it with a USB **data** cable.
3. Release BOOTSEL. A drive named **RPI-RP2** appears in your file manager.
4. Drag **`t14_keyboard.uf2`** onto that drive. Copy the UF2 file itself, not a ZIP or source-code folder.
5. The drive disappears automatically and the Pico becomes a keyboard. Open a text editor and type.

Installation is complete. It stays installed after unplugging; future connections just work after normal USB detection. Windows, macOS, and Linux use their built-in HID driver.

**No RPI-RP2 drive?** Reconnect while holding BOOTSEL and try another data cable or USB port. **Drive disappears after copying?** That is normal. **Want to update or undo?** Repeat the same steps with another UF2; flashing replaces the installed program.

The downloadable file is the build tested on this keyboard. [Checksums](downloads/SHA256SUMS.txt) are included. To run wiring diagnostics instead, flash [t14_diagnostics.uf2](https://github.com/mmerioles/t14x-/raw/refs/heads/main/downloads/t14_diagnostics.uf2) and follow the [diagnostics instructions](docs/diagnostics.md).

## Key functions

F1–F12 are ordinary function keys. **Fn** is a local modifier:

| Shortcut | Function |
| :--- | :--- |
| Fn + F1 | Mute |
| Fn + F2 / F3 | Volume down / up |
| Fn + F5 / F6 | Brightness down / up, when supported by the host |

Other Fn combinations keep their normal key action. Lenovo-specific mic mute, Fn Lock, wireless, and call actions are not implemented. The Pico’s onboard LED follows Caps Lock; the keyboard’s own LEDs are unwired.

**Limits:** six ordinary keys plus modifiers per USB report; ghost-prone combinations are suppressed. TrackPoint, mouse buttons, backlight, and keyboard indicator LEDs are not connected.

## Wiring

Unplug USB before changing wires. **FPC** is the 40-pin breakout contact, **GP** is the Pico GPIO label, and **physical** is its header position. Match ribbon contact numbering before connecting; exposed copper faces the connector contacts.

Bundles A and B each use brown, red, orange, yellow, green, blue, purple, gray, white, black. Bundle C uses the first six colors. Black wires here are signals, not ground.

| Wire ID | Color | FPC pin | Pico GPIO | Physical pin | Matrix role |
| :--- | :--- | ---: | :--- | ---: | :--- |
| A1 | ![Brown](docs/wire-colors/brown.svg) | 11 | GP0 | 1 | C8 |
| A2 | ![Red](docs/wire-colors/red.svg) | 12 | GP1 | 2 | R16 |
| A3 | ![Orange](docs/wire-colors/orange.svg) | 17 | GP2 | 4 | R12 |
| A4 | ![Yellow](docs/wire-colors/yellow.svg) | 18 | GP3 | 5 | R8 |
| A5 | ![Green](docs/wire-colors/green.svg) | 19 | GP4 | 6 | R9 |
| A6 | ![Blue](docs/wire-colors/blue.svg) | 20 | GP5 | 7 | R10 |
| A7 | ![Purple](docs/wire-colors/purple.svg) | 21 | GP6 | 9 | R11 |
| A8 | ![Gray](docs/wire-colors/gray.svg) | 22 | GP7 | 10 | R15 |
| A9 | ![White](docs/wire-colors/white.svg) | 23 | GP8 | 11 | R14 |
| A10 | ![Black](docs/wire-colors/black.svg) | 24 | GP9 | 12 | R5 |
| B1 | ![Brown](docs/wire-colors/brown.svg) | 25 | GP10 | 14 | R7 |
| B2 | ![Red](docs/wire-colors/red.svg) | 26 | GP11 | 15 | R6 |
| B3 | ![Orange](docs/wire-colors/orange.svg) | 27 | GP12 | 16 | R3 |
| B4 | ![Yellow](docs/wire-colors/yellow.svg) | 28 | GP13 | 17 | R1 |
| B5 | ![Green](docs/wire-colors/green.svg) | 29 | GP14 | 19 | C0 |
| B6 | ![Blue](docs/wire-colors/blue.svg) | 30 | GP15 | 20 | R2 |
| B7 | ![Purple](docs/wire-colors/purple.svg) | 31 | GP16 | 21 | R4 |
| B8 | ![Gray](docs/wire-colors/gray.svg) | 32 | GP17 | 22 | C2 |
| B9 | ![White](docs/wire-colors/white.svg) | 33 | GP18 | 24 | C5 |
| B10 | ![Black](docs/wire-colors/black.svg) | 34 | GP19 | 25 | R0 |
| C1 | ![Brown](docs/wire-colors/brown.svg) | 35 | GP20 | 26 | C3 |
| C2 | ![Red](docs/wire-colors/red.svg) | 36 | GP21 | 27 | C1 |
| C3 | ![Orange](docs/wire-colors/orange.svg) | 37 | GP22 | 29 | R13 |
| C4 | ![Yellow](docs/wire-colors/yellow.svg) | 38 | GP26 | 31 | C7 |
| C5 | ![Green](docs/wire-colors/green.svg) | 39 | GP27 | 32 | C6 |
| C6 | ![Blue](docs/wire-colors/blue.svg) | 40 | GP28 | 34 | C4 |

Leave **FPC 1–10 and 13–16** and the smaller ribbon disconnected for this keys-only build. None of the matrix wires connects to power, GND, AGND, or RUN. Pico GPIO is 3.3 V only.

### Key matrix

Each key joins one row and one column. For example, **A = R0 + C1 = FPC 34 + 36 = GP19 + GP21**. The table above translates every row and column to a wire. Empty cells have no mapped key.

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

`L`/`R` distinguish left/right modifiers. `Super` is Windows on Windows and Command on macOS. USB reports key positions; the host’s selected keyboard layout determines characters.

### Other connector functions

These are from the [T14 reference](https://github.com/delingren/thinkpad_keyboards/blob/main/t14-v1.md), **not tested or connected here**:

| Contact | Reference function |
| :--- | :--- |
| FPC 1–5 | Not established here; leave disconnected |
| FPC 6 / 7 / 8 | Middle / right / left mouse-button lines |
| FPC 9 | Mouse-button common |
| FPC 10 / 13 / 14 / 15 | Caps Lock / mic mute / speaker mute / Fn Lock LED lines |
| FPC 16 | Indicator common anode (+) |
| Separate 12-pin ribbon | TrackPoint and backlight; pin order and power wiring still need verification |

## Build and test

Use Pico SDK **2.2.0**, an Arm embedded compiler, CMake, and picotool. Set `PICO_SDK_PATH`, then:

```sh
cmake -S . -B build -DPICO_BOARD=pico
cmake --build build
python -m unittest discover -s tests -v
```

| Output | Use |
| :--- | :--- |
| `build/t14_keyboard.uf2` | Everyday USB HID keyboard |
| `build/t14_diagnostics.uf2` | Serial scanner for the [diagnostics app](docs/diagnostics.md) |

The two UF2 files replace one another. Use BOOTSEL to switch or recover; HID mode does not expose COM3. CI builds both UF2s and runs mapping and native keyboard-core tests. The prototype uses TinyUSB’s development VID, not a production USB allocation.

## Reference files

- [Measured key pairs and USB usage codes](docs/verified-keymap.md)
- [Verified hardware report](docs/verified-report.json)
- [Firmware keymap](firmware/keymap.c), [scan and USB code](firmware/keyboard_main.c)
- [Pico physical pinout](https://datasheets.raspberrypi.com/pico/Pico-R3-A4-Pinout.pdf)

`python tools/generate_keymap.py` regenerates the firmware map only when all 84 saved hardware results match. Tests use `--check` to detect drift.

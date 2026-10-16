# T14 Gen 1 keyboard → Raspberry Pi Pico

Convert a ThinkPad T14 Gen 1 keyboard into a USB keyboard using an original
RP2040 Raspberry Pi Pico. The current firmware only prints `Hello, world!` over
USB serial; matrix scanning, key mapping, and a diagnostic GUI are not yet
implemented.

## Color-coded wiring: keys only

**Disconnect USB before wiring. Do not power this wiring until the ribbon's
pin-1 orientation and seating have been verified.**

This plan uses the uncompressed matrix described in the
[T14 keyboard conversion reference](https://github.com/delingren/thinkpad_keyboards/blob/main/t14-v1.md):
connector pins **11, 12, and 17–40**, using all **26 exposed Pico GPIOs**.
The reference author's keyboard is tentatively identified as T14 Gen 1/T490
compatible. This is a reference-based wiring plan, not a pinout measured on our
keyboard yet.

### Wire colors and bundle labels

Use this repeating 10-color order:

![Brown](docs/wire-colors/brown.svg) → ![Red](docs/wire-colors/red.svg) → ![Orange](docs/wire-colors/orange.svg) → ![Yellow](docs/wire-colors/yellow.svg) → ![Green](docs/wire-colors/green.svg) → ![Blue](docs/wire-colors/blue.svg) → ![Purple](docs/wire-colors/purple.svg) → ![Gray](docs/wire-colors/gray.svg) → ![White](docs/wire-colors/white.svg) → ![Black](docs/wire-colors/black.svg)

Rainbow jumper packs do not all use the same order. Select wires by the color
in the table, rather than assuming their position in your strip. Violet means
purple; grey means gray. Here, black is a matrix signal, **not ground**.

Label both ends of three bundles **A**, **B**, and **C** with tape:

- **A:** first 10 wires, brown through black.
- **B:** next 10 wires, brown through black.
- **C:** final 6 wires, brown through blue.

The bundle letter distinguishes repeated colors. For example, **A-blue** and
**B-blue** are different wires.

### Exact connection table

**FPC pin** means the keyboard connector contact number, as carried through to
the breakout's numbered terminal after verifying its orientation. **GP** is the
Pico GPIO label. **Physical pin** is the Pico's 1–40 header position; it is not
the GPIO number.

| Wire ID | Color | Keyboard FPC pin | Pico GPIO | Pico physical pin |
| :--- | :--- | ---: | :--- | ---: |
| A1 | ![Brown](docs/wire-colors/brown.svg) | 11 | GP0 | 1 |
| A2 | ![Red](docs/wire-colors/red.svg) | 12 | GP1 | 2 |
| A3 | ![Orange](docs/wire-colors/orange.svg) | 17 | GP2 | 4 |
| A4 | ![Yellow](docs/wire-colors/yellow.svg) | 18 | GP3 | 5 |
| A5 | ![Green](docs/wire-colors/green.svg) | 19 | GP4 | 6 |
| A6 | ![Blue](docs/wire-colors/blue.svg) | 20 | GP5 | 7 |
| A7 | ![Purple](docs/wire-colors/purple.svg) | 21 | GP6 | 9 |
| A8 | ![Gray](docs/wire-colors/gray.svg) | 22 | GP7 | 10 |
| A9 | ![White](docs/wire-colors/white.svg) | 23 | GP8 | 11 |
| A10 | ![Black](docs/wire-colors/black.svg) | 24 | GP9 | 12 |
| B1 | ![Brown](docs/wire-colors/brown.svg) | 25 | GP10 | 14 |
| B2 | ![Red](docs/wire-colors/red.svg) | 26 | GP11 | 15 |
| B3 | ![Orange](docs/wire-colors/orange.svg) | 27 | GP12 | 16 |
| B4 | ![Yellow](docs/wire-colors/yellow.svg) | 28 | GP13 | 17 |
| B5 | ![Green](docs/wire-colors/green.svg) | 29 | GP14 | 19 |
| B6 | ![Blue](docs/wire-colors/blue.svg) | 30 | GP15 | 20 |
| B7 | ![Purple](docs/wire-colors/purple.svg) | 31 | GP16 | 21 |
| B8 | ![Gray](docs/wire-colors/gray.svg) | 32 | GP17 | 22 |
| B9 | ![White](docs/wire-colors/white.svg) | 33 | GP18 | 24 |
| B10 | ![Black](docs/wire-colors/black.svg) | 34 | GP19 | 25 |
| C1 | ![Brown](docs/wire-colors/brown.svg) | 35 | GP20 | 26 |
| C2 | ![Red](docs/wire-colors/red.svg) | 36 | GP21 | 27 |
| C3 | ![Orange](docs/wire-colors/orange.svg) | 37 | GP22 | 29 |
| C4 | ![Yellow](docs/wire-colors/yellow.svg) | 38 | GP26 | 31 |
| C5 | ![Green](docs/wire-colors/green.svg) | 39 | GP27 | 32 |
| C6 | ![Blue](docs/wire-colors/blue.svg) | 40 | GP28 | 34 |

Pico header positions follow the
[official original Pico pinout](https://datasheets.raspberrypi.com/pico/Pico-R3-A4-Pinout.pdf).
With the Pico's component side facing you and USB at the top, physical pin 1
is at the upper left. The left side counts down from 1 to 20; the right side
counts up from 21 at the bottom to 40 at the top.

### Connector layout, in numerical order

This is a numbered contact list, **not a left/right drawing of your connector**.
Do not infer ribbon orientation from it.

| FPC contacts | Connection |
| :--- | :--- |
| 1–10 | Leave disconnected |
| 11–12 | A1–A2 |
| 13–16 | Leave disconnected |
| 17–24 | A3–A10 |
| 25–34 | B1–B10 |
| 35–40 | C1–C6 |

The 40-pin connector uses 0.5 mm pitch in the reference. The separate 12-pin
TrackPoint/backlight connector uses 1 mm pitch. Leave that separate ribbon
disconnected during initial key mapping. The excluded 40-pin contacts include
mouse-button and indicator connections; they are not extra matrix lines.

### Ribbon seating and electrical checks

1. Unplug USB. Remove the previous sequential FPC 1–26 wiring.
2. Identify the breakout's pin-1 marking and verify how its numbered terminals
   map to the keyboard ribbon contacts. A reversed ribbon changes the mapping;
   connector contact direction varies, so do not assume contacts face up or down.
3. Open the connector latch as intended for that connector. Insert the ribbon
   straight and fully, with exposed copper facing the connector's contacts,
   then secure the latch without forcing it.
   On a ribbon with a blue stiffener behind its exposed pads, the **blue side
   faces away from the metal contacts**. Contacts inside the connector on top
   mean copper up / blue down; contacts on the bottom mean copper down / blue
   up. Do not choose a direction from the latch color or board orientation.
4. Connect the 26 wires using the table. Verify continuity with power removed,
   and check for accidental bridges between adjacent terminals.
5. Verify orientation before powering or running a scanner. A clear photo of
   the breakout's pin-1 marking, ribbon seating, and keyboard ribbon can help;
   continuity checks are needed where the markings do not establish the mapping.

For this passive key-matrix test, do **not** connect a matrix line to Pico GND,
AGND, RUN, ADC_VREF, 3V3, VBUS, or VSYS. Key switches connect pairs of GPIOs.
The Pico uses 3.3 V GPIO and its GPIO inputs are not 5 V tolerant. Power the
Pico through USB once the wiring is verified.

## Mapping and diagnostics status

- Proposed connector-to-GPIO assignment: documented above.
- Actual ribbon orientation, continuity, and key matrix: **not verified yet**.
- Current firmware: USB serial hello-world only; no key scanning or USB HID.
- Planned mapper: scan confirmed matrix wiring, report connector-pin pairs,
  record a label for each key press, and export measured results here.
- Planned GUI: display live presses and releases, guide individual key tests,
  and identify missing, stuck, or ambiguous connections.

Do not combine matrix lines for the initial mapping. The full matrix uses all
26 GPIOs, so TrackPoint communication and LED control need a later wiring
revision or additional hardware.

## Build the current firmware

Install the Pico SDK, CMake, an Arm embedded compiler, and a compatible build
tool. Set `PICO_SDK_PATH` to the SDK directory, then run:

```sh
cmake -S . -B build
cmake --build build
```

The current build produces `build/pico_hello.uf2`. The GitHub Actions workflow
also compiles the project. Flashing this file does not test the keyboard;
it only runs the existing hello-world program.

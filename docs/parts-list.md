# Parts list

## Electronics

| Qty | Part | Notes |
|---|---|---|
| 1 | Arduino Uno R3 | Hangs upside down under the case deck |
| 1 | Adafruit Music Maker shield (VS1053, 3 W amp version, product 1788) | Stacks on the Uno. Its USB and headphone openings are in the case's back wall |
| 1 | Ender-3 V2 display (DWIN DMT48270C043_04WNZ11) with its knob and cable | Flashed with `firmware/drum_player/DWIN_SET` |
| 1 | microSD card for the music | FAT32. Goes in the shield |
| 1 | microSD card for flashing the screen | Any small FAT32 card; only needed to flash it |
| 1 | Regulated 5 V supply, 1 A or more | Wired in; the power jack isn't brought out of the case |
| 1 | 1/4" mono cable | From the case's 1/4" jack to the Donner DDA-80 input |

## Printed

| Qty | Part | File |
|---|---|---|
| 1 | Hood | `cad/stl/drum_case_hood.stl` (STEP: `cad/drum_case_hood.step`). Includes the back wall; print it standing on its back, with supports |
| 1 | Bottom cover | `cad/stl/drum_case_bottom_cover.stl` (STEP: `cad/drum_case_bottom_cover.step`). Print flat, no supports |

## Hardware

| Qty | Part | Use |
|---|---|---|
| 5 | M2.5 x 8 self-tapping screws | Screen board onto its posts |
| 4 | 3 x 6 mm screws (no longer) | Uno onto its standoffs |
| 4 | 3 x 14 mm countersunk wood screws | Bottom cover into the hood: 2 behind the front lip, 2 in the back corners |
| 1 | Switchcraft-style 1/4" mono open-frame jack, 1 kOhm 1/4 W resistor, heat-shrink | The 1/4" hole in the back wall (USB side); see docs/wiring.md |
| 4 | Rubber feet, up to Ø10 mm | Recesses under the bottom cover |

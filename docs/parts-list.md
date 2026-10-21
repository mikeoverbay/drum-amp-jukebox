# Parts list

## Electronics

| Qty | Part | Notes |
|---|---|---|
| 1 | Arduino Uno R3 | Hangs upside down under the case deck |
| 1 | HW-261 "VS1053 MP3 Shield" (red) | Stacks on the Uno. Its headphone and mic jacks come out the case's left side |
| 1 | Ender-3 V2 display (DWIN DMT48270C043_04WNZ11) with its knob and cable | Flashed with `firmware/drum_player/DWIN_SET` |
| 1 | microSD card for the music | FAT32. Goes in the shield |
| 1 | microSD card for flashing the screen | Any small FAT32 card; only needed to flash it |
| 1 | Regulated 5 V supply, 1 A or more | Wired in; the power jack isn't brought out of the case |
| 1 | 3.5 mm stereo to 1/4" cable | From the shield's headphone jack to the Donner DDA-80 input |

## Printed

| Qty | Part | File |
|---|---|---|
| 1 | Hood | `cad/drum_case_hood.step`. Includes the back wall; print it standing on its back, with supports |
| 1 | Bottom cover | `cad/drum_case_bottom_cover.step`. Print flat, no supports |

## Hardware

| Qty | Part | Use |
|---|---|---|
| 5 | M2.5 x 8 self-tapping screws | Screen board onto its posts |
| 4 | 3 x 6 mm screws (no longer) | Uno onto its standoffs |
| 6 | 3 x 14 mm countersunk wood screws | Bottom cover into the hood: 2 front, 2 wing corners, 2 back corners |
| 4 | Rubber feet, up to Ø10 mm | Recesses under the bottom cover |

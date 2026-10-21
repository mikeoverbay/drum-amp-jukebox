# Case: drum-amp-jukebox (Uno + HW-261 VS1053 shield)

This is the case for the drum-amp player: an **Arduino Uno with the red HW-261 VS1053 MP3 shield**, feeding the Donner DDA-80.

From the front it looks like the console case: a vertical front lip, a 30° screen face with the Ender-3 V2 DWIN screen and knob, and a plain flat deck.

**It's T-shaped from above.** The screen part is full width. Behind it, both sides step in to the board's length, so the board's plugs show on both sides:
- **Right step:** the Uno's **USB-B**, flush with the outside. Power comes in by wire.
- **Left step:** the shield's **headphone and mic jacks**, standing 0.5 mm proud of a shallow recess.

**Size:**
- Overall: 169.1 W x 166.9 D x 66.0 H mm, including the 3 mm lip at the back.
- Narrow back: 78.8 mm wide, from 93.8 mm back.

![back](drumcase_tshape_back.svg)

## Files

| File | What it is |
|---|---|
| `drum_case_hood.step` | Hood: the T-shaped shell, screen face, deck, the 4 Uno standoffs, and 2 back pillars |
| `drum_case_tray.step` | Bottom and back wall in one piece, T-shaped like the hood, screwed up into it from below |
| `drum_case_assembly.step` | Both parts, plus the display model, your Uno model (`reference/arduino_uno_r3.step`) and the HW-261 shield model |
| `drum_case.py` | Parametric CadQuery source. Run `python drum_case.py` |
| `vs1053_shield/` | The shield model (made by the 4560 cap session, ±1 mm from photos) |
| `reference/` | The models the script fits against: the Ender-3 V2 display (`DisplayV2.step`) and your Uno (`arduino_uno_r3.step`) |
| `drumcase_tshape*.svg` | Views of the hood |

## Design

- **Screen:** the window, knob hole, posts and encoder pocket are identical to the console's. To install it, take the tray off, feed the board in through the bottom and screw it to the 5 posts with M2.5 x 8 screws.
- **Steps:** the walls where the case steps in sit 9.5 mm behind the screen's parts (`STEP_CLEAR`). That's what lets the screen come off its posts far enough to free the knob shaft, about 15 mm along the face, and then drop out.
- **Uno:** hangs upside down from the deck, low in the case and centred across it, with its USB end to the right and the power-header edge to the front.
  - It hangs on four D-shaped Ø9 mm standoffs, **30 mm long** (`STANDOFF_DROP` adds 25 mm). Each has four 3 mm gussets with 45° undersides up to the deck.
  - The Uno's back is 33 mm up, and the bottom of the shield is 10.3 mm up, 7.3 mm above the tray floor.
  - The hole by the power jack comes from your Uno STEP model.
  - **Screws: 3 x 6 mm** into Ø2.5 x 5.8 mm pilots at the bottom of the standoffs.
  - The board sits 9 mm back from the tightest fit (`UNO_BACK_SHIFT`), so the long front standoffs stay out of the screen's way out.
- **Right step:**
  - The USB-B gets a roomy 15.8 x 15.5 mm opening, 1.5 mm round the body (`USB_CLEAR`), and its face is flush with the outside.
  - The USB-B's size and position come from your Uno STEP model: 12.82 wide x 12.5 tall above the board, centred 35.6 mm from the power edge, sticking out 6.86 mm past the board.
  - No hole for the power jack: power comes in by wire. `BARREL_HOLE = True` adds a Ø10 hole for it.
- **Left step:** moved 1.5 mm out (`LEFT_WIDEN`) so the board ends don't run into it. The Uno's board end clears its inside face by 0.5 mm, the shield's by 1.2 mm.
  - On the outside, a 1.5 mm deep recess with rounded ends wraps both jacks. The jacks stand 0.5 mm proud of its floor, through a 1.5 mm wall.
  - Ø8.8 holes for the two 5.8 mm jack barrels: 1.5 mm all round (`JACK_CLEAR`). That leaves a 1.9 mm web between them.
- **Fitting the board:** the USB and the jack barrels stick through the narrow walls, 3.0 mm on the right and 2.0 mm on the left. **Flex the narrow walls out and pop the board in.**
- **Rounded edges:** every outside edge is rounded: R4 on the corners, the steps and the deck edges, plus the R6 ridge and R3 lip. The bottom edges are R2, because the 3 mm walls only have room for that. Where the steps' rounded inside corners meet the deck, two shallow 13° creases are left.
- **Back lip:** the hood runs 3 mm past the tray's back wall, so the back sits recessed.
- **Tray:** bottom and back wall, T-shaped like the hood. It's held by 6 **3 x 14 mm wood screws** from below, countersunk:
  - 2 into blocks behind the front lip;
  - 2 into blocks in the back corners of the wide part, against the step walls;
  - 2 into the back pillars.
- **Back pillars:** two Ø10 pillars run from the deck down to the tray floor behind the board, 20 mm either side of centre.
  - Each has two 3 mm gussets with 45° undersides along the back wall. There are none toward the board, because they'd hit it.
  - They're 2.9 mm clear of the shield.
- **microSD:** the card goes in from the USB end, but the socket's mouth is 14 mm inside the right step. **Take the tray off to swap the card**; the shield faces down, so it's right there.
- **No vents:** the narrow sides carry the plugs.

## Assembly order

**Screen first, then the Uno.**
1. Fit the screen.
2. Fit the shield on the Uno.
3. Flex the narrow walls and pop the stack in, with the USB-B into the right step and the jacks into the left. Screw it up with the 3 x 6 mm screws.
4. Screw the tray on.

## Checks run

- Both parts are valid single solids.
- No overlaps between the hood, tray, display, Uno and shield, checked against your actual Uno model. The Uno model's header sockets are 0.5 mm taller than real ones, so they overlap the shield's spacers by 0.5 mm in the model only.
- The USB-B face is flush with the outside of the right step, with 1.5 mm round it.
- The jack fronts are 0.5 mm proud of the left recess, with 1.5 mm round them.
- The board is 2.9 mm clear of the back pillars and 7.3 mm above the tray floor.
- The screen's way out is clear: 0.84 mm off the posts and 1.05 mm on the way down.
- The standoff pilots leave at least 4.6 mm of plastic to the outside.
- **Not modelled:** how far the walls actually flex. The board needs 2–3 mm. Print it and try; if it's too stiff, say so and I'll split one narrow side into a screwed-on plate.

## The shield (HW-261 VS1053)

- **Stack:** 22.7 mm from the Uno's back to the bottom of the shield's sockets: the Uno, 11 mm to the shield, and the shield's 8.5 mm sockets.
- **Jacks:** headphone (front) and mic (behind it), with centres 16.3 mm up.
- **Screws:** the shield's own holes aren't on the Uno pattern, so the Uno's 4 holes take the screws.

## Printing

- **Hood:** deck face down on the bed, so the top comes out smooth. Use supports for the slope, the screen posts, the front lip and the side openings. The standoffs, their gussets and the pillars then point up; the gussets' 45° faces need no support.
- **Tray:** bottom down. It needs no supports.

## Hardware

| Use | Parts |
|---|---|
| Display | 5 x M2.5 x 8 self-tapping screws |
| Uno | 4 x 3 x 6 mm screws up into the standoffs (no longer than 6 mm) |
| Tray | 6 x 3 x 14 mm countersunk wood screws (2 front, 2 wing corners, 2 back pillars) |
| Feet | 4 rubber feet, up to Ø10 mm |

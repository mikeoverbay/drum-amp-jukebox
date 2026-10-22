# Wiring

## Shield to Uno

The Adafruit Music Maker shield (the coffee player's board) plugs straight onto the Uno. The sketch uses these pins:

| Uno pin | Music Maker signal |
|---|---|
| D7 | VS1053 CS (command select) |
| D6 | VS1053 DCS (data select) |
| D3 | DREQ |
| D4 | SD card CS |
| D11 / D12 / D13 | SPI MOSI / MISO / SCK |

There's no reset pin. The firmware starts the VS1053 first, then the SD card.

**Nothing else may use D3, D4, D6 or D7.** On the earlier HW-261 build the knob was soldered to the shield's pins: turning or pressing it hit the VS1053 and SD card, so the card or chip failed at start-up at random.

(The red HW-261 shield, which used reset 8, CS 6, DCS 7, DREQ 2 and SD CS 9, has been dropped.)

## Screen (Ender-3 V2 DWIN) to Uno

| Screen | Uno | Notes |
|---|---|---|
| 5V | 5V | |
| GND | GND | |
| TX (screen out) | D0 (RX) | 500000 baud. The screen's `T5UIC1.CFG` is set to 489600, about 2% off and within tolerance |
| RX (screen in) | D1 (TX) | |
| Knob A | A0 | Pin-change interrupt |
| Knob B | A1 | |
| Knob push (ENT) | A2 | Hold 1 s to pause |
| Knob common | GND | No resistors: the sketch turns on the Uno's pull-ups |

- **Upload:** D0/D1 belong to the screen, so **unplug the screen's TX/RX wires to upload**, then plug them back in. The Uno sometimes needs a reset at the right moment for the upload to catch.
- **No screen:** set `hasScreen = false` in the sketch. It then auto-plays, the knob does volume, next and pause, and the USB Serial Monitor (115200) takes commands. Type `h` for the list.

## Power

- Bring in regulated **5 V, 1 A or more**, by wire to the Uno's 5V and GND. The screen's backlight is the biggest load.
- The Uno's power jack isn't brought out of the case.
- Don't feed 5 V in while the USB cable is plugged in for an upload; unplug one of them.

## Audio

- The shield's **headphone jack** (3.5 mm stereo) goes to the Donner DDA-80 through a 3.5 mm to 1/4" cable.
- **Mono** can be switched in the menu (Mono/Stereo). It's saved in EEPROM.
- **Bass and treble** are in the menu's Tone popup (bass 0-15 dB below 100 Hz, treble -8 to +7 steps of 1.5 dB above 3 kHz). They're saved in EEPROM when you press Done.
- **Caution:** on VS1053 boards the headphone jack's sleeve may be **GBUF** (about 1.25 V), not ground. Don't wire the jack sleeve to the Arduino's ground. Use a cable straight to the amp.

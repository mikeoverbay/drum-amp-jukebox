# drum-amp-jukebox

This is an MP3 jukebox for drumming along. It plays your song library through a **Donner DDA-80** drum amp, and you pick songs on an **Ender-3 V2 DWIN screen** with its knob.

It runs on an **Arduino Uno** with a red **HW-261 VS1053 MP3 shield** and sits in a 3D-printed sloped console case.

![case](cad/drumcase_tshape_back.svg)

## What it does

- **Menu:** Prev, Next, Play Random, Play song, Loop one song, Play Halloween, Volume, Mono/Stereo and Tone. Turn the knob to move, press to choose.
- **Play song:** a full-screen scrolling list of every song.
- **Pause:** hold the knob for 1 s to pause; press again to resume.
- **Settings:** bass and treble (the Tone popup) and mono/stereo are saved in EEPROM.
- **Playing screen:** title, progress bar, time, and a turning reel-to-reel animation.

## Repo layout

| Folder | What's in it |
|---|---|
| [`firmware/hw261_mp3_player/`](firmware/hw261_mp3_player/) | The Arduino sketch, plus the screen's flash set (`DWIN_SET/`) and the button art source (`tone_art/`) |
| [`cad/`](cad/) | The printed case: CadQuery source, STEP files, the shield model and the reference models. See [cad/README.md](cad/README.md) |
| [`sd-card/`](sd-card/) | Tools to build the music card: `MakeSongIndex.ps1`, the `SONG_NAMES.txt` title list, and `PATCHES.BIN` (VLSI VS1053b patches) |
| [`docs/`](docs/) | [Parts list](docs/parts-list.md) and [wiring](docs/wiring.md) |

## Getting it going

1. **Print the case:** see [cad/README.md](cad/README.md). The hood prints standing on its back wall, and the bottom cover is a flat plate.
2. **Flash the screen:**
   1. Copy `firmware/hw261_mp3_player/DWIN_SET/` to the root of a microSD card.
   2. With the screen powered off, insert the card and power it on. It shows blue, then orange when it's done.
   3. Take the card out.
   - Keep the screen's `9.ICO` under about 215 KB, or the screen drops the later icons.
3. **Make the music card:** FAT32, MP3s in the root, plus `PATCHES.BIN`. Then run:

   ```
   powershell -ExecutionPolicy Bypass -File sd-card\MakeSongIndex.ps1 -Drive I:
   ```

   This writes `SONGIDX.TXT`. The titles come from `SONG_NAMES.txt` first, then the MP3 tags.
4. **Upload the sketch:** open `firmware/hw261_mp3_player/hw261_mp3_player.ino` in the Arduino IDE. You need the Adafruit VS1053 and SD libraries; the board is Arduino Uno. **Unplug the screen's D0/D1 wires while uploading.**
5. **Wire it up:** see [docs/wiring.md](docs/wiring.md).

## Status

- The case is designed but not printed yet. Check how far the narrow side walls flex when you pop the board in.
- The firmware runs on the hardware: the menu, Tone popup and playback all work.
- The firmware here is a **copy** of `Documents\Arduino\hw261_mp3_player`, taken 2026-10-21. The drum session still works in the original, so copy its changes in when they land.

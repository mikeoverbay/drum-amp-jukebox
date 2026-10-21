#include <Arduino.h>
#include <SPI.h>
#include <SD.h>
#include <Adafruit_VS1053.h>
#include <EEPROM.h>
#include <avr/pgmspace.h>
// #include "SpectrumPlugin.h" // Analyzer disabled; cannot run with the patches.
// VLSI patches now load from PATCHES.BIN on the SD card (saves ~9 KB of flash).
// VS1053bPatches.h is kept only as the source of that file.
//
// HW-261 copy of coffee_player: the red "VS1053 MP3 Shield" on an Uno,
// same card (SONGIDX.TXT, PATCHES.BIN).
// With the DWIN screen (hasScreen = true): exactly the coffee player, display on D0/D1.
// Without it (hasScreen = false): it starts playing by itself, the knob is turn = volume,
// press = next random song, hold 1 s = pause (press again to resume), and USB Serial
// (115200) shows what plays and takes commands; type h for the list.

// HW-261 pins: X-RESET 8, X-CS 6, X-DCS 7, DREQ 2, SD CS 9 (SPI on D11-D13).
const uint8_t CARD_CS = 9;
Adafruit_VS1053_FilePlayer player(8, 6, 7, 2, CARD_CS);
// Runtime setting: false for no screen (D0/D1 then go to the USB Serial Monitor).
bool hasScreen = true;
uint16_t songCount = 0;
bool monoOutput = true; // Runtime setting; change with setMono().
// Volume 0-20, 20 = loudest. Runtime setting; change with setVolumeLevel().
const uint8_t VOLUME_MAX = 20;
uint8_t volumeLevel = VOLUME_MAX;
// Tone, saved in EEPROM. Bass boost 0-15 dB below 100 Hz; treble -8..7 steps of
// 1.5 dB above 3 kHz. Runtime settings; change with setTone().
const uint8_t BASS_MAX = 15;
const int8_t TREBLE_MIN = -8, TREBLE_MAX = 7;
uint8_t bassLevel = 0;
int8_t trebleLevel = 0;
// SONGIDX.TXT, built by MakeSongIndex.ps1. 64-byte records:
// 8.3 name padded to 12 + '|' + display name padded to 50 + LF.
const char SONG_INDEX[] = "/SONGIDX.TXT";
const char PATCH_FILE[] = "/PATCHES.BIN";
const uint8_t NAME_BYTES = 12;
const uint8_t TITLE_BYTES = 50;
const uint8_t RECORD_BYTES = 64;
const uint32_t SONG_LIST_START = 0; // First filename byte; adjust only for a header.
uint32_t listStart = 0;

const uint16_t INTER_TRACK_GAP_MS = 150;
int32_t lastSong = -1;

// What plays next. Runtime setting; change with setSongMode().
enum SongMode : uint8_t { MODE_RANDOM, MODE_LOOP_ONE, MODE_HALLOWEEN };
uint8_t songMode = MODE_RANDOM;
int32_t chosenSong = -1; // MODE_RANDOM: play once next. MODE_LOOP_ONE: the song to loop.
// Runtime setting: false waits at boot until a menu choice starts the music.
bool autoStart = !hasScreen; // No screen: no menu to start it from.
bool playbackOn = false; // Set by the first menu choice (or autoStart).
const char LOOP_FILE[] = "HAUNTED1.MP3";
const char LOOP_TITLE[] = "Scary Halloween sounds";
// const uint16_t frequencies[8] = {63, 125, 250, 500, 1000, 2000, 4000, 8000};

void halt(const __FlashStringHelper *message);
void waitReady();
void writeReg(uint8_t reg, uint16_t value);
uint16_t readReg(uint8_t reg);
void writeMemory(uint16_t address, uint16_t value);
uint16_t readMemory(uint16_t address);
bool loadPatches();
void applyPlayMode();
void setMono(bool on);
void setVolumeLevel(uint8_t level);
void setTone(int16_t bass, int16_t treble);
void saveTone();
void setSongMode(uint8_t mode, int32_t song);
void playPrevious();
bool findSong(uint16_t wanted, char *name, char *title);
void trimRight(char *s, uint8_t len);
// Title of the song playing now (or the boot message), redrawn when the list closes.
char currentTitle[51] = "Ready. Pick from the menu.";
void setup();
void loop();

// Without the screen, D0/D1 are free and the USB Serial Monitor gets the debug text.
bool DEBUG_SERIAL = !hasScreen;
template <typename T> void dbg(T v) { if (DEBUG_SERIAL) Serial.print(v); }
template <typename T> void dbgln(T v) { if (DEBUG_SERIAL) Serial.println(v); }
template <typename T> void dbgln(T v, int format) { if (DEBUG_SERIAL) Serial.println(v, format); }

// Ender-3 V2 DWIN display on hardware serial (D0/D1, 500000).
// Frame: 0xAA, command, data, then the 0xCC 0x33 0xC3 0x3C tail.
// Display RX <- Uno D1 (TX), display TX -> Uno D0 (RX).
bool displayOutput = hasScreen; // false: send nothing on D1 (TX).
const uint16_t BLACK = 0x0000;
const uint16_t WHITE = 0xFFFF;
const uint16_t GREEN = 0x07E0;
const uint8_t SPLASH_ORIENTATION = 1;
const uint8_t TEXT_ORIENTATION = 0;
const unsigned long SPLASH_MS = 3000;
const uint8_t FONT_ID = 3; // 12 x 24 pixels, 40 characters across. 2 = 10x20, 4 = 14x28, 5 = 16x32, 6 = 20x40.
const uint16_t HILITE = 0xFD20; // Orange: selected menu item.
const uint16_t EDITING = GREEN; // Item being changed with the knob.
// Screen layout (480 x 272). Left: title (2 lines), progress bar, time, song picker.
// Right: menu panel, one item per row.
const uint8_t TITLE_FONT = 2;    // 10 x 20: one size below the main font.
const uint8_t LEFT_CHARS = 28;  // Title characters per line in the left area.
const uint16_t TEXT_X = 10;
const uint16_t TITLE_Y = 10;
const uint16_t TITLE_Y2 = 34;
const uint16_t BAR_X = 10;
const uint16_t BAR_Y = 66;
const uint16_t BAR_W = 270;
const uint16_t BAR_H = 12;
const uint16_t TIME_Y = 88;
const uint16_t PICK_Y = 200;
const uint16_t LEFT_RIGHT = 289; // Last pixel column of the left area.
// Teak reel-to-reel under the time (12 frames, 200 x 96), reels turn while playing.
// Menu buttons and reel frames are one library, 9.ICO on the display, in place of
// Creality's stock icons (the bank the stock firmware uses, known to work).
// Icons: 0-18 and 31-32 coffee player buttons (unused here), 19-30 reels, 33-63 this
// player's smaller buttons and Tone popup (drum_player\tone_art\make_tone_art.py).
const uint8_t CD_LIB = 9;
const uint8_t CD_FIRST_ICON = 19;
const uint8_t CD_FRAMES = 12;
const uint16_t CD_W = 200;
const uint16_t CD_X = (LEFT_RIGHT + 1 - CD_W) / 2;
const uint16_t CD_Y = 166;
const unsigned long CD_FRAME_MS = 80; // About 3 s per turn of a reel.
const uint16_t PANEL_X = 298;
const uint16_t PANEL_ROW = 33;   // Buttons 29 high + 4 gap: 8 rows fit the 272-pixel screen.
const uint16_t PANEL_GAP = 5;    // Space between Prev and Next; text buttons are ROW - GAP high.
const uint16_t PANEL_Y = 4;
const uint16_t PANEL_HALF = (479 - PANEL_X - PANEL_GAP) / 2; // Width of Prev and Next.
// Menu buttons as pictures from 9.ICO on the display (see tone_art\make_tone_art.py).
// Runtime setting: false draws plain text buttons, for a display without our 9.ICO.
bool panelIcons = true;
const uint8_t MENU_LIB = 9;
// Icon widths must be even: the display garbles odd-width icons (89 did, 88 is fine).
const uint8_t MENU_ICON_BASE = 33;  // Normal = base + 2 * item, highlighted = + 1.
const uint8_t ICON_EDIT_PLAY = 51;  // Editing states.
const uint8_t ICON_EDIT_LOOP = 52;
const uint8_t ICON_EDIT_VOLUME = 53;
const uint8_t ICON_STEREO = 54;     // The Mono item's picture when stereo; highlighted = + 1.
const uint8_t ICON_TONE_ROW = 56;   // Popup rows: Bass 56, Treble 59 (normal, highlighted,
                                    // editing), Done 62 (normal, highlighted).
const uint16_t ART_ORANGE = 0xCAA0; // Burnt orange, as in the button art.

bool displayOn() { return displayOutput && !DEBUG_SERIAL; }

void dwinStart(uint8_t command) {
  Serial.write(uint8_t(0xAA));
  Serial.write(command);
}

void dwinWord(uint16_t value) {
  Serial.write(uint8_t(value >> 8));
  Serial.write(uint8_t(value));
}

void dwinEnd() {
  const uint8_t tail[] = {0xCC, 0x33, 0xC3, 0x3C};
  Serial.write(tail, sizeof(tail));
  Serial.flush();
  // Give the display 5 ms per command, but keep audio fed meanwhile.
  unsigned long started = millis();
  while (millis() - started < 5) player.feedBuffer();
}

void dwinRefresh() {
  dwinStart(0x3D);
  dwinEnd();
}

void dwinOrientation(uint8_t direction) {
  dwinStart(0x34);
  Serial.write(uint8_t(0x5A));
  Serial.write(uint8_t(0xA5));
  Serial.write(direction);
  dwinEnd();
}

void dwinClear(uint16_t color) {
  dwinStart(0x01);
  dwinWord(color);
  dwinEnd();
}

// filled: 1 = solid, 0 = outline.
void dwinRect(uint8_t filled, uint16_t color, uint16_t x1, uint16_t y1, uint16_t x2, uint16_t y2) {
  dwinStart(0x05);
  Serial.write(filled);
  dwinWord(color);
  dwinWord(x1);
  dwinWord(y1);
  dwinWord(x2);
  dwinWord(y2);
  dwinEnd();
}

void dwinTextFont(uint8_t font, uint16_t x, uint16_t y, const char *text, uint16_t fg, uint16_t bg) {
  dwinStart(0x11);
  Serial.write(uint8_t(0x40 | font)); // 0x40: fill the background behind each character.
  dwinWord(fg);
  dwinWord(bg);
  dwinWord(x);
  dwinWord(y);
  Serial.print(text);
  dwinEnd();
}

void dwinTextColor(uint16_t x, uint16_t y, const char *text, uint16_t fg, uint16_t bg) {
  dwinStart(0x11);
  Serial.write(uint8_t(0x40 | FONT_ID)); // 0x40: fill the background behind each character.
  dwinWord(fg);
  dwinWord(bg);
  dwinWord(x);
  dwinWord(y);
  Serial.print(text);
  dwinEnd();
}

// Icon id from library lib (N.ICO on the display), drawn as-is with its background.
void dwinIcon(uint8_t lib, uint8_t id, uint16_t x, uint16_t y) {
  dwinStart(0x23);
  dwinWord(x);
  dwinWord(y);
  Serial.write(uint8_t(0x80 | (lib & 0x1F))); // Bit 7: show the icon's own background.
  Serial.write(id);
  dwinEnd();
}

// Text with no background: only the letters are drawn, over whatever is there.
void dwinTextClear(uint16_t x, uint16_t y, const char *text, uint16_t fg) {
  dwinStart(0x11);
  Serial.write(FONT_ID); // Bit 6 clear: no background.
  dwinWord(fg);
  dwinWord(BLACK);
  dwinWord(x);
  dwinWord(y);
  Serial.print(text);
  dwinEnd();
}

void dwinText(uint16_t x, uint16_t y, const char *text) {
  dwinTextColor(x, y, text, WHITE, BLACK);
}

// Handshake (0x00): the display answers AA 00 'O' 'K' CC 33 C3 3C once it is up.
// Sends it every 100 ms until "OK" comes back or timeoutMs passes.
bool waitForDisplay(unsigned long timeoutMs) {
  if (!displayOn()) return false;
  unsigned long started = millis();
  unsigned long sent = 0;
  bool sawO = false;
  while (millis() - started < timeoutMs) {
    if (sent == 0 || millis() - sent >= 100) {
      while (Serial.available()) Serial.read(); // Drop anything stale.
      dwinStart(0x00);
      dwinEnd();
      sent = millis();
      sawO = false;
    }
    while (Serial.available()) {
      char c = Serial.read();
      if (sawO && c == 'K') return true;
      sawO = c == 'O';
    }
  }
  return false; // No answer: carry on anyway.
}

// Boot picture stored in the display (image 0), as on the Mega test sketch.
void showSplash() {
  if (!displayOn()) return;
  dwinOrientation(SPLASH_ORIENTATION);
  dwinStart(0x22);
  dwinWord(0);
  dwinEnd();
  delay(400);
  dwinRefresh();
}

void drawPanel(); // Menu panel, defined with the menu below.

void displayInit() {
  if (!displayOn()) return;
  dwinOrientation(TEXT_ORIENTATION);
  dwinClear(BLACK);
  drawPanel();
}

// Up to two lines of LEFT_CHARS, breaking at a space when possible.
void drawWrapped(uint16_t y1, uint16_t y2, const char *text) {
  char line[LEFT_CHARS + 1];
  uint8_t len = strlen(text);
  uint8_t cut = len;
  uint8_t next = len;
  if (len > LEFT_CHARS) {
    cut = next = LEFT_CHARS;
    for (uint8_t i = LEFT_CHARS; i > LEFT_CHARS / 2; i--) {
      if (text[i] == ' ') { cut = i; next = i + 1; break; }
    }
  }
  memcpy(line, text, cut);
  line[cut] = 0;
  dwinTextFont(TITLE_FONT, TEXT_X, y1, line, WHITE, BLACK);
  strncpy(line, text + next, LEFT_CHARS);
  line[LEFT_CHARS] = 0;
  if (line[0]) dwinTextFont(TITLE_FONT, TEXT_X, y2, line, WHITE, BLACK);
}

// Progress bar state for the current track.
uint32_t trackBytes = 0;
uint16_t barDrawn = 0;      // Filled width in pixels.
uint16_t shownSecs = 0xFFFF;
unsigned long lastProgress = 0;

// One-line hint under the time, 10 x 20 font.
const uint16_t HINT_Y = 124;
const uint16_t HINT_GREY = 0xC618; // Light grey: brighter than before, still quieter than white.

void drawHint(bool paused) {
  dwinRect(1, BLACK, 0, HINT_Y, LEFT_RIGHT, HINT_Y + 19);
  if (!playbackOn) return; // Nothing playing: no hint.
  dwinTextFont(2, TEXT_X, HINT_Y, paused ? "Press knob to resume" : "Hold knob 1 sec to pause",
               HINT_GREY, BLACK);
}

void displayTrack(const char *name) {
  barDrawn = 0;
  shownSecs = 0xFFFF;
  if (!displayOn()) return;
  dwinRect(1, BLACK, 0, 0, LEFT_RIGHT, CD_Y - 2); // Title, bar and time; the CD keeps spinning.
  drawWrapped(TITLE_Y, TITLE_Y2, name);
  dwinRect(0, WHITE, BAR_X, BAR_Y, BAR_X + BAR_W + 1, BAR_Y + BAR_H);
  drawHint(false);
  dwinRefresh();
}

// Writes m:ss and returns the end of the text.
char *formatTime(char *p, uint32_t secs) {
  utoa(secs / 60, p, 10);
  p += strlen(p);
  *p++ = ':';
  *p++ = '0' + (secs % 60) / 10;
  *p++ = '0' + secs % 10;
  *p = 0;
  return p;
}

// Once a second: grow the bar and redraw "position / length".
void updateProgress() {
  if (!displayOn() || player.stopped() || millis() - lastProgress < 1000) return;
  lastProgress = millis();
  uint16_t secs = readReg(VS1053_REG_DECODETIME);
  if (secs == shownSecs) return;
  shownSecs = secs;
  uint16_t rate = readMemory(0x1E05); // Average bytes per second of this stream.
  uint32_t total = rate ? trackBytes / rate : 0;
  if (total) {
    uint32_t px = uint32_t(secs) * BAR_W / total;
    if (px > BAR_W) px = BAR_W;
    if (px > barDrawn) {
      dwinRect(1, GREEN, BAR_X + 1 + barDrawn, BAR_Y + 1, BAR_X + px, BAR_Y + BAR_H - 1);
      barDrawn = px;
    }
  }
  char text[20];
  char *p = formatTime(text, secs);
  strcpy_P(p, PSTR(" / "));
  p = formatTime(p + 3, total);
  strcpy_P(p, PSTR("   ")); // Covers a longer previous time.
  dwinText(TEXT_X, TIME_Y, text);
  dwinRefresh();
}

// Rotary encoder on the display board, common to GND:
// A -> A0 (PC0), B -> A1 (PC1), push (ENT) -> A2 (PC2).
const uint8_t ENCODER_STEPS_PER_DETENT = 4;
const bool ENCODER_REVERSED = false; // Flip if turning right goes backwards.
volatile int8_t encoderSteps = 0;
volatile uint8_t encoderLast = 0;

// Pin-change interrupt for A0/A1: never misses steps while the SD card is busy.
ISR(PCINT1_vect) {
  // Quadrature table: +1, -1 or 0 for each (previous, current) A/B state.
  static const int8_t table[16] = {0, -1, 1, 0, 1, 0, 0, -1, -1, 0, 0, 1, 0, 1, -1, 0};
  uint8_t now = PINC & 0x03;
  encoderSteps += table[(encoderLast << 2) | now];
  encoderLast = now;
}

void encoderBegin() {
  pinMode(A0, INPUT_PULLUP);
  pinMode(A1, INPUT_PULLUP);
  pinMode(A2, INPUT_PULLUP);
  encoderLast = PINC & 0x03;
  PCMSK1 |= _BV(PCINT8) | _BV(PCINT9);
  PCICR |= _BV(PCIE1);
}

// Whole detents turned since the last call; positive is clockwise.
int8_t encoderTake() {
  noInterrupts();
  int8_t detents = encoderSteps / ENCODER_STEPS_PER_DETENT;
  encoderSteps -= detents * ENCODER_STEPS_PER_DETENT;
  interrupts();
  return ENCODER_REVERSED ? -detents : detents;
}

// True once per press, debounced.
// Button events. The pin must read the same for 30 ms before it counts, so a noise
// blip (for example while the knob is turning) is not a press.
// BTN_SHORT: released before LONG_PRESS_MS. BTN_LONG: held that long (sent once,
// while still held; the release after it is ignored).
enum ButtonEvent : uint8_t { BTN_NONE, BTN_SHORT, BTN_LONG };
const unsigned long LONG_PRESS_MS = 1000;

uint8_t buttonEvent() {
  static bool stable = false;   // Debounced state.
  static bool lastRead = false;
  static bool longSent = false;
  static unsigned long since = 0;
  static unsigned long downAt = 0;
  bool down = !(PINC & _BV(2));
  if (down != lastRead) {
    lastRead = down;
    since = millis();
    return BTN_NONE;
  }
  if (down != stable && millis() - since >= 30) {
    stable = down;
    if (down) {
      downAt = millis();
      longSent = false;
      return BTN_NONE;
    }
    return longSent ? BTN_NONE : BTN_SHORT; // Released.
  }
  if (stable && !longSent && millis() - downAt >= LONG_PRESS_MS) {
    longSent = true;
    return BTN_LONG;
  }
  return BTN_NONE;
}

// Menu panel on the right. Turning moves the highlight; the button commits.
enum MenuState : uint8_t { MENU_MAIN, MENU_PICK, MENU_VOLUME, MENU_TONE };
// Prev and Next share the top row; every other item has a row of its own.
enum MenuItem : uint8_t {
  ITEM_PREV, ITEM_NEXT, ITEM_RANDOM, ITEM_PLAY, ITEM_LOOP, ITEM_HALLOWEEN, ITEM_VOLUME, ITEM_MONO,
  ITEM_TONE, ITEM_COUNT
};
const char ITEM_TEXT[ITEM_COUNT][15] PROGMEM = {
  "<< Prev", "Next >>", "Play Random", "Play song", "Loop one song", "Play Halloween",
  "Volume ", "Mono ", "Tone"
};
const unsigned long PICK_TIMEOUT_MS = 30000; // Song list closes after this long idle.
uint8_t menuState = MENU_MAIN;
uint8_t menuItem = ITEM_RANDOM;
uint16_t pickSong = 0;  // Song shown while picking.
bool pickToLoop = false;
unsigned long menuTouched = 0;

// The item for the mode that is playing now, shown in green.
// A song chosen with "Play song" is playing (shuffle resumes after it).
bool playingPick = false;

uint8_t activeItem() {
  if (!playbackOn) return ITEM_COUNT; // Nothing playing: no dot anywhere.
  if (songMode == MODE_LOOP_ONE) return ITEM_LOOP;
  if (songMode == MODE_HALLOWEEN) return ITEM_HALLOWEEN;
  return playingPick ? ITEM_PLAY : ITEM_RANDOM;
}

void drawItem(uint8_t item) {
  uint8_t row = item <= ITEM_NEXT ? 0 : item - ITEM_NEXT;
  uint16_t y = PANEL_Y + row * PANEL_ROW;
  uint16_t x1 = item == ITEM_NEXT ? PANEL_X + PANEL_HALF + PANEL_GAP : PANEL_X;
  uint16_t x2 = item == ITEM_PREV ? PANEL_X + PANEL_HALF : 479;
  bool selected = item == menuItem;
  bool editing = selected && menuState != MENU_MAIN;
  if (panelIcons) {
    // Button picture from 9.ICO; only the changing values are drawn as text.
    uint8_t id = MENU_ICON_BASE + item * 2 + (selected ? 1 : 0);
    if (editing) id = item == ITEM_PLAY ? ICON_EDIT_PLAY : item == ITEM_LOOP ? ICON_EDIT_LOOP : ICON_EDIT_VOLUME;
    if (item == ITEM_MONO && !monoOutput) id = ICON_STEREO + (selected ? 1 : 0); // Picture shows the setting.
    dwinIcon(MENU_LIB, id, x1, y);
    if (item == ITEM_VOLUME) { // White and bold: drawn twice, one pixel apart, no background.
      char value[4];
      utoa(volumeLevel, value, 10);
      uint16_t vx = x2 - 14 - strlen(value) * 12;
      dwinTextClear(vx, y + 3, value, WHITE);
      dwinTextClear(vx + 1, y + 3, value, WHITE);
    }
    if (item == activeItem()) dwinRect(1, GREEN, x2 - 14, y + 11, x2 - 8, y + 17); // Playing now.
    return;
  }
  uint16_t bg = editing ? EDITING : selected ? HILITE : BLACK;
  uint16_t fg = selected ? BLACK : item == activeItem() ? GREEN : WHITE;
  char text[16];
  strcpy_P(text, ITEM_TEXT[item]);
  if (item == ITEM_VOLUME) utoa(volumeLevel, text + strlen(text), 10);
  if (item == ITEM_MONO) strcat_P(text, monoOutput ? PSTR("On") : PSTR("Off"));
  dwinRect(1, bg, x1, y, x2, y + PANEL_ROW - PANEL_GAP);
  dwinTextColor(x1 + 6, y + 4, text, fg, bg);
}

void drawPanel() {
  if (!displayOn()) return;
  for (uint8_t i = 0; i < ITEM_COUNT; i++) drawItem(i);
  dwinRefresh();
}

// Tone popup over the left side: Bass, Treble, Done. Turning moves the highlight;
// pressing Bass or Treble edits it (turn changes it, press again stops), Done closes.
const uint16_t TONE_X1 = 40, TONE_Y1 = 60, TONE_X2 = 250, TONE_Y2 = 214;
const uint16_t TONE_BG = 0x10C4; // Near-black blue-grey.
const uint16_t TONE_BTN_X = TONE_X1 + (TONE_X2 - TONE_X1 - 182) / 2;
enum ToneRow : uint8_t { TONE_BASS, TONE_TREBLE, TONE_DONE, TONE_ROWS };
uint8_t toneRow = TONE_BASS;
bool toneEditing = false;

// The left side is covered (song list or Tone popup): leave title, bar, time and reels alone.
bool leftCovered() { return menuState == MENU_PICK || menuState == MENU_TONE; }

void drawToneRow(uint8_t row) {
  uint16_t y = TONE_Y1 + 34 + row * PANEL_ROW;
  bool selected = row == toneRow;
  if (!panelIcons) {
    char text[12];
    strcpy_P(text, row == TONE_BASS ? PSTR("Bass ") : row == TONE_TREBLE ? PSTR("Treble ") : PSTR("Done"));
    if (row != TONE_DONE) itoa(row == TONE_BASS ? bassLevel : trebleLevel, text + strlen(text), 10);
    uint16_t bg = selected && toneEditing ? EDITING : selected ? HILITE : BLACK;
    dwinRect(1, bg, TONE_BTN_X, y, TONE_BTN_X + 181, y + PANEL_ROW - PANEL_GAP);
    dwinTextColor(TONE_BTN_X + 6, y + 2, text, selected ? BLACK : WHITE, bg);
    return;
  }
  uint8_t id = ICON_TONE_ROW + row * 3 + (selected ? (toneEditing ? 2 : 1) : 0);
  dwinIcon(MENU_LIB, id, TONE_BTN_X, y);
  if (row == TONE_DONE) return;
  char value[4];
  itoa(row == TONE_BASS ? bassLevel : trebleLevel, value, 10);
  uint16_t vx = TONE_BTN_X + 182 - 14 - strlen(value) * 12;
  dwinTextClear(vx, y + 3, value, WHITE);
  dwinTextClear(vx + 1, y + 3, value, WHITE);
}

void openTone() {
  toneRow = TONE_BASS;
  toneEditing = false;
  if (!displayOn()) return;
  dwinRect(1, TONE_BG, TONE_X1, TONE_Y1, TONE_X2, TONE_Y2);
  dwinRect(0, ART_ORANGE, TONE_X1, TONE_Y1, TONE_X2, TONE_Y2);
  dwinRect(0, ART_ORANGE, TONE_X1 + 1, TONE_Y1 + 1, TONE_X2 - 1, TONE_Y2 - 1);
  dwinTextColor((TONE_X1 + TONE_X2) / 2 - 24, TONE_Y1 + 4, "Tone", ART_ORANGE, TONE_BG);
  for (uint8_t i = 0; i < TONE_ROWS; i++) drawToneRow(i);
  dwinRefresh();
}

// Song picker: a scrolling list that fills the whole screen.
const uint8_t LIST_FONT = FONT_ID;  // 12 x 24, same as the title text.
const uint8_t LIST_ROWS = 9;        // 9 rows of 30 pixels = 270.
const uint16_t LIST_ROW_H = 30;
const uint8_t LIST_CHARS = 39;      // Characters that fit across the screen at 12 pixels each.
uint16_t listTop = 0;               // Song shown in the top row.
// SONGIDX.TXT, opened once at boot and never closed. Opening a file searches the
// card's root folder (hundreds of long-name entries), which starved the audio.
File songIndex;
const uint16_t LIST_BG = 0x2124;    // Near-black grey, RGB 0.15 (38, 38, 38); 0.33 looked too bright.

// One row: white text on dark grey; the song under the knob gets an orange bar.
void drawListRow(File &list, uint16_t song) {
  player.feedBuffer(); // Keep the music fed between rows.
  uint16_t y = (song - listTop) * LIST_ROW_H;
  char title[TITLE_BYTES + 1];
  int n = 0;
  if (list.seek(listStart + uint32_t(song) * RECORD_BYTES + NAME_BYTES + 1))
    n = list.read(title, TITLE_BYTES);
  trimRight(title, n > 0 ? n : 0);
  title[LIST_CHARS] = 0;
  bool selected = song == pickSong;
  uint16_t bg = selected ? ART_ORANGE : LIST_BG;
  dwinRect(1, bg, 0, y, 479, y + LIST_ROW_H - 1);
  dwinTextFont(LIST_FONT, 4, y + 3, title, WHITE, bg); // White on every row.
}

// Whole list from listTop down.
void drawList() {
  if (!displayOn()) return;
  dwinRect(1, LIST_BG, 0, 0, 479, 271);
  if (songIndex) {
    for (uint16_t s = listTop; s < listTop + LIST_ROWS && s < songCount; s++) drawListRow(songIndex, s);
  }
  dwinRefresh();
}

// Open the list with the current song (or the first) highlighted, near the middle.
void openPicker() {
  pickSong = lastSong >= 0 ? lastSong : 0;
  listTop = pickSong > LIST_ROWS / 2 ? pickSong - LIST_ROWS / 2 : 0;
  if (songCount > LIST_ROWS && listTop > songCount - LIST_ROWS) listTop = songCount - LIST_ROWS;
  drawList();
}

// Move the highlight; scroll only when it would leave the screen.
void movePick(int8_t turn) {
  uint16_t old = pickSong;
  pickSong = (int32_t(pickSong) + turn % int16_t(songCount) + songCount) % songCount;
  if (pickSong < listTop) {
    listTop = pickSong;
    drawList();
  } else if (pickSong >= listTop + LIST_ROWS) {
    listTop = pickSong - LIST_ROWS + 1;
    drawList();
  } else if (displayOn()) { // Same page: just repaint the two rows that changed.
    if (songIndex) {
      drawListRow(songIndex, old);
      drawListRow(songIndex, pickSong);
    }
    dwinRefresh();
  }
}

// Back to the normal screen: menu panel, title, progress bar, time (the CD redraws itself).
void closePicker() {
  if (!displayOn()) return;
  dwinRect(1, BLACK, 0, 0, 479, 271);
  drawPanel();
  displayTrack(currentTitle);
}

// Pause (button held): the decoder simply stops being fed, so the song keeps its place.
uint8_t pausedItem = ITEM_COUNT; // Menu item highlighted when it paused.
const uint16_t PAUSED_X = 180;   // "PAUSED" sits right of the time.

void showPaused(bool on) {
  if (!displayOn() || leftCovered()) return;
  if (on) dwinTextColor(PAUSED_X, TIME_Y, "PAUSED", ART_ORANGE, BLACK);
  else dwinRect(1, BLACK, PAUSED_X, TIME_Y, LEFT_RIGHT, TIME_Y + 23);
  drawHint(on);
  dwinRefresh();
}

void pausePlayback() {
  if (!playbackOn || player.stopped() || player.paused()) return;
  player.pausePlaying(true);
  pausedItem = menuItem;
  showPaused(true);
}

void resumePlayback() {
  player.pausePlaying(false);
  showPaused(false);
}

void menuUpdate() {
  static unsigned long lastTurn = 0;
  int8_t turn = encoderTake();
  uint8_t button = buttonEvent();
  if (button == BTN_LONG) { // Hold: pause whatever is playing.
    menuTouched = millis();
    pausePlayback();
    return;
  }
  bool press = button == BTN_SHORT;
  if (turn) lastTurn = millis();
  if (press && millis() - lastTurn < 200) press = false; // Not while the knob is moving.
  if (!turn && !press) {
    if (menuState == MENU_PICK && millis() - menuTouched > PICK_TIMEOUT_MS) {
      menuState = MENU_MAIN;
      closePicker();
    }
    return;
  }
  menuTouched = millis();
  if (!displayOn()) { // No screen: turn = volume, press = next song (or resume when paused).
    if (turn) {
      setVolumeLevel(constrain(int16_t(volumeLevel) + turn, 0, VOLUME_MAX));
      dbg(F("Volume "));
      dbgln(volumeLevel);
    }
    if (press) {
      if (player.paused()) resumePlayback();
      else setSongMode(MODE_RANDOM, -1);
    }
    return;
  }
  switch (menuState) {
    case MENU_MAIN:
      if (turn) {
        uint8_t old = menuItem;
        menuItem = (menuItem + turn % ITEM_COUNT + ITEM_COUNT) % ITEM_COUNT;
        drawItem(old);
        drawItem(menuItem);
        dwinRefresh();
      }
      if (!press) return;
      // Paused and still on the item that was highlighted when it paused: carry on.
      if (player.paused() && menuItem == pausedItem) {
        resumePlayback();
        return;
      }
      switch (menuItem) {
        case ITEM_PREV: playPrevious(); break;
        case ITEM_NEXT: setSongMode(MODE_RANDOM, -1); break; // Leaves loop modes too.
        case ITEM_RANDOM: setSongMode(MODE_RANDOM, -1); break;
        case ITEM_PLAY:
        case ITEM_LOOP:
          pickToLoop = menuItem == ITEM_LOOP;
          menuState = MENU_PICK;
          openPicker();
          break;
        case ITEM_HALLOWEEN: setSongMode(MODE_HALLOWEEN, -1); break;
        case ITEM_VOLUME: menuState = MENU_VOLUME; break;
        case ITEM_MONO: setMono(!monoOutput); break;
        case ITEM_TONE:
          menuState = MENU_TONE;
          openTone();
          return; // The panel stays as it is.
      }
      if (menuState != MENU_PICK) drawPanel(); // The song list now covers the screen.
      break;
    case MENU_PICK:
      if (turn) movePick(turn);
      if (press) {
        // Close first, so the new song's title draws on the normal screen.
        menuState = MENU_MAIN;
        setSongMode(pickToLoop ? MODE_LOOP_ONE : MODE_RANDOM, pickSong);
        playingPick = !pickToLoop; // Dot on "Play song" until shuffle takes over.
        closePicker(); // Redraws the panel too, with the new mode marked.
      }
      break;
    case MENU_VOLUME:
      if (turn) setVolumeLevel(constrain(int16_t(volumeLevel) + turn, 0, VOLUME_MAX));
      if (press) menuState = MENU_MAIN;
      drawItem(ITEM_VOLUME);
      dwinRefresh();
      break;
    case MENU_TONE:
      if (press && toneRow == TONE_DONE) {
        menuState = MENU_MAIN;
        saveTone(); // Once, when done, not on every click.
        closePicker(); // Same full redraw as after the song list.
        return;
      }
      if (press) toneEditing = !toneEditing;
      if (turn && toneEditing && toneRow == TONE_BASS) setTone(bassLevel + turn, trebleLevel);
      if (turn && toneEditing && toneRow == TONE_TREBLE) setTone(bassLevel, trebleLevel + turn);
      if (turn && !toneEditing) {
        uint8_t old = toneRow;
        toneRow = (toneRow + turn % TONE_ROWS + TONE_ROWS) % TONE_ROWS;
        drawToneRow(old);
      }
      drawToneRow(toneRow);
      dwinRefresh();
      break;
  }
}
void halt(const __FlashStringHelper *message) {
  dbgln(message);
  if (displayOn()) { // Show the error on screen too.
    char text[41];
    strncpy_P(text, (PGM_P)message, sizeof(text) - 1);
    text[sizeof(text) - 1] = 0;
    dwinOrientation(TEXT_ORIENTATION);
    dwinClear(BLACK);
    dwinText(TEXT_X, TITLE_Y, text);
    dwinRefresh();
  }
  while (true) { delay(100); }
}

void waitReady() {
  unsigned long started = millis();
  while (!player.readyForData()) {
    if (millis() - started > 1000) {
      halt(F("ERROR: VS1053 DREQ timeout."));
    }
  }
}

void writeReg(uint8_t reg, uint16_t value) {
  waitReady();
  player.sciWrite(reg, value);
}

uint16_t readReg(uint8_t reg) {
  waitReady();
  return player.sciRead(reg);
}

void writeMemory(uint16_t address, uint16_t value) {
  writeReg(VS1053_REG_WRAMADDR, address);
  writeReg(VS1053_REG_WRAM, value);
}

uint16_t readMemory(uint16_t address) {
  writeReg(VS1053_REG_WRAMADDR, address);
  return readReg(VS1053_REG_WRAM);
}

/* Analyzer disabled.
void loadSpectrum() {
  // Decode VLSI's compressed SCI write table directly from AVR flash.
  uint16_t pos = 0;
  while (pos < sizeof(plugin) / sizeof(plugin[0])) {
    uint16_t reg = pgm_read_word(&plugin[pos++]);
    uint16_t count = pgm_read_word(&plugin[pos++]);
    if (count & 0x8000) {
      count &= 0x7FFF;
      uint16_t value = pgm_read_word(&plugin[pos++]);
      while (count--) writeReg(reg, value);
    } else {
      while (count--) writeReg(reg, pgm_read_word(&plugin[pos++]));
    }
  }

  // Standard spectrumAnalyzer1053b plugin memory map (no other patches).
  for (uint8_t i = 0; i < 8; i++) {
    writeMemory(0x1868 + i, frequencies[i]);
  }
  writeMemory(0x1870, 25000); // End the frequency list after eight bands.
  writeMemory(0x1801, 0);     // Request recalculation for these bands.
}
*/

// VLSI's compressed SCI write table (vs1053b-patches.plg) as little-endian
// words in PATCHES.BIN. The table ends by writing 0x50 to AIADDR, which starts it.
bool loadPatches() {
  File f = SD.open(PATCH_FILE);
  if (!f) return false;
  auto next = [&]() -> uint16_t {
    uint16_t low = f.read();
    return low | uint16_t(f.read()) << 8;
  };
  while (f.available() >= 4) {
    uint16_t reg = next();
    uint16_t count = next();
    if (count & 0x8000) {
      count &= 0x7FFF;
      uint16_t value = next();
      while (count--) writeReg(reg, value);
    } else {
      while (count--) writeReg(reg, next());
    }
  }
  f.close();
  // Starting the patch clears playMode, so set it after every load.
  applyPlayMode();
  return true;
}

void applyPlayMode() {
  // VLSI patches playMode (X:0x1E09): bit 0 = mono downmix. Safe during playback.
  writeMemory(0x1E09, monoOutput ? 0x0001 : 0x0000);
}

// Saved settings live just below the random seed (which uses the last 8 bytes).
// A marker byte says the slot has been written, so a blank EEPROM keeps the defaults.
const int MONO_EEPROM = 1014;        // Marker at 1014, value at 1015.
const int TONE_EEPROM = 1011;        // Marker at 1011, bass at 1012, treble at 1013.
const uint8_t SETTING_MARKER = 0xA5;

void loadSettings() {
  if (EEPROM.read(MONO_EEPROM) == SETTING_MARKER) monoOutput = EEPROM.read(MONO_EEPROM + 1) != 0;
  if (EEPROM.read(TONE_EEPROM) == SETTING_MARKER) {
    bassLevel = constrain(EEPROM.read(TONE_EEPROM + 1), 0, BASS_MAX);
    trebleLevel = constrain(int8_t(EEPROM.read(TONE_EEPROM + 2)), TREBLE_MIN, TREBLE_MAX);
  }
}

void saveTone() {
  EEPROM.update(TONE_EEPROM, SETTING_MARKER);
  EEPROM.update(TONE_EEPROM + 1, bassLevel);
  EEPROM.update(TONE_EEPROM + 2, uint8_t(trebleLevel));
}

// SCI_BASS: treble amplitude (signed, 1.5 dB) | treble from 3 kHz | bass dB | bass below 100 Hz.
void applyTone() {
  writeReg(VS1053_REG_BASS, (uint16_t(trebleLevel & 0x0F) << 12) | (3 << 8) | (bassLevel << 4) | 10);
}

void setTone(int16_t bass, int16_t treble) {
  bassLevel = constrain(bass, 0, BASS_MAX);
  trebleLevel = constrain(treble, TREBLE_MIN, TREBLE_MAX);
  applyTone();
}

void setMono(bool on) {
  monoOutput = on;
  applyPlayMode();
  // update() only writes when the value changes, which saves EEPROM wear.
  EEPROM.update(MONO_EEPROM, SETTING_MARKER);
  EEPROM.update(MONO_EEPROM + 1, on ? 1 : 0);
}

void setVolumeLevel(uint8_t level) {
  volumeLevel = level;
  // VS1053 attenuation in 0.5 dB steps: level 20 = 1 dB down, level 0 = 51 dB down.
  uint8_t attenuation = 2 + (VOLUME_MAX - level) * 5;
  player.setVolume(attenuation, attenuation);
}

void initializeRandom() {
  // Reserve the Uno's last eight EEPROM bytes (1016-1023).
  const int base = EEPROM.length() - 8;
  const uint32_t magic = 0x53504D31UL;
  uint32_t savedMagic, seed;
  EEPROM.get(base, savedMagic);
  EEPROM.get(base + 4, seed);
  if (savedMagic != magic || seed == 0) seed = 0x53A9C127UL;
  // Advance the persistent state once per boot, including a RESET.
  seed ^= seed << 13;
  seed ^= seed >> 17;
  seed ^= seed << 5;
  EEPROM.put(base + 4, seed);
  EEPROM.put(base, magic);
  uint32_t usableSeed = seed & 0x7FFFFFFFUL;
  randomSeed(usableSeed ? usableSeed : 1);
  dbgln(F("New random seed saved in EEPROM."));
}

void countSongs() {
  songIndex = SD.open(SONG_INDEX); // Stays open for the life of the sketch.
  File &list = songIndex;
  if (!list) halt(F("ERROR: SONGIDX.TXT not found."));
  listStart = SONG_LIST_START;
  // Optional UTF-8 BOM is not part of the first filename.
  if (listStart == 0 && list.read() == 0xEF &&
      list.read() == 0xBB && list.read() == 0xBF) listStart = 3;
  if (list.size() <= listStart) halt(F("ERROR: Song list is empty."));
  uint32_t bytes = list.size() - listStart;
  uint32_t count = bytes / RECORD_BYTES;
  uint8_t tail = bytes % RECORD_BYTES;
  if (tail == RECORD_BYTES - 1) count++; // Last record can omit its LF.
  else if (tail) {
    dbg(F("Trailing bytes outside full records: "));
    dbgln(tail);
  }
  if (!count || count > 65535) halt(F("ERROR: Invalid record count."));
  songCount = uint16_t(count);
  dbg(F("Song-list records: "));
  dbgln(songCount);
}

// Trailing spaces are padding; cut them off.
void trimRight(char *s, uint8_t len) {
  s[len] = 0;
  while (len && s[len - 1] == ' ') s[--len] = 0;
}

// name needs NAME_BYTES + 1 bytes, title needs TITLE_BYTES + 1.
bool findSong(uint16_t wanted, char *name, char *title) {
  name[0] = title[0] = 0;
  File &list = songIndex; // Already open; just seek.
  if (!list) return false;
  const uint32_t offset = listStart + uint32_t(wanted) * RECORD_BYTES;
  if (!list.seek(offset) || list.read(name, NAME_BYTES) != NAME_BYTES ||
      list.read() != '|' || list.read(title, TITLE_BYTES) != TITLE_BYTES) {
    return false;
  }
  trimRight(name, NAME_BYTES);
  trimRight(title, TITLE_BYTES);
  // 1-8 filename characters + .mp3, case-insensitive. No conversion.
  const char *dot = strchr(name, '.');
  uint8_t base = dot ? uint8_t(dot - name) : 0;
  bool valid = base >= 1 && base <= 8 && strcasecmp(dot, ".mp3") == 0;
  for (uint8_t i = 0; i < base; i++) {
    uint8_t ch = uint8_t(name[i]);
    if (ch <= 32 || ch >= 127 || ch == '/' || ch == '\\') {
      valid = false;
    }
  }
  if (!title[0]) strcpy(title, name); // No display name: show the file name.
  // Verify this really is a record boundary; allow EOF after the record.
  if (list.available()) {
    int lf = list.read();
    if (lf != '\n') valid = false;
  }
  if (!valid) {
    dbg(F("Invalid .mp3 record or LF at record "));
    dbg(uint32_t(wanted) + 1);
    dbg(F(" (byte "));
    dbg(offset);
    dbgln(')');
  }
  return valid;
}

// Starts one file and resets the position counter and progress bar.
bool startTrack(const char *file, const char *title) {
  // DECODE_TIME is not cleared between files; the datasheet says write it twice.
  writeReg(VS1053_REG_DECODETIME, 0);
  writeReg(VS1053_REG_DECODETIME, 0);
  // Opening only the selected track avoids a separate SD.exists() scan.
  if (!player.startPlayingFile(file)) {
    dbg(F("Cannot open file: "));
    dbgln(file);
    return false;
  }
  trackBytes = player.currentTrack.size();
  dbg(F("\nNow playing: "));
  dbgln(title);
  strncpy(currentTitle, title, sizeof(currentTitle) - 1);
  currentTitle[sizeof(currentTitle) - 1] = 0;
  if (leftCovered()) { // The list or popup covers the left side: draw it on close.
    barDrawn = 0;
    shownSecs = 0xFFFF;
  } else {
    displayTrack(title);
  }
  return true;
}

// Songs played before the current one, newest last, for Prev.
const uint8_t HISTORY_SIZE = 8;
uint16_t history[HISTORY_SIZE];
uint8_t historyCount = 0;
bool goingBack = false; // The next trySong() comes from Prev: don't record it.

void rememberSong(uint16_t song) {
  if (historyCount == HISTORY_SIZE) { // Full: drop the oldest.
    memmove(history, history + 1, (HISTORY_SIZE - 1) * sizeof(history[0]));
    historyCount--;
  }
  history[historyCount++] = song;
}

bool trySong(uint16_t selected) {
  char name[NAME_BYTES + 1];
  char title[TITLE_BYTES + 1];
  if (!findSong(selected, name, title) || !startTrack(name, title)) return false;
  if (!goingBack && lastSong >= 0 && lastSong != int32_t(selected)) rememberSong(lastSong);
  goingBack = false;
  lastSong = selected;
  return true;
}

// Prev: the song before this one, or the start of this one if there is no history.
void playPrevious() {
  int32_t song = lastSong;
  if (historyCount) {
    song = history[--historyCount];
    goingBack = true;
  }
  if (song >= 0) setSongMode(MODE_RANDOM, song);
}

void startNextSong() {
  if (songMode == MODE_HALLOWEEN && startTrack(LOOP_FILE, LOOP_TITLE)) return;
  if (chosenSong >= 0) {
    uint16_t song = chosenSong;
    if (songMode != MODE_LOOP_ONE) chosenSong = -1; // Play once, then shuffle.
    if (trySong(song)) return;
  }
  if (playingPick) { // The chosen song is done: stop and wait for the next choice.
    playingPick = false;
    playbackOn = false;
    strcpy_P(currentTitle, PSTR("Ready. Pick from the menu."));
    if (menuState == MENU_MAIN && displayOn()) {
      displayTrack(currentTitle);
      drawItem(ITEM_PLAY);
      drawItem(ITEM_RANDOM);
      dwinRefresh();
    }
    return;
  }
  uint16_t selected;
  if (songCount > 1 && lastSong >= 0) {
    selected = random(long(songCount - 1));
    if (selected >= lastSong) selected++;
  } else selected = random(long(songCount));

  // Try random choice first. If absent/invalid, try the following records.
  // Bounded retries avoid getting stuck on missing files in the song list.
  for (uint32_t attempt = 0; attempt < songCount; attempt++) {
    if (selected != lastSong && trySong(selected)) return;
    selected++;
    if (selected == songCount) selected = 0;
  }
  // If only the last song is playable, repeat it rather than stop playback.
  if (lastSong >= 0 && trySong(uint16_t(lastSong))) return;
  halt(F("No playable songs in SONGIDX.TXT"));
}

// Takes effect now: stopping the track makes loop() start the right one.
void setSongMode(uint8_t mode, int32_t song) {
  songMode = mode;
  chosenSong = song;
  playbackOn = true;
  playingPick = false; // The song picker sets it again after this call.
  player.stopPlaying();
}

void finishDecoder() {
  // VS1053b datasheet 10.5.1: flush decoded tail, then cancel old stream.
  uint8_t fill[32];
  memset(fill, uint8_t(readMemory(0x1E06)), sizeof(fill)); // endFillByte
  for (uint8_t block = 0; block < 65; block++) { // 2080 >= 2052 bytes
    waitReady();
    player.playData(fill, sizeof(fill));
  }
  writeReg(VS1053_REG_MODE, readReg(VS1053_REG_MODE) | VS1053_MODE_SM_CANCEL);
  for (uint8_t block = 0; block < 64; block++) {
    waitReady();
    player.playData(fill, sizeof(fill));
    if (!(readReg(VS1053_REG_MODE) & VS1053_MODE_SM_CANCEL)) return;
  }
  // Rare cancellation failure: reset, then restore the patches and mono mode.
  dbgln(F("Resetting decoder between tracks."));
  player.softReset();
  setVolumeLevel(volumeLevel);
  applyTone();
  loadPatches();
}

void setup() {
  // Display CFG set to 489600 (7833600 / 0x10); 2.1% off, within UART tolerance.
  Serial.begin(hasScreen ? 500000 : 115200);
  // Clear the screen the moment the display answers, so nothing old stays up.
  if (waitForDisplay(3000) && displayOn()) {
    dwinOrientation(TEXT_ORIENTATION);
    dwinClear(BLACK);
    dwinRefresh();
  }
  showSplash();
  unsigned long splashStart = millis();
  // On the HW-261 a card not yet in SPI mode holds MISO low and blocks the VS1053, so
  // the card starts first. The VS1053 is held in reset with both selects high meanwhile,
  // so it can't answer the card's commands either.
  pinMode(6, OUTPUT); digitalWrite(6, HIGH); // X-CS
  pinMode(7, OUTPUT); digitalWrite(7, HIGH); // X-DCS
  pinMode(8, OUTPUT); digitalWrite(8, LOW);  // X-RESET
  // A few tries: the screen powering up at the same time can make the first one fail.
  bool cardOk = false;
  for (uint8_t attempt = 0; attempt < 5 && !cardOk; attempt++) {
    if (attempt) delay(300);
    cardOk = SD.begin(CARD_CS);
  }
  if (!cardOk) halt(F("ERROR: SD card not found."));
  digitalWrite(8, HIGH);
  delay(10);
  bool vsOk = false;
  for (uint8_t attempt = 0; attempt < 3 && !vsOk; attempt++) {
    if (attempt) delay(200);
    vsOk = player.begin();
  }
  if (!vsOk) {
    // 0x0000 or 0xFFFF: no reply at all (wiring/solder); anything else: it answered wrong.
    uint16_t status = player.sciRead(VS1053_REG_STATUS);
    dbg(F("SCI_STATUS=0x"));
    dbgln(status, HEX);
    if (status == 0x0000) halt(F("VS1053 no reply (0000): check solder"));
    if (status == 0xFFFF) halt(F("VS1053 no reply (FFFF): check solder"));
    halt(F("VS1053 wrong reply: not a VS1053?"));
  }
  dbgln(F("VS1053 found."));
  countSongs();
  initializeRandom();
  loadSettings(); // Mono, before the patches apply it.

  setVolumeLevel(volumeLevel);
  applyTone();
  dbgln(F("Loading VS1053b patches..."));
  if (!loadPatches()) halt(F("ERROR: PATCHES.BIN not found."));
  dbg(F("Play mode: 0x"));
  dbgln(readMemory(0x1E09), HEX);
  while (millis() - splashStart < SPLASH_MS) {} // Splash stays up 3 s in total.
  displayInit();
  encoderBegin();

  // No useInterrupt(): loop() services playback and SCI reads sequentially.
  player.playbackLoop(false);
  if (autoStart) {
    playbackOn = true;
    startNextSong();
  } else {
    displayTrack(currentTitle); // "Ready. Pick from the menu."
  }

  /* Analyzer disabled.
  // Allow the decoder to process frames and initialize analyzer results.
  unsigned long started = millis();
  while (millis() - started < 500) player.feedBuffer();
  uint16_t bands = readMemory(0x1802);
  dbg(F("Spectrum bands: "));
  dbgln(bands);
  if (bands != 8) halt(F("ERROR: Expected eight spectrum bands."));
  */
  dbgln(F("Mono playback running."));
  if (!hasScreen) serialHelp();
}

// One CD frame every CD_FRAME_MS while music plays. Stops between tracks and
// while the song picker covers it; stays on whatever frame it reached.
void spinCD() {
  static unsigned long last = 0;
  static uint8_t cdFrame = 0;
  if (!displayOn() || player.stopped() || player.paused() || leftCovered()) return;
  if (millis() - last < CD_FRAME_MS) return;
  last = millis();
  cdFrame = (cdFrame + 1) % CD_FRAMES;
  dwinIcon(CD_LIB, CD_FIRST_ICON + cdFrame, CD_X, CD_Y);
  dwinRefresh();
}

// USB Serial commands, the screenless stand-in for the menu. Songs are numbered from 1
// in SONGIDX.TXT order (A-Z): type the number, then Enter.
void serialHelp() {
  Serial.println(F("Commands: <number> Enter = play that song once, then random"));
  Serial.println(F("  n next   b back   p pause/resume   + - volume"));
  Serial.println(F("  r random   o loop this song   w Halloween   m mono on/off"));
  Serial.println(F("  [ ] bass down/up   { } treble down/up"));
  Serial.println(F("  l list 10 songs from the current one   h this help"));
}

void serialCommands() {
  static uint16_t typed = 0;
  static bool typing = false;
  while (Serial.available()) {
    char c = Serial.read();
    if (c >= '0' && c <= '9') {
      typed = typing ? typed * 10 + (c - '0') : c - '0';
      typing = true;
      continue;
    }
    if (c == '\n' || c == '\r') {
      if (typing && typed >= 1 && typed <= songCount) setSongMode(MODE_RANDOM, typed - 1);
      else if (typing) { Serial.print(F("Pick 1-")); Serial.println(songCount); }
      typing = false;
      continue;
    }
    typing = false;
    switch (c) {
      case 'n': setSongMode(MODE_RANDOM, -1); break;
      case 'b': playPrevious(); break;
      case 'p': if (player.paused()) resumePlayback(); else pausePlayback(); break;
      case '+':
      case '-':
        setVolumeLevel(constrain(int16_t(volumeLevel) + (c == '+' ? 1 : -1), 0, VOLUME_MAX));
        Serial.print(F("Volume "));
        Serial.println(volumeLevel);
        break;
      case '[':
      case ']':
      case '{':
      case '}':
        if (c == '[' || c == ']') setTone(bassLevel + (c == ']' ? 1 : -1), trebleLevel);
        else setTone(bassLevel, trebleLevel + (c == '}' ? 1 : -1));
        saveTone();
        Serial.print(F("Bass "));
        Serial.print(bassLevel);
        Serial.print(F("  Treble "));
        Serial.println(trebleLevel);
        break;
      case 'r': setSongMode(MODE_RANDOM, -1); break;
      case 'o': if (lastSong >= 0) setSongMode(MODE_LOOP_ONE, lastSong); break;
      case 'w': setSongMode(MODE_HALLOWEEN, -1); break;
      case 'm':
        setMono(!monoOutput);
        Serial.println(monoOutput ? F("Mono") : F("Stereo"));
        break;
      case 'l': {
        char name[NAME_BYTES + 1];
        char title[TITLE_BYTES + 1];
        uint16_t first = lastSong >= 0 ? lastSong : 0;
        for (uint16_t s = first; s < first + 10 && s < songCount; s++) {
          player.feedBuffer();
          findSong(s, name, title);
          Serial.print(s + 1);
          Serial.print(F("  "));
          Serial.println(title);
        }
        break;
      }
      case 'h': serialHelp(); break;
    }
  }
}

void loop() {
  player.feedBuffer();
  if (!hasScreen) serialCommands(); // With the screen, Serial belongs to the display.
  menuUpdate();
  if (!leftCovered()) updateProgress(); // The list or popup covers the bar and time.
  spinCD();
  if (playbackOn && player.stopped()) {
    finishDecoder();
    delay(INTER_TRACK_GAP_MS);
    startNextSong();
  }
}

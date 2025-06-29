# -*- coding: utf-8 -*-
# ─── Board & DisplayIO Imports ────────────────────────────────
import board
import busio
import displayio
import terminalio
import neopixel  # Import the neopixel library
from adafruit_display_text import label
from i2cdisplaybus import I2CDisplayBus
from adafruit_displayio_ssd1306 import SSD1306 as ADAFRUIT_SSD1306

# ─── KMK Core & Extensions ────────────────────────────────────
from kmk.kmk_keyboard import KMKKeyboard
from kmk.scanners import DiodeOrientation
from kmk.modules.encoder import EncoderHandler
from kmk.extensions.rgb import RGB, AnimationModes
from kmk.extensions.media_keys import MediaKeys
from kmk.keys import KC

# --- Library Note ----------------------------------------------
# This code requires the following libraries in your 'lib' folder:
#  - adafruit_display_text
#  - i2cdisplaybus
#  - neopixel.mpy
# You can get them from the Adafruit CircuitPython library bundle.
# ---------------------------------------------------------------

# ─── Initialize KMK Keyboard ──────────────────────────────────
keyboard = KMKKeyboard()

# Disable KMK's internal debugging to prevent serial spam
keyboard.debug_enabled = False

# ─── Matrix Pins (3x3 = 9 Keys) ───────────────────────────────
keyboard.col_pins = (board.A3, board.RX, board.SCK)
keyboard.row_pins = (board.A0, board.A1, board.A2)
keyboard.diode_orientation = DiodeOrientation.COL2ROW

# ─── Media Keys for Volume Support ────────────────────────────
keyboard.extensions.append(MediaKeys())

# ─── RGB Lighting (Onboard LED Only) ──────────────────────────
# Onboard RGB LED on the XIAO RP2040
rgb_onboard = RGB(
    pixel_pin=board.NEOPIXEL,
    num_pixels=1,
    animation_mode=AnimationModes.RAINBOW,
    val_default=25, # Set brightness to 25%
)
keyboard.extensions.append(rgb_onboard)

# ─── OLED Display (Rotated 180° with Scrolling Text) ──────────
displayio.release_displays()
i2c_bus = busio.I2C(board.SCL, board.SDA)
display_bus = I2CDisplayBus(i2c_bus, device_address=0x3C)

# Initialize the display using the Adafruit library
oled_display = ADAFRUIT_SSD1306(display_bus, width=128, height=64)
oled_display.rotation = 180  # Flip the display 180 degrees

# Create a displayio group to hold our text label
main_group = displayio.Group()
oled_display.root_group = main_group

# Define the text and font
SCROLLING_TEXT = "XIAO KMK MACROPAD                                         "
font = terminalio.FONT

# Create the text label
text_label = label.Label(
    font,
    text=SCROLLING_TEXT,
    color=0xFFFFFF,
    scale=3,  # Set scale to 2 for a good size
)
# Use anchor point and anchored position for perfect centering
text_label.anchor_point = (0.0, 0.7)  # Anchor to the vertical middle
text_label.anchored_position = (oled_display.width, oled_display.height // 2)

main_group.append(text_label)


# --- Custom Scroller Module for KMK ---
class Scroller:
    def __init__(self, label, display):
        self.label = label
        self.display = display
        # FIX: Re-introduce the tick counter to slow down the display
        self.tick = 0

    def during_bootup(self, keyboard):
        pass

    def before_matrix_scan(self, keyboard):
        # This runs on every KMK loop.
        self.tick += 1

        # FIX: Only update the display every 50th cycle.
        # This makes the animation very slow, but it frees up the
        # processor and eliminates input lag for keypresses.
        if (self.tick % 60) == 0:
            self.label.x = self.label.x - 15  # Move the label 1 pixel to the left

            # Check if the label has scrolled completely off the left side
            if self.label.x < -self.label.bounding_box[2]:
                # Reset the position to the right side of the screen
                self.label.x = self.display.width

    def after_matrix_scan(self, keyboard):
        pass

    def before_hid_send(self, keyboard):
        pass

    def after_hid_send(self, keyboard):
        pass

    def on_powersave_enable(self, keyboard):
        pass

    def on_powersave_disable(self, keyboard):
        pass

    def process_key(self, keyboard, key, is_pressed, int_coord):
        return key

    def deinit(self, keyboard):
        pass

# Add our custom scroller module to KMK
keyboard.modules.append(Scroller(text_label, oled_display))


# ─── Rotary Encoder (No Button) ───────────────────────────────
encoder = EncoderHandler()
encoder.pins = (
    (board.MOSI, board.MISO, None),  # A, B, (no button)
)
encoder.map = [
    ((KC.VOLU, KC.VOLD),),  # CW = volume up, CCW = volume down
]
keyboard.modules.append(encoder)

# ─── Keymap: Numpad Layout ────────────────────────────────────
keyboard.keymap = [
    [
        KC.N7, KC.N8, KC.N9,
        KC.N4, KC.N5, KC.N6,
        KC.N1, KC.N2, KC.N3,
    ]
]

# ─── Launch Firmware ──────────────────────────────────────────
if __name__ == '__main__':
    # This print statement will still run once at startup
    print("Starting KMK Firmware...")
    keyboard.go()

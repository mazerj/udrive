# -*- Mode: Python; tab-width: 4; py-indent-offset: 4; -*-
#
# USB Joystick/Joypad interface class
# Fri Feb 23 12:18:09 2007 mazer
#
# The Joystick class opens a usb joystick (as a file) and can read
# and parse the device info on the fly. It's a 100% python way to
# read the device, although if the kernel drivers change it could
# become obsolete, so be careful!
#
# Each Joystick object maintains the internal state of the the buttons
# and axis. The object isn't actually threaded, but sucks the device
# file dry each time you query an axis or button.
#
# To query a button's status (and drain the input queue), just call
# the .button(n) method. 0 for up 1 for down.. Buttons start with
# number 1.
#
# Directional controller on the gamepad shows up as axis movement
# (axis(1) for horizontal, axis(2) for vertical) of +-32676..
#

import os, struct

"""
following structure taken from:
  kernel-sources...../Documentation/input/joystick-api.txt

struct js_event {
  unsigned long time;		/* event timestamp in milliseconds */
  short value;			/* value */
  unsigned char type;		/* event type */
  unsigned char number;		/* axis/button number */
;
"""

JS_EVENT_BUTTON = 0x01    # button pressed/released
JS_EVENT_AXIS = 0x02      # joystick moved
JS_EVENT_INIT = 0x80      # initial state of device

class Joystick:
    def __init__(self, devname='/dev/input/js0'):
        self.handle = open(devname,  "r", os.O_RDONLY|os.O_NDELAY)
        self.event_fmt = 'LhBB'
        self.event_size = struct.calcsize(self.event_fmt)
        self.button_state = {}
        self.axis_state = {}

    def query(self):
        import select
        s = select.select([self.handle], [], [], 0)
        if len(s[0]) == 0:
            return 0
        event = self.handle.read(self.event_size)
        time, value, type, number = struct.unpack(self.event_fmt, event)
        if type is JS_EVENT_BUTTON:
            if value:
                self.button_state[number] = value
            else:
                try:
                    del self.button_state[number]
                except KeyError:
                    pass
        elif type is JS_EVENT_AXIS:
            if value:
                self.axis_state[number] = value
            else:
                try:
                    del self.axis_state[number]
                except KeyError:
                    pass
        return 1

    def button(self, n):
        while self.query():
            # drain input off joystick
            pass
        try:
            # treat as one-shots:
            s = self.button_state[n]
            self.button_state[n] = 0
            return s
        except KeyError:
            return 0
    
    def axis(self, n):
        while self.query():
            # drain input off joystick
            pass
        try:
            # treat as one-shots:
            s = self.axis_state[n]
            self.axis_state[n] = 0
            return s
        except KeyError:
            return 0
    
def ignore(event=None):
    pass



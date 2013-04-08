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
};


-- Fri Jun 25 13:51:52 2010 mazer --

In Lucid (or earlier), this changed to:

struct js_event {
	__u32 time;	/* event timestamp in milliseconds */
	__s16 value;	/* value */
	__u8 type;	/* event type */
	__u8 number;	/* axis/button number */
};

size should be: 64 bits = 8 bytes

"""

JS_EVENT_BUTTON = 0x01    # button pressed/released
JS_EVENT_AXIS = 0x02      # joystick moved
JS_EVENT_INIT = 0x80      # initial state of device

class JoyStick:
    def __init__(self, devname='/dev/input/js0'):
        self.handle = open(devname,  "r", os.O_RDONLY|os.O_NDELAY)
        if calcsize('L') == 4:
            # 32bit arch
            self.event_fmt = 'LhBB'
            self.event_size = struct.calcsize(self.event_fmt)
        else:
            # 64bit arch
            self.event_fmt = 'IhBB'
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
        if not type & JS_EVENT_INIT:
            if type & JS_EVENT_BUTTON:
                self.button_state[number] = value
            else:
                self.axis_state[number] = value
        return 1

    def button(self, n):
        while self.query():
            # drain input off joystick
            pass
        try:
            return self.button_state[n]
        except KeyError:
            return 0
    
    def axis(self, n):
        while self.query():
            # drain input off joystick
            pass
        try:
            return self.axis_state[n]
        except KeyError:
            return 0
    

if __name__ == '__main__':
    j = JoyStick()
    while 1:
        for n in range(6):
            print j.button(n),
        print "%8d %8d" % (j.axis(0), j.axis(1))
    

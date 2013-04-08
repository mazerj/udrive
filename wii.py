# -*- Mode: Python; tab-width: 4; py-indent-offset: 4; -*-
#
# Wii Remote interface

WII_2     = (2**(1-1))
WII_1     = (2**(2-1))
WII_B     = (2**(3-1))
WII_A     = (2**(4-1))
WII_MINUS = (2**(5-1))
# bit6 = ?
# bit7 = ?
WII_HOME  = (2**(8-1))
WII_LEFT  = (2**(9-1))
WII_RIGHT = (2**(10-1))
WII_DOWN  = (2**(11-1))
WII_UP    = (2**(12-1))
WII_PLUS  = (2**(13-1))

class WiiMote:
	def __undermouse(self, w):
		"""
		Position a window 'w' directly underneath the mouse
		"""
		rw, rh = w.winfo_reqwidth(), w.winfo_reqheight()
		x, y = w.winfo_pointerx()-(rw/2), w.winfo_pointery()-(rh/2)
		if x < 0:
			x = 0
		elif (x+rw) >= w.winfo_screenwidth():
			x = w.winfo_screenwidth() - rw
		if y < 0:
			y = 0
		elif (y+rh) >= w.winfo_screenheight():
			y = w.winfo_screenheight() - rh
		w.geometry("+%d+%d" % (x, y))

    def __init__(self, devname):
        import Tkinter, cwiid

        w = Tkinter.Toplevel()
        w.overrideredirect(1)
        w.withdraw()
        f = Tkinter.Frame(w, borderwidth=20, background='red')
        f.pack(expand=1, fill=BOTH)
		if len(devname) == 17:
			l = Tkinter.Label(f, text='Press 1+2 buttons on [%s]' % devname)
		else:
			l = Tkinter.Label(f, text='Press 1+2 buttons on remote')
        l.pack(expand=1, fill=BOTH)
        
        w.update_idletasks()
        self.__undermouse(w)
        w.deiconify()
        w.update_idletasks()

		if len(devname) == 17:
			# fully specified hex 6-tuple, then connect to specified wiimote
            self.wiimote = cwiid.Wiimote(devname)
        else:
            # connect to first wiimote that's available
            self.wiimote = cwiid.Wiimote()

        w.destroy()

		# setup wii to report btn and accelerometer data:
		self.wiimote.rpt_mode = cwiid.RPT_BTN ^ cwiid.RPT_ACC
            
    def button(self, n=None):
		# first button is 0.. not 1
		if n:
			return self.wiimote.state['buttons'] & (2**n)
		else:
			return self.wiimote.state['buttons']

	def battery(self):
		import cwiid
		return int(100.0 * self.wiimote.state['battery'] / cwiid.BATTERY_MAX)

	def buzz(self, w=None):
		if w:
			self.wiimote.rumble = 1
			w.after(75, lambda: self.buzz(None))
		else:
			self.wiimote.rumble = 0

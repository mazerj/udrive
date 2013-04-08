#!/usr/bin/env python
# -*- Mode: Python; tab-width: 4; py-indent-offset: 4; -*-

import string, sys, os
from Tkinter import *

__debugflag__ = 0

# this uses the pyserial package (pyserial.sf.net)
# last version pyserial-2.2
try:
    import serial
except ImportError:
    sys.stderr.write('warning: pyserial package is not installed!\n')
    __debugflag__ = 1

class beep:
    toplevel = None
    def __init__(self, toplevel=None):
        if toplevel:
            beep.toplevel = toplevel
        elif beep.toplevel:
            beep.toplevel.bell()


class Controller(Frame):
    def __init__(self, tkparent, multi, n, port):
        Frame.__init__(self, tkparent, borderwidth=0, relief=RIDGE)

        # parent widget (MultiController)
        self.parent = tkparent
        self.multi = multi

        # motor number (1-8 for our setup)
        self.motor_no = n

        # serial port handle
        self.port = port

        # compute step size in microns
        tpi = 101.61                    # threads per inch
        ratio = 125.0                   # gearing ratio on micromo motor
        self.um_per_step = 1.0 / tpi / ratio / 3.0 * 25400.0
        
        # Max travel length is 14mm (in um). Lock the drive to
        # stay within 0 and 14mm.
        # min travel is zero.
        self.up_limit = 0
        self.down_limit = 14000

        # start off with motor unlocked
        self.locked = 0

        self.position = 0
        self.abs_position = 0
        self.ss = 1

        # Build a little Tkinter controller widget. We are subclassing
        # of a Frame widget, so we don't need an outer frame.

        # motor number (color indicates: selected, in motion, idle)
        self.motor_label = Label(self, text='%d' % n, bg='white')

        # relative position labels (um and steps)
        self.poslabel = Label(self, anchor=E)
        
        # absolute position labels (um and steps)
        self.abs_poslabel = Label(self, anchor=W)

        # zero relative position button
        z = Button(self, text='<-ZERO',
                   padx=2, pady=0,
                   command=lambda s=self: s.restore(0, None, None, None))
        # lock this drive button
        self.lock = Button(self, text=' LOCK  ',
                           padx=2, pady=0,
                           command=lambda s=self: s.toglock())

        # go home this drive button
        h = Button(self, text='go H',
                   padx=2, pady=0,
                   command=lambda s=self: s.home())
        # zero absolute position button -- use with caution! (set home)
        az = Button(self, text='set H',
                    padx=2, pady=0,
                    command=self.at_home)

        # step size indicator
        self.ssl = Label(self, text='')

        # use grid manager to layout the widgets in a nice array

        self.motor_label.grid(row=0, column=0, rowspan=2, padx=5)
        
        self.poslabel.grid(row=0, column=1, columnspan=2, sticky=W+E+N+S)

        self.ssl.grid(row=1, column=1, columnspan=2, sticky=E)
        
        z.grid(row=0, column=3)
        self.lock.grid(row=1, column=3)
        self.abs_poslabel.grid(row=0, column=5, columnspan=2, sticky=W+E+N+S)
        
        h.grid(row=1, column=5)
        az.grid(row=1, column=6)

        # set initial parameters (stepsizes etc)
        self.restore(0, 10, 0, None)
        
    def step(self, multiplier):
        # never move locked drives!
        if self.locked:
            return None

        try:
            nsteps = multiplier * self.ss_get()     # 1-37676
            if multiplier > 0:
                # advance
                dir = 1
            else:
                # retract
                dir = 0

            if self.multi.limiters.get():
                dest = (self.abs_position + nsteps) * self.um_per_step
                if dest < self.up_limit:
                    self.abs_poslabel.configure(fg='red')
                    return 0
                elif dest > self.down_limit:
                    self.abs_poslabel.configure(fg='red')
                    return 0
            self.abs_poslabel.configure(fg='black')

            motorno = self.motor_no     # 1-64
            #speed = 0                   # 0(fastest) - 7(slowest) (docs XXX)
            #speed = 3                   # 0(fastest) - 7(slowest) (docs XXX)
            speed = self.multi.config.speed

            if nsteps >= 0:
                cmd = "%d %d %d %d %d \n" % (1, nsteps, motorno, dir, speed)
            else:
                cmd = "%d %d %d %d %d \n" % (1, -nsteps, motorno, dir, speed)

            if self.port is None:
                self.position = self.position + nsteps
                self.abs_position = self.abs_position + nsteps
            else:
                self.port.write(cmd)
                # now wait until the command is done
                while 1:
                    resp = self.port.readline()
                    try:
                        l = string.split(resp)
                        if int(l[0]) == 1:
                            break
                        p = float(l[3])
                        self.update()
                    except:
                        sys.stderr.write('Lost controlled contact!\n')
                        sys.stderr.write('Saved state and exiting.\n')
                        self.multi.quitprog()
                        sys.exit(1)
                    l = string.split(resp)
                self.position = self.position + nsteps
                self.abs_position = self.abs_position + nsteps
            self.redraw()
        finally:
            pass

        # tell MultiController we moved -- for auto-saving..
        self.multi.tick()
            
        return 1

    def toglock(self, set=None):
        if set is not None:
            self.locked = set
        else:
            self.locked = not self.locked

        if self.locked:
            self.lock.config(text=' UNLCK ')
        else:
            self.lock.config(text='  LOCK ')

            
        self.redraw()

    def redraw(self):
        if self.multi.um.get():
            self.poslabel.configure(text='%06dum' %
                                    int(self.position * self.um_per_step))
            self.abs_poslabel.configure(text='%06dum' %
                                        int(self.abs_position * \
                                            self.um_per_step))
            self.ssl.config(text="%.0fum" % \
                            (self.ss * self.um_per_step, ))

        else:
            self.poslabel.configure(text='%06dst' % self.position)
            self.abs_poslabel.configure(text='%06dst' % self.abs_position)
            self.ssl.config(text="%dst" % \
                            (self.ss, ))

        if self.locked:
            self.poslabel.configure(fg='gray60')
            self.abs_poslabel.configure(fg='gray60')
            self.ssl.configure(fg='gray80')
            self.motor_label.configure(fg='gray60')
        else:
            self.poslabel.configure(fg='black')
            self.abs_poslabel.configure(fg='black')
            self.ssl.configure(fg='black')
            self.motor_label.configure(fg='black')
        

    def ss_set(self, s, um=0):
        if um:
            s = int(0.5 + (s / self.um_per_step))
        # max stepsize is 500 steps (~300um)
        self.ss = max(1, min(s, 500))
        self.redraw()
        
    def ss_get(self):
        return self.ss

    def at_home(self):
        self.restore(None, None, None, 0)

    def home(self):
        try:
            self.parent.stepping = 1
            if self.abs_position > 0:
                while not self.multi.abort:
                    if self.step(-1) == 0:
                        return
                    self.update()
        finally:
            self.parent.stepping = 0
        beep()

    def restore(self, position, stepsize, locked, abs_position):
        if position is not None:
            self.position = position
        if abs_position is not None:
            self.abs_position = abs_position
        if locked is not None:
            self.toglock(locked)
        if stepsize is not None:
            self.ss_set(stepsize)
            
        self.redraw()

class MultiController(Frame):
    def __init__(self, parent, nmax, config):
        self.rootwin = parent
        self.oldgeo = None
        self.parent = parent
        self.config = config

        try:
            if __debugflag__ or self.config.controller == 'None':
                self.port = None
                sys.stderr.write('skipping port open\n')
            else:
                self.port = serial.Serial(port=self.config.controller,
                                          baudrate=115200,
                                          parity=serial.PARITY_EVEN,
                                          bytesize=8, stopbits=1,
                                          timeout=1,
                                          rtscts=0, xonxoff=0)
                self.port.setDTR(1)
                self.port.setRTS(1)
                
                connect = 0
                # send ping command and get response (should # be "2 \n")
                self.port.write("7 \n")
                for n in range(100):
                    resp = self.port.readline()
                    if resp[0] == '2':
                        #sys.stderr.write('Connected.\n')
                        connect = 1
                        break
                    elif len(resp) == 1 and ord(resp[0]) == 255:
                        sys.stderr.write("Can't see controller. Check power!\n")
                        sys.exit(1)
                    else:
                        #sys.stderr.write('Controller garbage: [%s]\n' % resp)
                        pass
                if not connect:
                    sys.stderr.write('Controller funky -- power cycle!]\n')
                    sys.exit(1)
                    
        except serial.serialutil.SerialException:
            sys.stderr.write("Can't open serial port: %s\n" % \
                             self.config.controller)
            sys.stderr.write("Check permissions or run as root!\n")
            self.port = None

        # give up root access now that the serial port's open
        import pwd, os
        try:
            uid = pwd.getpwnam(os.environ['SUDO_USER'])[2]
        except KeyError:
            uid = pwd.getpwnam(os.environ['USER'])[2]
        os.seteuid(uid)            

        Frame.__init__(self, parent)
        self.configure(borderwidth=0)
        
        menu = Menu(parent)
        parent.config(menu=menu)

        filemenu = Menu(menu, tearoff=0)
        menu.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="Save", command=self.save_to_file)
        filemenu.add_command(label="Re-focus keyboard",
                             command=self.focus_set)
        filemenu.add_separator()
        filemenu.add_command(label="Zero all drives", command=self.zero_all)
        filemenu.add_command(label="Home all drives", command=self.home_all)
        filemenu.add_separator()
        filemenu.add_command(label="Quit", command=self.quitprog)

        showmenu = Menu(menu, tearoff=0)
        menu.add_cascade(label="Set", menu=showmenu)
        showmenu.add_command(label="Toggle active only",
                             command=self.toggle_showall)

        self.moveall = IntVar()
        self.moveall.set(0)
        showmenu.add_checkbutton(label="Move All",
                                 variable=self.moveall,
                                 onvalue=1, offvalue=0,
                                 selectcolor='black',
                                 command=self.redraw)
                                 
        self.limiters = IntVar()
        self.limiters.set(1)
        showmenu.add_checkbutton(label="Use Limiters",
                                 variable=self.limiters,
                                 onvalue=1, offvalue=0,
                                 selectcolor='black',
                                 command=self.redraw)
        self.um = IntVar()
        self.um.set(1)
        showmenu.add_checkbutton(label="show microns", variable=self.um,
                                 onvalue=1, offvalue=0,
                                 selectcolor='black',
                                 command=self.redraw)
        
        self.drives = {}
        self.controller_frame = Frame(self)
        self.controller_frame.pack(side=TOP, fill=X, expand=1, pady=0)
        for i in range(1,nmax+1):
            self.drives[i] = Controller(self.controller_frame, self,
                                        i, self.port)
            self.drives[i].grid(row=i, column=1, pady=2, padx=2)
            self.drives[i].config(pady=5, borderwidth=3, relief=FLAT)
            self.ndrives = i

        f = Frame(self)
        f.pack(expand=1, fill=X)
        self.txt = Label(f, text='', anchor=W)
        self.txt.pack(expand=1, side=LEFT)
        self.msg = Label(f, text='', anchor=E)
        self.msg.pack(expand=1, side=RIGHT)
        
        self.argument = ''

        self.active = 0
        self._showactive = 0
        
        self.select(1)
        
		self.bind("<KeyPress>", self.keypress)

		self.focus_set()
        
        self.abort = 0
        self.stepping = 0

        self.nticks = 0

    def select(self, n):
        if self.active > 0:
            self.drives[self.active].configure(relief=FLAT)
            self.drives[self.active].motor_label.config(bg='white')
        self.active = n
        self.drives[self.active].configure(relief=RAISED)
        self.drives[self.active].motor_label.config(bg='red')
        self.toggle_showall()
        self.toggle_showall()           # need both!

    def redraw(self):
        for k in range(1,1+self.ndrives):
            self.drives[k].redraw()

    def keypress(self, ev, keysym=None):
        #print ev.keysym

        if not ev is None:
            # NOT simulated keypress
            keysym = ev.keysym
        
        if keysym == 'Escape' or \
               keysym == 'KP_Divide' or keysym == 'KP_Multiply':
            self.abort = 1
            return
            
        if self.stepping:
            # if not escape, busy stepping .. don't do anything
            return
            
        if keysym == 'Up' or keysym == 'KP_Up' :
            if self.moveall.get():
                for k in range(1,1+self.ndrives):
                    self.stepping = 1
                    self.drives[k].step(-1)
                    self.stepping = 0
                    if self.abort:
                        self.abort = 0
                        return
            else:
                self.stepping = 1
                self.drives[self.active].step(-1)
                self.stepping = 0
            beep()
        elif keysym == 'Down' or keysym == 'KP_Down':
            if self.moveall.get():
                for k in range(1,1+self.ndrives):
                    self.stepping = 1
                    self.drives[k].step(1)
                    self.stepping = 0
                    if self.abort:
                        self.abort = 0
                        return
            else:
                self.stepping = 1
                self.drives[self.active].step(1)
                self.stepping = 0
            beep()
        elif keysym == 'space' or keysym in 'nN' or \
             keysym == 'KP_End':

            ntries = 0
            n = self.active
            while 1:
                n = n + 1
                if n > self.ndrives:
                    n = 1
                if not self.drives[n].locked:
                    break
                ntries = ntries + 1
                if ntries > self.ndrives:
                    sys.stderr.write('warning: all drives locked\n')
                    n = -1
                    break
            if n >= 0:
                self.select(n)
        elif keysym in 'pP' or keysym == 'KP_Home':

            ntries = 0
            n = self.active
            while 1:
                n = n - 1
                if n < 1:
                    n = self.ndrives
                if not self.drives[n].locked:
                    break
                ntries = ntries + 1
                if ntries > self.ndrives:
                    sys.stderr.write('warning: all drives locked\n')
                    n = -1
                    break
            if n >= 0:
                self.select(n)
        elif keysym == 'equal':
            # toggle limiters
            if self.limiters.get():
                self.limiters.set(0)
            else:
                self.limiters.set(1)
        elif (keysym in 'lL') or keysym == 'KP_Insert':
            self.drives[self.active].toglock()
        elif keysym in 'qQ':
            # quit
            self.quitprog()
            self.txt = None
        elif keysym in '0123456789':
            self.argument = self.argument + keysym
        elif keysym == 'BackSpace':
            self.argument = self.argument[:-1]
        elif keysym == 'KP_Subtract'  or keysym in '-_':
            k = self.drives[self.active].ss_get()
            self.drives[self.active].ss_set(k - 1)
        elif keysym == 'KP_Add' or keysym in '=+':
            k = self.drives[self.active].ss_get()
            self.drives[self.active].ss_set(k + 1)
        elif keysym in 'sS':
            # set stepsize on current drive
            try:
                i = int(self.argument)
                self.drives[self.active].ss_set(i)
            except ValueError:
                for k in range(1,1+self.ndrives):
                    self.drives[k].ss_set(self.drives[self.active].ss_get())
            self.argument = ''
        elif keysym in 'uU':
            # set stepsize on current drive
            try:
                i = int(self.argument)
                self.drives[self.active].ss_set(i, um=1)
            except ValueError:
                for k in range(1,1+self.ndrives):
                    self.drives[k].ss_set(self.drives[self.active].ss_get())
            self.argument = ''
        elif keysym in 'gG':
            # goto motor
            try:
                i = int(self.argument)
                if (i > 0) and (i < (self.ndrives+1)):
                    self.select(i)
            except ValueError:
                pass
            self.argument = ''
        elif keysym in 'aA':
            self.toggle_showall()

        if self.txt:
            if len(self.argument) > 0:
                self.txt.config(text='arg: ' + self.argument)
            else:
                self.txt.config(text='')

    def zero_all(self):
        for k in range(1,1+self.ndrives):
            self.drives[k].restore(0, None, None, None)

    def home_all(self):
        try:
            self.stepping = 1
            nmoved = 1
            while nmoved > 0:
                nmoved = 0
                for k in range(1,1+self.ndrives):
                    d = self.drives[k]
                    if d.abs_position > 0 and d.step(-1) == 1:
                        nmoved = nmoved + 1
                    if self.abort:
                        self.abort = None
                        return 0

                    # need this to catch abort signal!
                    self.update()
        finally:
            self.stepping = 0
        beep()

    def toggle_showall(self):
        if self._showactive:
            self.show_all()
        else:
            self.show_one()
            
    def show_one(self):
        for k in self.drives.keys():
            if not k == self.active:
                self.drives[k].grid_forget()
        self._showactive = 1
    
    def show_all(self):
        for k in self.drives.keys():
            self.drives[k].grid(row=k, column=1)
        self._showactive = 0

    def tick(self):
        """auto-save state every 1 ticks (tick is step on any drive)"""
        
        if self.nticks > 1:
            self.save_to_file()
            self.nticks = 0
        else:
            self.nticks = self.nticks + 1

    def save_to_file(self, root=None):
        try:
            f = open(self.config.statefile, 'w')
            f.write('A%d\n' % self.active)
            f.write('M%d\n' % self.moveall.get())
            for k in self.drives.keys():
                f.write('S%d,%d,%d,%d,%d\n' % (k,
                                            self.drives[k].position,
                                            self.drives[k].ss_get(),
                                            self.drives[k].locked,
                                            self.drives[k].abs_position))
            f.close()
        except IOError:
            sys.stderr.write("Can't write %s.\n" % self.config.statefile)

    def restore_from_file(self):
        try:
            f = open(self.config.statefile, 'r').readlines()
            for l in f:
                if l[0] == 'A':
                    self.select(int(l[1:]))
                elif l[0] == 'M':
                    self.moveall. set(int(l[1:]))
                elif l[0] == 'S':
                    (n, position, stepsize, locked, absposition) = \
                        map(int, string.split(l[1:], ','))
                    self.drives[n].restore(position, stepsize,
                                           locked, absposition)
                else:
                    sys.stderr.write('ignored: %s' % l)
        except IOError:
            sys.stderr.write("Can't read %s.\n" % self.config.statefile)

    def quitprog(self):
        self.save_to_file()
        self.parent.destroy()


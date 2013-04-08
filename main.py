#!/usr/bin/env python
# -*- Mode: Python; tab-width: 4; py-indent-offset: 4; -*-

def ignore(event=None):
    pass

class ConfigInfo:
    def __init__(self, file='/etc/udrive.conf'):
        import ConfigParser

        # Default config settings:
        self.statefile = '/etc/udriverc'
        self.controller = '/dev/ttyS0'
        self.joystick = '/dev/input/js0'
        self.wii = 'None'
        self.speed = 3
        
        c = ConfigParser.RawConfigParser()
        c.read(file)
        if len(c.sections()) > 0:
            section = c.sections()[0]
            if c.has_option(section, 'statefile'):
                self.statefile = c.get(section, 'statefile')
            if c.has_option(section, 'controller'):
                self.controller = c.get(section, 'controller')
            if c.has_option(section, 'joystick'):
                self.joystick = c.get(section, 'joystick')
            if c.has_option(section, 'wii'):
                self.wii = c.get(section, 'wii')
            if c.has_option(section, 'speed'):
                self.speed = c.getint(section, 'speed')
                if self.speed < 0: self.speed = 0
                if self.speed > 7: self.speed = 7

if __name__ == '__main__':
    config = ConfigInfo('/etc/udrive.conf')
    
	tk = Tk()
    tk.title('udrive control')
    tk.option_add('*Foreground', 'black')
    tk.option_add('*Background', 'grey')
    #tk.option_add('*Font', '-*-lucidatypewriter-medium-r-*-*-14-*-*-*-m-*-*-*')

    os.system('xset b 100 1000 25')
    beep(tk)
    
    # disable tab traversal of the widgets:
    tk.bind_all("<Tab>", ignore)

    # prevent closure until initialized:
    tk.protocol("WM_DELETE_WINDOW", ignore)
    
    # initialise control panel
    c = MultiController(tk, 8, config)
    c.pack()
    c.restore_from_file()

    # now closure is ok..
    tk.protocol("WM_DELETE_WINDOW", lambda c=c: c.quitprog())

    js = None
    if config.joystick == 'None':
        sys.stderr.write("warning: no joystick specified\n")
    else:
        try:
            js = Joystick(devname=config.joystick)
        except:
            sys.stderr.write("Can't access joystick at %s\n" % config.joystick)

    wii = None
    if config.wii == 'None':
        sys.stderr.write("warning: no wii remote specified\n")
    else:
        tk.withdraw()
        wii = WiiMote(config.wii)
        wii.buzz(tk)
        tk.deiconify()

    # looks like axis control is unreliable..
    axis = 0
    firstpass = 1
    
    while 1:
        if js:
            if js.button(0):
                c.keypress(None, 'Down')
            elif axis and js.axis(1) > 0:
                c.keypress(None, 'Down')
            elif js.button(3):
                c.keypress(None, 'Up')
            elif axis and js.axis(1) < 0:
                c.keypress(None, 'Up')
            elif js.button(1):
                c.keypress(None, 'n')
            elif js.button(2):
                c.keypress(None, 'p')
            elif js.button(5):
                c.keypress(None, 'Escape')
            elif js.button(6) or js.button(7):
                tk.withdraw()
                tk.lift()
                tk.deiconify()

        if wii:
            if firstpass:
                bat = wii.battery()
                c.msg.config(text='[%.0f%% bat]' % bat)
                if bat < 25:
                    c.msg.config(bg='red')
                else:
                    c.msg.config(bg='green')
            b = wii.button()
            if b:
                if b & WII_DOWN:
                    c.keypress(None, 'Down')
                    wii.buzz(tk)
                if b & WII_UP:
                    c.keypress(None, 'Up')
                    wii.buzz(tk)
                if b & WII_RIGHT:
                    c.keypress(None, 'n')
                if b & WII_LEFT:
                    c.keypress(None, 'p')
                if b & WII_PLUS:
                    c.keypress(None, '+')
                if b & WII_MINUS:
                    c.keypress(None, '-')
                if b & WII_A:
                    c.keypress(None, 'Escape')
                if b & WII_1:
                    c.keypress(None, 'a')
                if b & WII_B:
                    tk.withdraw()
                    tk.lift()
                    tk.deiconify()
                    
                bat = wii.battery()
                c.msg.config(text='[%.0f%% bat]' % bat)
                if bat < 25:
                    c.msg.config(bg='red')
                else:
                    c.msg.config(bg='green')
                    
                while 1:
                    tk.update()
                    b = wii.button()
                    if b == 0: break

        try:
            tk.update()
        except:
            # tk has been destroyed, end execution..
            break
        firstpass = 0

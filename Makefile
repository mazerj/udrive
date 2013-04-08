install: udrive.py udriveperm
	sudo cp udrive.sh /usr/bin/udrive
	sudo mv udrive.py /usr/bin
	sudo mv udriveperm /usr/bin
	sudo chmod +x /usr/bin/udrive /usr/bin/udrive.py
	sudo chown root /usr/bin/udriveperm
	sudo chmod u+s /usr/bin/udriveperm
	sudo touch /etc/udriverc
	sudo chmod a+rw /etc/udriverc
	if [ ! -e /etc/udrive.conf ]; then sudo cp udrive.conf /etc; fi;

udrive.py: controller.py joystick.py wii.py main.py
	cat controller.py joystick.py wii.py main.py > udrive.py

udriveperm: udriveperm.c
	cc -o udriveperm udriveperm.c

install-lib:
	(cd pyserial-2.2; python ./setup.py install)

clean:
	rm -rf udrive.py udriveperm \#*~ pyserial-2.2/build/*


# needs to run as root
# if you want to use sudo for this, add:
#   ALL     ALL= NOPASSWD: /usr/bin/udrive.py
# to /etc/sudoers


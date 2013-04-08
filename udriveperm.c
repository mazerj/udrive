#include <stdio.h>

// hard coded SUID-root program to release access to
// ports (serial/joystick etC) needed to udrive to run
// properly.
//
// warning: this is an ugly hack (but reasonably safe)

main()
{
  int uid = getuid();
  setuid(0);
  system("/bin/chmod a+rwx /dev/input/js* 2>/dev/null");
  system("/bin/chmod a+rwx /dev/USB* 2>/dev/null");
  system("/bin/chmod a+rwx /dev/ttyS* 2>/dev/null");
  setuid(uid);
  return(0);
}

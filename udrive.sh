#!/bin/sh

udriveperm >>/tmp/udrive-`whoami`.log 2>&1
/usr/bin/udrive.py >>/tmp/udrive-`whoami`.log 2>&1 &

#! /usr/bin/env python
#
# Python module for managing the Numato USB 8-port GPIO board
#
# Written by Mark Hatle <mark@hatle.net>
# Copyright (C) 2018 Mark Hatle
#
# All of the items here are licensed under the GNU General Public License 2.0, unless
# otherwise noted.  See COPYING for further details.
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import serial
from time import sleep
import threading

class Gpio():
    def __init__(self, serial_port):
        self.lock = threading.Lock()   # Thread lock for the data

        try:
            self.lock.acquire()

            self.gpio      = None	# Stored GPIO value

            self.gpio_fd   = None
            self.gpio_port = serial_port

            self.events = []   # Thread events when data is updated

            self.gpio_fd   = serial.Serial(self.gpio_port, 115200, timeout=0)

            self.init = True

        finally:
            self.lock.release()

    def __del__(self):
        self.gpio_fd.close()

    def registerEvent(self, event):
        if event not in self.events:
            self.events.append(event)

    def deregisterEvent(self, event):
        if event in self.events:
            self.events.remove(event)

    def getGpio(self):
        try:
            self.lock.acquire()
            #print("D: raw gpio  %s" % self.gpio)
            if self.gpio:
                return int(self.gpio)
            else:
                return None
        finally:
            self.lock.release()

        return result

    def poll_gpio(self):
        def _gpio_write(output):
            #print('D: "%s" --> gpio' % output)
            self.gpio_fd.write(output + '\n')
            # Give the device time to respond
            sleep(.1)

        def _gpio_readbuffer():
            buffer = ""
            while True:
                input = self.gpio_fd.read()
                #print('D: "%s" <-- gpio' % input)
                if not input:
                    break
                buffer += input
            return buffer

        def _write_read_gpio(output):
            _gpio_write(output)
            buffer = _gpio_readbuffer()
            lines = []
            prompt = False
            for line in buffer.split('\n\r'):
                # Skip blank lines
                if not line:
                    continue
                # Skip output command
                if line == output:
                    continue
                # Skip prompt
                if line == ">":
                    prompt = True
                    break
                lines.append(line)

            if not prompt:
                raise exception("Input did not end with prompt")

            #print('line: "%s"' % lines)
            return lines

        if self.init:
            self.init = False
            _write_read_gpio('')

        lines = _write_read_gpio('gpio readall')
        if len(lines) > 1:
            # Got unexpected data
            print("Warning got more then one line of data: %s" % lines)

        return int(lines[0], 16)

    # run the gpio API watcher.
    def run(self, wait_time=1):
        last_gpio = self.getGpio()
        while True:
            gpio = self.poll_gpio()
            if gpio != last_gpio:
                try:
                    self.lock.acquire()

                    self.gpio = gpio
                    last_gpio = gpio

                finally:
                    self.lock.release()
                    for event in self.events:
                        event.set()

            sleep(wait_time)


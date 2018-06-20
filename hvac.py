#! /usr/bin/env python
#
# This is the HVAC control software written for my own home integration.
# The software bridges the Nest thermostats, an 8-port Numato GPIO board, the
# IFTTT service, all to control heating and cooling within the home.
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

from lib import nest
from lib import gpio
from lib import ifttt
from lib import livingroom

import settings

import threading

from time import sleep

lastbin_gpio = ""
def process_gpio_event():
    global lastbin_gpio
    gpio_lines = gpio_obj.getGpio()
    bin_gpio = ("{0:b}".format(gpio_lines))
    if lastbin_gpio != bin_gpio:
        print("gpio: %s state change" % bin_gpio)
    else:
        print("gpio: %s" % bin_gpio)
    lastbin_gpio = bin_gpio

last_update = {}
def process_nest_event():
    global last_update
    (updated, thermostats) = nest_obj.getThermostats()
    for id in thermostats:
        if not id in last_update:
            last_update[id] = 0
        if id not in updated or updated[id] <= last_update[id]:
            continue
        last_update[id] = updated[id]

        thermostat = thermostats[id]

        status = thermostat['hvac_mode']
        if status != 'off':
            if thermostat['hvac_state'] != 'off':
                status = '%s (%sm) to %s' % (thermostat['hvac_state'], thermostat['time_to_target'], thermostat['target_temperature_f'])
            else:
                status = '%s to %s' % (thermostat['hvac_mode'], thermostat['target_temperature_f'])

        print("%s: %s (current %sF %s%%)" % (thermostat['name'], status,
                 thermostat['ambient_temperature_f'],
                 thermostat['humidity']))


gpio_obj = gpio.Gpio(settings.GPIO_SERIAL)
nest_obj = nest.Nest(settings.NEST_TOKEN)
ifttt_obj = ifttt.IFTTT(settings.IFTTT_TOKEN)

livingroom_obj = livingroom.LivingRoom(nest_obj, gpio_obj, ifttt_obj)

gpio_thread = threading.Thread(target=gpio_obj.run)
nest_thread = threading.Thread(target=nest_obj.run, args=(True,))
ifttt_thread = threading.Thread(target=ifttt_obj.run)

livingroom_thread = threading.Thread(target=livingroom_obj.run)

# Process for ongoing status
nest_event = threading.Event()
nest_obj.registerEvent(nest_event)

gpio_thread.daemon = True
nest_thread.daemon = True
ifttt_thread.daemon = True
livingroom_thread.daemon = True

gpio_thread.start()
nest_thread.start()
ifttt_thread.start()
livingroom_thread.start()

print("HVAC Control Software v0.3")
print("Copyright (C) 2018 Mark Hatle")
print("See the source code for licensing terms and conditions.")

while True:
    event = nest_event.wait(.1)
    if event:
        nest_event.clear()
        process_nest_event()


# Individual device configuration: Livingroom
#
# This drives the models/algorithms to manage my livingroom
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

import nest
import gpio
import ifttt
import threading
from time import sleep

class LivingRoom():
    def __init__(self, nest=None, gpio=None, ifttt=None):
        self.nest        = nest
        self.gpio        = gpio
        self.ifttt       = ifttt

        # ifff action and response retry value (0 = no wait for an activation, assume it worked)
        self.ifttt_on    = ( "livingroom_ac_on", 0 )
        self.ifttt_off   = ( "livingroom_ac_off", 0 )
        self.ifttt_cool  = ( "livingroom_ac_cool", 30 )
        self.ifttt_eco   = ( "livingroom_ac_eco", 30 )
        self.ifttt_temp  = ( "livingroom_ac_set_%s", 0 )

        # Current Living Room settings
        self.ac_on       = None  # Is the air conditioner on or off?
        self.ac_cooling  = None  # Is the air conditioner cooling?
        self.ac_temp     = 0  # Degrees F to set the AC unit to
        self.ac_min      = 64
        self.ac_max      = 80
        self.ac_temp_default = 70  # Default temp if no info from the thermostat

        self.ac_cooling_on_offset  = -2 # When cooling drop temp by N degrees
        self.ac_cooling_off_offset =  2 # When NOT cooling raise temp by N degrees

        # Nest specific settings
        self.therm_id    = None   # ID for this thermostat (set by looking up the name)
        self.therm_name  = "Family Room Thermostat (Living Room)" # Nest name_long
        self.therm_temp  = 0  # Degrees F thermostat is set to (default value)
        self.therm_ambient = None # Degrees F thermostat has detected
        self.therm_mode  = None  # Mode thermostat is set to: off, heat, cool
        self.therm_state = None  # Current state: off, heating, cooling

        # GPIO specific settings
        self.gpio_cool    = 0x10
        self.gpio_mask    = self.gpio_cool
        self.ac_status    = False
        self.last_gpio    = None

        # In an unknown init stage...
        self.init = True

    def _action(self, ifttt_action, args=None):
        (action, retry) = ifttt_action
        if args:
            action = action % (args)
        self.ifttt.send_action(action, retry)

    def turn_on_ac(self):
        if self.ac_on != True:
            self._action(self.ifttt_on)
            self.ac_on = True

    def turn_off_ac(self):
        if self.ac_on != True:
            self._action(self.ifttt_off)
            self.ac_on = False

    def turn_on_cooling(self):
        if self.ac_on and self.ac_cooling != True:
            self._action(self.ifttt_cool)
            self.ac_cooling = True
            self.set_ac_temp()

    def turn_off_cooling(self):
        if self.ac_on and self.ac_cooling != False:
            self._action(self.ifttt_eco)
            self.ac_cooling = False
            self.set_ac_temp()

    def set_ac_temp(self):
        if self.ac_on != True:
            self.ac_temp = 0
            return

        therm_target = self.therm_temp
        if therm_target == 0:
            therm_target = self.ac_temp_default  # reasonable default

        if self.ac_cooling:
            # There are cases when the nest might call for cooling
            # where the set temp is higher then ambient, compensate for this
            if self.therm_ambient and self.therm_ambient < therm_target:
                therm_target = self.therm_ambient
            ac_temp = therm_target + self.ac_cooling_on_offset
        else:
            ac_temp = therm_target + self.ac_cooling_off_offset

        if ac_temp < self.ac_min:
            ac_temp = self.ac_min

        if ac_temp > self.ac_max:
            ac_temp  = self.ac_max

        if ac_temp != self.ac_temp:
            self.ac_temp = ac_temp
            self._action(self.ifttt_temp, self.ac_temp)


    def init_nest(self):
        (updated, thermostats) = self.nest.getThermostats()
        for id in thermostats:
            thermostat = thermostats[id]

            if thermostat['name_long'] == self.therm_name:
                self.therm_id = id
                break

        return self.therm_id

    def update_nest(self, thermostats):
        if not self.therm_id:
            if not self.init_nest():
                return

        thermostat = thermostats[self.therm_id]

        status = thermostat['hvac_mode']
        if status != 'off':
            if thermostat['hvac_state'] != 'off':
                status = '%s (%sm) to %s' % (thermostat['hvac_state'], thermostat['time_to_target'], thermostat['target_temperature_f'])
            else:
                status = '%s to %s' % (thermostat['hvac_mode'], thermostat['target_temperature_f'])

        print("LR: %s: %s (current %sF %s%%)" % (thermostat['name'], status,
                 thermostat['ambient_temperature_f'],
                 thermostat['humidity']))

        self.set_nest_mode(thermostat['hvac_mode'])
        self.set_nest_state(thermostat['hvac_state'])
        self.set_nest_ambient(thermostat['ambient_temperature_f'])
        self.set_nest_temp(thermostat['target_temperature_f'])

    def set_nest_mode(self, mode):
        if self.therm_mode != mode:
            if mode == "off":
                self.turn_off_ac()
            elif mode == "heat":
                self.turn_off_ac()
            elif mode == "cool" or mode == "heat-cool":
                self.turn_on_ac()
            else:
                raise Exception("Unknown mode: %s" % mode)

            self.therm_mode = mode

    def set_nest_state(self, mode):
        if self.therm_state != mode:
            self.therm_state = mode

    def set_nest_ambient(self, temp):
        self.therm_ambient = temp
 
    def set_nest_temp(self, temp):
        if self.therm_temp != temp:
            self.therm_temp = temp
            self.set_ac_temp()


    def update_gpio(self, gpio_lines):
        # It may be too early to process this...
        if gpio_lines is None:
            return

        gpio_lines = gpio_lines & self.gpio_mask

        try:
            if self.last_gpio == gpio_lines:
                return

            if self.last_gpio is None and self.ac_on is None:
                # First time through, no idea the state of the air con unit...
                # We assume it should be turned -on-...  The nest will 'correct' this
                # once it has initialized...
                self.turn_on_ac()

            if self.last_gpio is None or (gpio_lines & self.gpio_cool) != (self.last_gpio & self.gpio_cool):
                if not gpio_lines & self.gpio_cool:
                    self.turn_on_cooling()
                elif gpio_lines & self.gpio_cool:
                    self.turn_off_cooling()
        finally:
            self.last_gpio = gpio_lines

    def run(self):
        self.init_nest()

        livingroom_gpio = threading.Event()
        livingroom_nest = threading.Event()

        self.gpio.registerEvent(livingroom_gpio)
        self.nest.registerEvent(livingroom_nest)

        last_updated = 0

        # Give the other threads a chance to update and generate
        # events
        sleep(2)

        while True:
            # Process the nest first, so we can hopefully setup the state
            # of the HVAC system...
            event = livingroom_nest.wait(.1)
            if event:
                livingroom_nest.clear()
                (updated, thermostats) = self.nest.getThermostats()
                if updated and self.therm_id:
                    if updated[self.therm_id] <= last_updated:
                        continue
                    else:
                        last_updated = updated[self.therm_id]
                self.update_nest(thermostats)

            # Process the GPIO even if the NEST isn't ready
            # it will have to assume some basic info...
            event = livingroom_gpio.wait(.1)
            if event:
                livingroom_gpio.clear()
                self.update_gpio(self.gpio.getGpio())

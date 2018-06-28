# Individual device configurations
#
# This drives the models/algorithms to manage individual zones
# (actual zone info is in a class per-zone elsewhere)
#
# Written by Mark Hatle <mark@hatle.net>
# Copyright (C) 2018 Mark Hatle
#
# All of the items here are licensed under the GNU General Public License 2.0,
# unless otherwise noted.  See COPYING for further details.
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
import logging

class Zone():
    # The class that uses this MUST set has_heat, has_cool, has_fan
    # ifttt_* actions, and therm_name
    def __init__(self, nest=None, gpio=None, ifttt=None):
        self.logger = logging.getLogger('HVAC.Zone')

        self.nest        = nest
        self.gpio        = gpio
        self.ifttt       = ifttt

        self.has_heat    = False  # IFTTT controllable (secondary) heat
        self.has_cool    = False  # IFTTT controllable cooling
        self.has_fan     = False  # IFTTT controllable fan

        # ifff action and response retry value (0 = no wait for an activation, assume it worked)
        self.ifttt_heat_on  = None
        self.ifttt_heat_off = None
        self.ifttt_cool_on  = None
        self.ifttt_cool_off = None
        self.ifttt_fan_on   = None
        self.ifttt_fan_off  = None

        self.ifttt_cooling_on   = None
        self.ifttt_cooling_off  = None
        self.ifttt_cooling_temp = None

        self.ifttt_heating_on   = None
        self.ifttt_heating_off  = None
        self.ifttt_heating_temp = None

        # Current zone settings
        self.fan_on       = None  # Is the fan on or off?

        self.heat_on      = None  # Is the heater on or off?
        self.heating_on   = None  # Are we currenting heating?
        self.heating_temp = 0
        self.heating_min  = 0
        self.heating_max  = 100
        self.heating_default = 70
        self.heating_on_offset  =  2 # When heating raise temp N degrees
        self.heating_off_offset = -2 # When NOT heating drop temp by N degrees

        self.ac_on       = None  # Is the air conditioner on or off?
        self.ac_cooling  = None  # Is the air conditioner cooling?
        self.ac_temp     = 0     # Degrees F to set the AC unit to
        self.ac_min      = 64
        self.ac_max      = 80
        self.ac_temp_default = 70  # Default temp if no info from the thermostat
        self.ac_cooling_on_offset  = -2 # When cooling drop temp by N degrees
        self.ac_cooling_off_offset =  2 # When NOT cooling raise temp by N degrees

        # Nest specific settings
        self.therm_id      = None  # ID for this thermostat (set by looking up the name)
        self.therm_name    = None  # Nest name_long
        self.therm_temp    = 0     # Degrees F thermostat is set to (default value)
        self.therm_ambient = None  # Degrees F thermostat has detected
        self.therm_mode    = None  # Mode thermostat is set to: off, heat, cool
        self.therm_state   = None  # Current state: off, heating, cooling

        # GPIO specific settings
        self.gpio_cool    = 0x0
        self.gpio_heat    = 0x0
        self.gpio_fan     = 0x0
        self.last_gpio    = None

    def _action(self, ifttt_action, args=None):
        if ifttt_action is None:
            # Action not implemented...
            return

        (action, retry) = ifttt_action
        if args:
            action = action % (args)
        self.ifttt.send_action(action, retry)

    def turn_on_fan(self):
        if self.has_fan and self.fan_on != True:
            self._action(self.ifttt_fan_on)
            self.fan_on = True

    def turn_off_fan(self):
        if self.has_fan and self.fan_on != False:
            self._action(self.ifttt_fan_off)
            self.fan_on = False

    def turn_on_heat(self):
        if self.has_heat and self.heat_on != True:
            self._action(self.ifttt_heat_on)
            self.heat_on = True

    def turn_off_heat(self):
        if self.has_heat and self.heat_on != False:
            self._action(self.ifttt_head_off)
            self.heat_on = False

    def turn_on_heating(self):
        if self.has_heat and self.heat_on and self.heating != True:
            self._action(self.ifttt_heating_on)
            self.heating = True
            self.set_heat_temp()

    def turn_off_heating(self):
        if self.has_heat and self.heat_on and self.heating != False:
            self._action(self.ifttt_heating_off)
            self.heating = False
            self.set_heat_temp()

    def set_heat_temp(self, force=False):
        if not self.has_heat or self.heat_on != True:
            self.heating_temp = 0
            return

        therm_target = self.therm_temp
        if therm_target == 0:
            therm_target = self.heating_default  # reasonable default

        if self.heating:
            # There are cases when the nest might call for heating
            # where the set temp is higher then ambient, compensate for this
            if self.therm_ambient and self.therm_ambient > therm_target:
                therm_target = self.therm_ambient
            target_temp = therm_target + self.heating_on_offset
        else:
            target_temp = therm_target + self.heating_off_offset

        if target_temp < self.heating_min:
            target_temp = self.heating_min

        if target_temp > self.heating_max:
            target_temp  = self.heading_max

        if force or (target_temp != self.target_temp):
            self.heating_temp = target_temp
            self._action(self.ifttt_heating_temp, self.heating_temp)


    def turn_on_ac(self):
        if self.has_cool and self.ac_on != True:
            self._action(self.ifttt_cool_on)
            self.ac_on = True

    def turn_off_ac(self):
        if self.has_cool and self.ac_on != False:
            self._action(self.ifttt_cool_off)
            self.ac_on = False

    def turn_on_cooling(self):
        if self.has_cool and self.ac_on and self.ac_cooling != True:
            self._action(self.ifttt_cooling_on)
            self.ac_cooling = True
            # Whenever we change modes, we MUST set the temp
            self.set_ac_temp(force=True)

    def turn_off_cooling(self):
        if self.has_cool and self.ac_on and self.ac_cooling != False:
            self._action(self.ifttt_cooling_off)
            self.ac_cooling = False
            # Whenever we change modes, we MUST set the temp
            self.set_ac_temp(force=True)

    def set_ac_temp(self, force=False):
        if not self.has_cool or self.ac_on != True:
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
            target_temp = therm_target + self.ac_cooling_on_offset
        else:
            target_temp = therm_target + self.ac_cooling_off_offset

        if target_temp < self.ac_min:
            target_temp = self.ac_min

        if target_temp > self.ac_max:
            target_temp  = self.ac_max

        if force or (target_temp != self.ac_temp):
            self.ac_temp = target_temp
            self._action(self.ifttt_cooling_temp, self.ac_temp)

    def turn_on_fan(self):
        if self.has_fan and self.fan_on != True:
            self._action(self.ifttt_fan_on)
            self.fan_on = True

    def turn_off_fan(self):
        if self.has_fan and self.fan_on != False:
            self._action(self.ifttt_fan_off)
            self.fan_on = False


    def init_nest(self, thermostats):
        if not self.therm_name:
            raise Exception("No thermostat 'name_long' (self.therm_name) defined!")

        for id in thermostats:
            thermostat = thermostats[id]

            if thermostat['name_long'] == self.therm_name:
                self.therm_id = id
                break

        if not self.therm_id:
            msg = "Thermostat %s not found!\nAvailable thermostats:\n" % (self.therm_name)
            for id in thermostats:
                msg += "  %s\n" % (thermostats[id]['name_long'])
            self.logger.error(msg)

        return self.therm_id

    def update_nest(self, thermostats):
        if not self.therm_id:
            if not self.init_nest(thermostats):
                self.logger.error("Thermostat not found for %s!" % self.therm_name)
                return

        thermostat = thermostats[self.therm_id]

        self.set_nest_has_fan(thermostat['has_fan'])
        self.set_nest_has_cool(thermostat['can_cool'])
        self.set_nest_has_heat(thermostat['can_heat'])
        self.set_nest_ambient(thermostat['ambient_temperature_f'])

        # Note in heat-cool mode the temps are managed differently
        # not yet implemented...
    
        # For now we just track the 'high' temp, which is cooling...
        if self.therm_mode == "heat-cool" or self.therm_mode == "eco":
            self.set_nest_temp(thermostat['target_temperature_high_f'])
        else:
            self.set_nest_temp(thermostat['target_temperature_f'])

        # We need to set the mode -after- the temp, so on startup we don't end up sending
        # it twice...
        self.set_nest_mode(thermostat['hvac_mode'])
        self.set_nest_state(thermostat['hvac_state'])

        status = self.therm_mode
        if status != 'off':
            if self.therm_state != 'off':
                status = '%s (%sm) to %s' % (self.therm_state, thermostat['time_to_target'], self.therm_temp)
            else:
                status = '%s to %s' % (self.therm_mode, self.therm_temp)

        self.logger.info("%s: %s (current %sF %s%%)" % (self.therm_name, status,
                 thermostat['ambient_temperature_f'],
                 thermostat['humidity']))

    def set_nest_has_fan(self, fan):
        if self.has_fan != fan:
            self.has_fan = fan

    def set_nest_has_cool(self, cool):
        if self.has_cool != cool:
            self.has_cool = cool

    def set_nest_has_heat(self, heat):
        if self.has_cool != heat:
            self.has_cool = heat

    def set_nest_mode(self, mode):
        if self.therm_mode != mode:
            if mode == "off":
                self.turn_off_ac()
                self.turn_off_heat()
            elif mode == "heat":
                self.turn_off_ac()
                self.turn_on_heat()
            elif mode == "cool":
                self.turn_on_ac()
                self.turn_off_heat()
            elif mode == "heat-cool" or mode == "eco":
                self.logger.warning("eco/heat-cool mode not implemented!")
                self.turn_on_ac()
                self.turn_on_heat()
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
            self.set_ac_temp(temp)
            self.set_heat_temp(temp)

    def update_gpio(self, gpio_lines):
        # It may be too early to process this...
        if gpio_lines is None:
            return

        gpio_lines = gpio_lines & self.gpio_mask

        try:
            if self.last_gpio == gpio_lines:
                return

            # Cooling
            if (self.gpio_cool != 0) and (self.last_gpio is None or (gpio_lines & self.gpio_cool) != (self.last_gpio & self.gpio_cool)):
                if not gpio_lines & self.gpio_cool:  #  0 is cooling
                    # GPIO always overrules the Nest...
                    if self.ac_on is None:
                        # First time through, no idea the state of the air con unit...
                        self.has_cool = True
                        self.turn_on_ac()
                    self.turn_on_cooling()
                elif gpio_lines & self.gpio_cool:    # !0 is off
                    self.turn_off_cooling()

            # Heating
            if (self.gpio_heat != 0) and (self.last_gpio is None or (gpio_lines & self.gpio_heat) != (self.last_gpio & self.gpio_heat)):
                if not gpio_lines & self.gpio_heat:  #  0 is heating
                    # GPIO always overrules the Nest...
                    if self.heat_on is None:
                        # First time through, no idea the state of the air con unit...
                        self.has_heat = True
                        self.turn_on_heat()
                    self.turn_on_heating()
                elif gpio_lines & self.gpio_heat:    # !0 is off
                    self.turn_off_heating()

            # Fan
            if (self.gpio_fan != 0) and (self.last_gpio is None or (gpio_lines & self.gpio_fan) != (self.last_gpio & self.gpio_fan)):
                if not gpio_lines & self.gpio_fan:  #  0 is fan on
                    # GPIO always overrules the Nest...
                    if self.fan_on is None:
                        # First time through, no idea the state of the air con unit...
                        self.has_fan = True
                        self.turn_on_fan()
                    self.turn_on_fan()
                elif gpio_lines & self.gpio_fan:    # !0 is off
                    self.turn_off_fan()

        finally:
            self.last_gpio = gpio_lines

    def run(self):
        self.gpio_mask    = self.gpio_cool | self.gpio_heat | self.gpio_fan

        zone_event = threading.Event()
        zone_gpio  = threading.Event()
        zone_nest  = threading.Event()

        self.gpio.registerEvent(zone_event)
        self.gpio.registerEvent(zone_gpio)

        self.nest.registerEvent(zone_event)
        self.nest.registerEvent(zone_nest)

        # Give the system a chance to start up and query
        sleep(5)

        # Start off by parsing everything
        zone_event.set()
        zone_gpio.set()
        zone_nest.set()

        last_updated = 0

        while True:
            event = zone_event.wait(60)
            if not event:
                continue
            zone_event.clear()

            # Process the nest first, so we can hopefully setup the state
            # of the HVAC system...
            event = zone_nest.wait(.1)
            if event:
                zone_nest.clear()
                (updated, thermostats) = self.nest.getThermostats()
                if updated and self.therm_id:
                    if updated[self.therm_id] <= last_updated:
                        continue
                    else:
                        last_updated = updated[self.therm_id]
                self.update_nest(thermostats)

            if not self.therm_id:
                self.logger.debug("Waiting for Nest data to start up zone GPIO control...")
                continue

            # Process the GPIO even if the NEST isn't ready
            # it will have to assume some basic info...
            event = zone_gpio.wait(.1)
            if event:
                zone_gpio.clear()
                self.update_gpio(self.gpio.getGpio())

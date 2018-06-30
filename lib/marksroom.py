# Individual device configuration: Mark's Room
#
# This drives the models/algorithms to manage my bedroom
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

from zone import Zone

import datetime
import logging

class MarksRoom(Zone):
    def __init__(self, nest=None, gpio=None, ifttt=None):
        Zone.__init__(self, nest=nest, gpio=gpio, ifttt=ifttt)

        self.logger = logging.getLogger('HVAC.Zone.MarksRoom')

        self.display_name = "Mark's Room"

        # ifff action and response retry value (0 = no wait for an activation, assume it worked)
        self.ifttt_cool_on      = ( "marksroom_ac_on", 0 )
        self.ifttt_cool_off     = ( "marksroom_ac_off", 0 )
        self.ifttt_cooling_on   = ( "marksroom_ac_cool", 30 )
        self.ifttt_cooling_off  = ( "marksroom_ac_eco", 30 )
        self.ifttt_cooling_temp = ( "marksroom_ac_set_%s", 0 )

        self.ifttt_cooling_fan_auto = ( "marksroom_ac_fan_auto", 0 )
        self.ifttt_cooling_fan_high = ( "marksroom_ac_fan_high", 0 )
        self.ifttt_cooling_fan_med  = ( "marksroom_ac_fan_med", 0 )
        self.ifttt_cooling_fan_low  = ( "marksroom_ac_fan_low", 0 )

        #self.ifttt_fan_on       = ( "marksroom_fan_on", 0)
        #self.ifttt_fan_off      = ( "marksroom_fan_off", 0)

        # Current Bedroom Room settings
        # GE (Haier) AEC08LX 8,000BTU 120V
        self.ac_min      = 64
        self.ac_max      = 86
        self.ac_temp_default = 70  # Default temp if no info from the thermostat
        self.ac_cooling_on_offset  = -10 # When cooling drop temp by N degrees
        self.ac_cooling_off_offset =  2 # When NOT cooling raise temp by N degrees
        self.ac_cooling_fan = None

        # Nest specific settings
        self.therm_name  = "Master Bedroom Thermostat (Mark's Bedroom)" # Long Name

        # GPIO specific settings
        self.gpio_cool    = 1 << 4
        self.gpio_fan     = 1 << 5

    # At night we want the fan to stay on low, faster the fan the louder it
    # is.  I just wish there was a way to turn off the 'beep' when it changes
    # modes and/or temps.
    def cooling_fan_speed(self, mode):
        if self.ac_cooling_fan != mode:
            self.ac_cooling_fan = mode
            if mode == "low":
                self._action(self.ifttt_cooling_fan_low)
            elif mode == "med":
                self._action(self.ifttt_cooling_fan_med)
            elif mode == "high":
                self._action(self.ifttt_cooling_fan_high)
            else:
                self._action(self.ifttt_cooling_fan_auto)

    def turn_on_cooling(self):
        Zone.turn_on_cooling(self)
        if self.ac_cooling == True:
            hour = datetime.datetime.now()
            if hour.hour >= 22 or hour.hour < 8:    # 10pm to 8am
                self.cooling_fan_speed('low')
            elif hour.hour >= 10 and hour.hour < 18: # 10am to 6pm
                self.cooling_fan_speed('high')
            else:                                # 8am to 10am and 6pm to 10pm
                self.cooling_fan_speed('auto')

    def turn_off_cooling(self):
        Zone.turn_off_cooling(self)
        if self.ac_cooling == False:
            hour = datetime.datetime.now()
            # If it's between 10pm and 8am, set the fan to -low-
            if hour.hour >= 22 or hour.hour < 8:    # 10pm to 8am
                self.cooling_fan_speed('low')
            else:
                self.cooling_fan_speed('auto')


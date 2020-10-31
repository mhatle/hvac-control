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

from zone import Zone
import logging

class LivingRoom(Zone):
    def __init__(self, nest=None, gpio=None, ifttt=None):
        Zone.__init__(self, nest=nest, gpio=gpio, ifttt=ifttt)

        self.logger = logging.getLogger('HVAC.Zone.LivingRoom')

        self.display_name = "Living Room"

        # ifff action and response retry value (0 = no wait for an activation, assume it worked)
        self.ifttt_cool_on      = ( "livingroom_ac_on", 0 )
        self.ifttt_cool_off     = ( "livingroom_ac_off", 0 )
        self.ifttt_cooling_on   = ( "livingroom_ac_cool", 30 )
        self.ifttt_cooling_off  = ( "livingroom_ac_eco", 30 )
        self.ifttt_cooling_temp = ( "livingroom_ac_set_%s", 0 )

        self.ifttt_heating_on   = ( "livingroom_heat_on", 0 )
        self.ifttt_heating_off   = ( "livingroom_heat_off", 0 )

        # Current Living Room settings
        # GE (Haier) AEC10AX 10,000BTU 120V
        self.ac_min      = 64
        self.ac_max      = 86
        self.ac_temp_default = 70  # Default temp if no info from the thermostat
        self.ac_cooling_on_offset  = -10 # When cooling drop temp by N degrees
        self.ac_cooling_off_offset =  2 # When NOT cooling raise temp by N degrees

        # Nest specific settings
        self.therm_name  = "Living Room Thermostat" # Nest name_long

        # GPIO specific settings
        self.gpio_cool    = 1 << 2 # Living room cool stage 1
        self.gpio_heat    = 1 << 6 # Living room heat stage 2

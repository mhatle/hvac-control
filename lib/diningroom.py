# Individual device configuration: Livingroom
#
# This drives the models/algorithms to manages the third stage heating
# of the living room.  The room next door, the 'dining room', contains another
# plugin heater and will be treated as 'stage three' for the living room
# thermostat.  It only needs to come on if extra heating is required.
#
# Written by Mark Hatle <mark@hatle.net>
# Copyright (C) 2019 Mark Hatle
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

class DiningRoom(Zone):
    def __init__(self, nest=None, gpio=None, ifttt=None):
        Zone.__init__(self, nest=nest, gpio=gpio, ifttt=ifttt)

        self.logger = logging.getLogger('HVAC.Zone.DiningRoom')

        self.display_name = "Dining Room"

        # ifff action and response retry value (0 = no wait for an activation, assume it worked)
        self.ifttt_heating_on   = ( "dining_room_heat_on", 0 )
        self.ifttt_heating_off   = ( "dining_room_heat_off", 0 )

        # Nest specific settings
        # Since the room is shared with the living room, we use this
        # as the basis of which mode we're in.
        self.therm_name  = "Living Room Thermostat" # Nest name_long

        # GPIO specific settings
        self.gpio_heat    = 1 << 1  # Living room heat stage 3

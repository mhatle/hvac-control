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

import logging

from lib import nest
from lib import gpio
from lib import ifttt
from lib import livingroom
from lib import catroom
from lib import marksroom
from lib import amysroom

import settings

import threading

from time import sleep

def main():
    logger = logging.getLogger('HVAC')
    logger.setLevel(logging.DEBUG)

    filehandle = logging.FileHandler('hvac.log')
    filehandle.setLevel(logging.DEBUG)

    consolehandle = logging.StreamHandler()
    consolehandle.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    filehandle.setFormatter(formatter)

    logger.addHandler(filehandle)
    logger.addHandler(consolehandle)

    logger.info("HVAC Control Software v0.4")
    logger.info("Copyright (C) 2018 Mark Hatle")
    logger.info("See the source code for licensing terms and conditions.")

    gpio_obj = gpio.Gpio(settings.GPIO_SERIAL)
    nest_obj = nest.Nest(settings.NEST_TOKEN)
    ifttt_obj = ifttt.IFTTT(settings.IFTTT_TOKEN)

    livingroom_obj = livingroom.LivingRoom(nest_obj, gpio_obj, ifttt_obj)
    catroom_obj = catroom.CatRoom(nest_obj, gpio_obj, ifttt_obj)
    amysroom_obj = amysroom.AmysRoom(nest_obj, gpio_obj, ifttt_obj)
    marksroom_obj = marksroom.MarksRoom(nest_obj, gpio_obj, ifttt_obj)

    gpio_thread = threading.Thread(target=gpio_obj.run)
    nest_thread = threading.Thread(target=nest_obj.run, args=(True,))
    ifttt_thread = threading.Thread(target=ifttt_obj.run)

    livingroom_thread = threading.Thread(target=livingroom_obj.run)
    catroom_thread = threading.Thread(target=catroom_obj.run)
    amysroom_thread = threading.Thread(target=amysroom_obj.run)
    marksroom_thread = threading.Thread(target=marksroom_obj.run)

    # Process for ongoing status
    gpio_thread.daemon = True
    nest_thread.daemon = True
    ifttt_thread.daemon = True
    livingroom_thread.daemon = True
    catroom_thread.daemon = True
    amysroom_thread.daemon = True
    marksroom_thread.daemon = True

    gpio_thread.start()
    nest_thread.start()
    ifttt_thread.start()
    livingroom_thread.start()
    catroom_thread.start()
    amysroom_thread.start()
    marksroom_thread.start()

    while True:
        sleep(60)

if __name__ == '__main__':
    main()

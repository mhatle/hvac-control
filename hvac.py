#! /usr/bin/env python
#
# This is the HVAC control software written for my own home integration.
# The software bridges the Nest thermostats, an 8-port Numato GPIO board, the
# IFTTT service, all to control heating and cooling within the home.
#
# Written by Mark Hatle <mark@hatle.net>
# Copyright (C) 2018-2019 Mark Hatle
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
from lib import diningroom
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
    logger.info("Copyright (C) 2018-2019 Mark Hatle")
    logger.info("See the source code for licensing terms and conditions.")

    gpio_obj = gpio.Gpio(settings.GPIO_SERIAL)
    nest_obj = nest.Nest(settings.NEST_TOKEN)
    ifttt_obj = ifttt.IFTTT(settings.IFTTT_TOKEN)

    livingroom_obj = livingroom.LivingRoom(nest_obj, gpio_obj, ifttt_obj)
    catroom_obj = catroom.CatRoom(nest_obj, gpio_obj, ifttt_obj)
    diningroom_obj = diningroom.DiningRoom(nest_obj, gpio_obj, ifttt_obj)
    amysroom_obj = amysroom.AmysRoom(nest_obj, gpio_obj, ifttt_obj)
    marksroom_obj = marksroom.MarksRoom(nest_obj, gpio_obj, ifttt_obj)

    gpio_thread = None
    nest_thread = None
    ifttt_thread = None

    livingroom_thread = None
    catroom_thread = None
    diningroom_thread = None
    amysroom_thread = None
    marksroom_thread = None

    while True:
        if not gpio_thread or not gpio_thread.isAlive():
            if gpio_thread:
                logger.error('GPIO Thread failed, restarting')
            else:
                logger.info('Starting GPIO Thread')
            gpio_thread = threading.Thread(target=gpio_obj.run)
            gpio_thread.daemon = True
            gpio_thread.start()

        if not nest_thread or not nest_thread.isAlive():
            if nest_thread:
                logger.error('Works with Nest Thread failed, restarting')
            else:
                logger.info('Starting Works with Nest Thread')
            nest_thread = threading.Thread(target=nest_obj.run, args=(True,))
            nest_thread.daemon = True
            nest_thread.start()

        if not ifttt_thread or not ifttt_thread.isAlive():
            if ifttt_thread:
                logger.error('IFTTT Thread failed, restarting')
            else:
                logger.info('Starting IFTTT Thread')
            ifttt_thread = threading.Thread(target=ifttt_obj.run)
            ifttt_thread.daemon = True
            ifttt_thread.start()

        if not livingroom_thread or not livingroom_thread.isAlive():
            if livingroom_thread:
                logger.error('livingroom Thread failed, restarting')
            else:
                logger.info('Starting livingroom Thread')
            livingroom_thread = threading.Thread(target=livingroom_obj.run)
            livingroom_thread.daemon = True
            livingroom_thread.start()

        if not catroom_thread or not catroom_thread.isAlive():
            if catroom_thread:
                logger.error('catroom Thread failed, restarting')
            else:
                logger.info('Starting catroom Thread')
            catroom_thread = threading.Thread(target=catroom_obj.run)
            catroom_thread.daemon = True
            catroom_thread.start()

        if not diningroom_thread or not diningroom_thread.isAlive():
            if diningroom_thread:
                logger.error('diningroom Thread failed, restarting')
            else:
                logger.info('Starting diningroom Thread')
            diningroom_thread = threading.Thread(target=diningroom_obj.run)
            diningroom_thread.daemon = True
            diningroom_thread.start()

        if not amysroom_thread or not amysroom_thread.isAlive():
            if amysroom_thread:
                logger.error('amysroom Thread failed, restarting')
            else:
                logger.info('Starting amysroom Thread')
            amysroom_thread = threading.Thread(target=amysroom_obj.run)
            amysroom_thread.daemon = True
            amysroom_thread.start()

        if not marksroom_thread or not marksroom_thread.isAlive():
            if marksroom_thread:
                logger.error('marksroom Thread failed, restarting')
            else:
                logger.info('Starting marksroom Thread')
            marksroom_thread = threading.Thread(target=marksroom_obj.run)
            marksroom_thread.daemon = True
            marksroom_thread.start()

        sleep(60)

if __name__ == '__main__':
    main()

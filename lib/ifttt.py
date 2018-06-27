# IFTTT control (bi-directional) for managing HVAC devices
#
# This module uses the 'webhooks' interface, and also assumes the local machine
# can be used for status updates via a corresponding cgi-bin/named-pipe.
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

import urllib2
from time import sleep
import threading
import os
import stat
import logging

class IFTTT():
    def __init__(self, token):
        self.logger = logging.getLogger('HVAC.IFTTT')

        self.lock = threading.Lock()

        try:
            self.lock.acquire()

            self.ifttt_token = token
            self.ifttt_url   = "https://maker.ifttt.com/trigger/%s/with/key/{0}".format(self.ifttt_token)
            self.ifttt_actions = {}     # action : retry_timeout [if not acknowledged]

        finally:
            self.lock.release()

    # retry of 0 means don't retry, otherwise it's the number of seconds to
    # wait for a confirmation (via the named pipe/fifo)
    def send_action(self, action, retry=0):
        def _http_request(action):
            while True:
                try:
                    res = urllib2.urlopen(urllib2.Request(self.ifttt_url % (action)))
                    self.logger.debug("result: %s" % res.read())
                    break
                except urllib2.HTTPError as e:
                    self.logger.error("HTTP Error: %s: %s" % (e.code, e.reason))
                    self.logger.debug(" Requested: %s" % (self.ifttt_url % (action)))
                    self.logger.debug(" Actual:    %s" % (e.geturl()))
                    sleep(5)
                except urllib2.URLError as e:
                    self.logger.error('URLError: %s %s' % (self.ifttt_url % (action), e))
                    sleep(5)

            return res

        self.logger.info("Sending ifttt %s" % action)

        try:
            self.lock.acquire()
            if action in self.ifttt_actions:
                del self.ifttt_actions[action]
        finally:
            self.lock.release()

        res = _http_request(action)

        if retry > 0:
            try:
                self.lock.acquire()
                self.ifttt_actions[action] = retry
            finally:
                self.lock.release()
        sleep(1)

    def run(self, wait_time=10, pipe_name='/var/www/cgi-bin/hvac-fifo'):
        if not os.path.exists(pipe_name):
            raise Exception('no fifo: %s' % pipe_name)

        while True:
            with open(pipe_name, 'r') as fifo:
                while True:
                    action = fifo.readline().strip()
                    if len(action) == 0:
                        break

                    self.logger.debug("Clear action: %s" % action)
                    try:
                        self.lock.acquire()
                        if action in self.ifttt_actions:
                            del self.ifttt_actions[action]
                    finally:
                        self.lock.release()

            self.logger.debug("Action list:")
            for action in self.ifttt_actions:
                 self.logger.debug(action)

            sleep(wait_time)

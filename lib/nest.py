# Communicate with the Nest developer API via either polling or streaming
# protocol (Works with Nest API)
#
# See: https://developers.nest.com
#
# Note: the REST_streaming interface is based on the examples provided by Nest
# it is my interpretation of those examples, so there may be similarities with
# the original example code.
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

import json
import copy
import threading

class Nest():
    def __init__(self, token, url='https://developer-api.nest.com'):
        self.lock = threading.Lock()     # Thread lock for the data

        try:
            self.lock.acquire()

            self.nest_url = url
            self.nest_token = token
            self.thermostats = {}
            self.updated = {}
            self.events = []     # Thread events when data is updated
        finally:
            self.lock.release()

    def registerEvent(self, event):
        if event not in self.events:
            self.events.append(event)

    def deregisterEvent(self, event):
        if event in self.events:
            self.events.remove(event)

    def REST(self):
        import urllib2

        header = {
                   'Content-Type' : 'application/json',
                   'Authorization' : 'Bearer {0}'.format(self.nest_token)
                 }

        res = urllib2.urlopen(urllib2.Request(self.nest_url, headers=header))
        return res.read()

    def REST_Streaming(self):
        import sseclient # see install information below
        import urllib3

        def get_event_stream():
            # Must use this version for sseclient for this sample
            #   https://github.com/mpetazzoni/sseclient
            import sseclient
            import urllib3

            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

            """ Start REST streaming device events given a Nest token.  """
            request_url = self.nest_url
            while True:
                http = urllib3.PoolManager()
                headers = {
                    'Accept': 'text/event-stream',
                    'Authorization': "Bearer {0}".format(self.nest_token)
                }
                response = http.request('GET', request_url, headers=headers, preload_content=False, retries=False)

                if response.status == 307:
                    print response.get_redirect_location()
                    request_url = response.get_redirect_location()
                    continue

                if response.status == 401:
                    raise exception('Authentication Problem: 401')

                break

            client = sseclient.SSEClient(response)
            return client

        client = get_event_stream()
        for event in client.events(): # returns a generator
            event_type = event.event
            if event_type == 'open': # not always received here
                pass
            elif event_type == 'put':
                yield event.data
            elif event_type == 'keep-alive':
                #print "No data updates. Receiving an HTTP header to keep the conne$
                pass
            elif event_type == 'auth_revoked' or event_type == 'cancel' :
                print "revoked token: ", event
                yield '%s' %  json.dumps(err.result)
            elif event_type == 'error':
                print "error message: ", event.data # check if contains error code
                yield '%s' %  json.dumps({"error": event.data})
            else:
                raise exception("Unknown event, no handler for it.")

    def getThermostats(self):
        try:
            self.lock.acquire()
            updated = copy.deepcopy(self.updated)
            thermostats = copy.deepcopy(self.thermostats)
        finally:
            self.lock.release()

        return (updated, thermostats)

    def load(self, data):
        updated = False

        try:
            self.lock.acquire()
            # Sometimes the real data is under a data element
            if 'data' in data:
                data = data['data']

            # We only process thermostats
            if not ('devices' in data and 'thermostats' in data['devices']):
                print("Invalid data: %s" % data)
                return

            for id in data['devices']['thermostats']:
                thermostat = data['devices']['thermostats'][id]

                if not (id in self.thermostats):
                    self.thermostats[id] = {}
                    self.updated[id] = 0

                for element in thermostat:
                    if element not in self.thermostats[id] or \
                       self.thermostats[id][element] != thermostat[element]:
                        self.thermostats[id][element] = thermostat[element]

                        # We only care about fields changing, not the connection time
                        if element != "last_connection":
                            self.updated[id] += 1
                            updated = True
        finally:
            self.lock.release()
            if updated:
                for event in self.events:
                    event.set()


    # run the nest API watcher.
    # streaming = True/False - use the REST or Streaming APIs
    # wait_time, when using REST how often do wait to poll?
    def run(self, streaming=False, wait_time=150):
        from time import sleep

        if streaming == False:
            while True:
                result = self.REST()
                data = json.loads(result)
                self.load(data)
                sleep(wait_time)

        for result in self.REST_Streaming():
            data = json.loads(result)
            self.load(data)

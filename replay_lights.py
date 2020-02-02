import appdaemon.plugins.hass.hassapi as hass
import sqlite3
import os
import json
from datetime import datetime
from datetime import timedelta

#
# Replay Light History when Away
#
# Args: Number of days back to replay
#

class ReplayLights(hass.Hass):

  def initialize(self):
     self.log("started")
     self.numberOfDaysBack = self.args["numberOfDaysBack"]
     self.run_hourly(self.scheduleNextEventBatch, datetime.now() + timedelta(seconds=5))

  def scheduleNextEventBatch(self,kwargs):
     self.log("scheduling")
     conn = sqlite3.connect('/config/home-assistant_v2.db')
     c = conn.cursor()
     for row in c.execute(f'SELECT event_data FROM events WHERE time_fired > datetime("now","localtime","-{self.numberOfDaysBack} days","+1 minutes") AND time_fired < datetime("now","localtime","-{self.numberOfDaysBack} days","+61 minutes") AND event_data like "%light%" AND NOT event_data like "%all_lights%"'):
        try:
           event = json.loads(row[0])
           entity_id = event["entity_id"]
           event_new_state = event["new_state"]["state"]
           event_trig_at = datetime.strptime(event["new_state"]["last_changed"][:-6], "%Y-%m-%dT%H:%M:%S.%f") + timedelta(days=self.numberOfDaysBack)
           self.log(f"scheduling {entity_id} to {event_new_state} at {event_trig_at}")
           self.run_at(self.executeEvent, event_trig_at, entity_id = entity_id, event_new_state = event_new_state)
        except KeyError:
           self.log(f"failed to parse {row}")


  def executeEvent(self, kwargs):
     if self.get_state("group.persons") == "home":
        self.log(f"did not turn {kwargs['entity_id']} {kwargs['event_new_state']}, someone is at home")
     else:
        self.call_service(f"light/turn_{kwargs['event_new_state']}", entity_id = kwargs['entity_id'])
        self.log(f"turned {kwargs['entity_id']} {kwargs['event_new_state']}")
               

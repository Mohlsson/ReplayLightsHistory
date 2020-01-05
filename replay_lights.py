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
     self.log("Replay Lights started")
     self.numberOfDaysBack = self.args["numberOfDaysBack"]
     self.scheduleNextEvent()


  def scheduleNextEvent(self):
     conn = sqlite3.connect('/config/home-assistant_v2.db')
     c = conn.cursor()
     c.execute(f'SELECT event_data FROM events WHERE time_fired > datetime("now","localtime","-{self.numberOfDaysBack} days","+1 second") AND event_data LIKE "%light.%" AND event_data LIKE "%entity_id%"')
     event = json.loads(c.fetchone()[0])
     self.entity_id = event["entity_id"]
     self.event_new_state = event["new_state"]["state"]
     event_trig_at = datetime.strptime(event["new_state"]["last_changed"][:-6], "%Y-%m-%dT%H:%M:%S.%f") + timedelta(days=self.numberOfDaysBack)
     self.log(f"Scheduling {self.entity_id} to {self.event_new_state} at {event_trig_at}")
     self.run_at(self.executeEvent, event_trig_at)


  def executeEvent(self, kwargs):
     if self.get_state("group.persons") == "home":
        self.log(f"Dit not turn {self.entity_id} {self.event_new_state}")
     else:
        self.call_service(f"light/turn_{self.event_new_state}", entity_id = self.entity_id)
        self.log(f"Turned {self.entity_id} to {self.event_new_state}")
     self.scheduleNextEvent()

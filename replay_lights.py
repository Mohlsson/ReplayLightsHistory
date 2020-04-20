import appdaemon.plugins.hass.hassapi as hass
import sqlite3
import os
import json
from datetime import datetime
from datetime import timedelta
from dateutil import tz

#
# Replay Light History when Away
#
# Args: Number of days back to replay
#

class ReplayLights(hass.Hass):

  def initialize(self):
     self.log("started")
     try:
        self.numberOfDaysBack = self.args["numberOfDaysBack"]
     except KeyError:
        self.numberOfDaysBack = 7
     try:
        self.devType = self.args["deviceType"]
     except KeyError:
        self.devType = "switch"
     try:
        self.enableTag = self.args["enableTag"]
     except KeyError:
        self.devType = "input_boolean.light_replay_enabled"
     try:
        self.enableVal = self.args["enableVal"]
     except KeyError:
        self.enableVal = "on"

     self.run_hourly(self.scheduleNextEventBatch, datetime.now() + timedelta(seconds=5))

  def scheduleNextEventBatch(self,kwargs):

     # set replay time based on input_number, or config file or default to 7
     try:
        days_back = int(float(self.get_state("input_number.replay_days_back")))
     except TypeError:
        days_back = self.numberOfDaysBack

     self.log("Scheduling Replaying "+str(days_back)+ " day[s] back")

     conn = sqlite3.connect('/config/home-assistant_v2.db')
     c = conn.cursor()
     for row in c.execute(f'SELECT event_data FROM events WHERE event_type="state_changed" AND time_fired > \
                          datetime("now","-{days_back} days","+1 minutes") AND \
                          time_fired < datetime("now","-{days_back} days","+61 minutes") AND \
                          event_data like "%{self.devType}%" AND NOT event_data like "%group%" AND NOT event_data like "%group%" AND NOT event_data like "%scene%"'):
        try:
           event = json.loads(row[0])
           entity_id = event["entity_id"]
           event_new_state = event["new_state"]["state"]
           # A state of unavailable happens with power is removed from a switch or plug
           if event_new_state == 'unavailable':
              event_new_state = 'off'
           # If it looks like we're trying to turn something off that is off then skip it
           if event_new_state == 'off':
              if event["old_state"] is None:
                continue

           # pull time from database.  
           event_trig_at = datetime.strptime(event["new_state"]["last_changed"][:-6], "%Y-%m-%dT%H:%M:%S.%f") + timedelta(days=days_back)
           #events are in UTC so we need to conver to local time
           from_zone = tz.tzutc()
           to_zone = tz.tzlocal()
           #first set the date so it knows it's UTC, and then update to local zone
           event_trig_at = event_trig_at.replace(tzinfo=from_zone)
           event_trig_at = event_trig_at.astimezone(to_zone)
           self.log(f"scheduling {entity_id} to {event_new_state} at {event_trig_at}")
           self.run_at(self.executeEvent, event_trig_at, entity_id = entity_id, event_new_state = event_new_state)
        except KeyError:
           self.log(f"failed to parse {row}")

     c.close()

  def executeEvent(self, kwargs):
     replay_enable = self.get_state(self.enableTag)
     if replay_enable == self.enableVal:
        self.call_service(f"{self.devType}/turn_{kwargs['event_new_state']}", entity_id = kwargs['entity_id'])
        self.log(f"turned {kwargs['entity_id']} {kwargs['event_new_state']}")
     else:
        self.log(f"did not turn {kwargs['entity_id']} {kwargs['event_new_state']} because input_boolean.light_replay_enabled is not on")

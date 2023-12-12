import appdaemon.plugins.hass.hassapi as hass
import pymysql.cursors
import sqlite3
import os
import json
from datetime import datetime
from datetime import timedelta
from datetime import datetime
import time

#
# Replay Light History when Away
#
# Args: Number of days back to replay
#

class ReplayLights(hass.Hass):

  def initialize(self):
     self.log("Starting")
     try:
        self.hassDir = self.args["hassDir"]
     except KeyError:
        self.hassDir = "/homeassistant"
        self.log("Defaulting Home Assistant config directory to {}".format(self.hassDir),level="WARNING")
     try:
         self.databaseType = self.args["databaseType"]
     except KeyError:
        self.databaseType = "sqlite3"
        self.log("Defaulting Database Type to {}".format(self.databaseType),level="WARNING")
     try:
         self.databaseHost = self.args["databaseHost"]
     except KeyError:
        self.databaseHost = "localhost"
        self.log("Defaulting Database Host to {}".format(self.databaseHost),level="WARNING")
     try:
         self.databaseUser= self.args["databaseUser"]
     except KeyError:
        if self.databaseType == 'MariaDB':
            self.databaseUser = 'homeassistant'
            self.log("Defaulting Database User to homeassistant",level="WARNING")
     try:
         self.databasePassword= self.args["databasePassword"]
     except KeyError:
        if self.databaseType == 'MariaDB':
            self.log("Database password is needed for MariaDB",level="ERROR")
     try:
         self.databaseSchema = self.args["databaseSchema"]
     except KeyError:
        self.databaseSchema = "homeassistant"
        self.log("Defaulting Database Home Assistant Schema to {}".format(self.databaseSchema),level="WARNING")
     try:
        self.numberOfDaysBack = self.args["numberOfDaysBack"]
     except KeyError:
        self.numberOfDaysBack = 7
        self.log("Defaulting Number of Days Back to {}".format(self.numberOfDaysBack),level="WARNING")
     try:
        self.devType = self.args["deviceType"]
     except KeyError:
        self.devType = "switch"
        self.log("Defaulting Device Type to {}".format(self.devType),level="WARNING")
     try:
        self.enableTag = self.args["enableTag"]
     except KeyError:
        self.enableTag = "input_boolean.light_replay_enabled"
        self.log("Defaulting Enable Tag to {}".format(self.enableTag),level="WARNING")
     try:
        self.enableVal = self.args["enableVal"]
     except KeyError:
        self.enableVal = "on"
        self.log("Defaulting Enable Tag Value to {}".format(self.enableVal),level="WARNING")
     try:
        self.plugsOnSwitch = self.args["smartControlledByDumb"].split(",")
     except KeyError:
        self.plugsOnSwitch = None
     try:
        self.excludeList = self.args["excludeList"].split(",")
     except KeyError:
        self.excludeList = None

     self.status_tab = dict()

     self.run_hourly(self.scheduleNextEventBatch, datetime.now() + timedelta(seconds=5))

  def scheduleNextEventBatch(self,kwargs):
     databaseType=self.databaseType

     # set replay time based on input_number, or config file or default to 7
     try:
        days_back = int(float(self.get_state("input_number.replay_days_back")))
     except TypeError:
        days_back = self.numberOfDaysBack

     self.log("Scheduling Replaying "+str(days_back)+ " day[s] back")
     if databaseType == 'sqlite3':
        conn = sqlite3.connect("{}/home-assistant_v2.db".format(self.hassDir))
        c = conn.cursor()
        result=c.execute(f'SELECT states_meta.entity_id, states.state, states.last_updated_ts FROM states\
                        JOIN states_meta ON states_meta.metadata_id = states.metadata_id\
                        WHERE states_meta.entity_id LIKE "{self.devType}%"\
                        AND states.last_updated_ts > unixepoch() + (-{days_back}*24*60*60 + 1*60)\
                        AND states.last_updated_ts < unixepoch() + (-{days_back}*24*60*60 + 61*60)')
        #result=c.execute(f'SELECT entity_id, state, last_updated FROM states WHERE entity_id LIKE "{self.devType}%" AND last_updated > \
        #                 datetime("now","-{days_back} days","+1 minutes") AND last_updated < datetime("now","-{days_back} days","+61 minutes")')
        #result=c.execute(f'SELECT event_data FROM events WHERE event_type="state_changed" AND time_fired > \
        #                  datetime("now","-{days_back} days","+1 minutes") AND \
        #                  time_fired < datetime("now","-{days_back} days","+61 minutes") AND \
        #                  event_data like "%{self.devType}%" AND NOT event_data like "%group%" AND NOT event_data like "%automation%" AND NOT event_data like "%sensor%" AND NOT event_data like "%scene%"')
     if databaseType == 'MariaDB':
        conn = pymysql.connect(host=self.databaseHost, user=self.databaseUser, password=self.databasePassword, db=self.databaseSchema, charset='utf8')
        self.log("Connection to MariaDB was succesfull")
        query = f'SELECT states_meta.entity_id, states.state, states.last_updated_ts FROM states \
                        JOIN states_meta ON states_meta.metadata_id = states.metadata_id \
                        WHERE states_meta.entity_id LIKE "{self.devType}%" \
                        AND states.last_updated_ts > UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL {days_back} DAY)) \
                        AND states.last_updated_ts <= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL {days_back} DAY) + INTERVAL 1 HOUR)'
        self.log(f"SQL query: {query}",level="DEBUG")
        #query = f'SELECT entity_id, state, created FROM states WHERE domain="{self.devType}" \
        #     AND created > DATE_ADD(DATE_ADD(UTC_TIMESTAMP(),INTERVAL -{days_back} DAY), INTERVAL 1 MINUTE) \
        #     AND created <= DATE_ADD(DATE_ADD(UTC_TIMESTAMP(),INTERVAL -{days_back} DAY), INTERVAL 61 MINUTE)'
        with conn.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()

     for a in result:
        self.log(a,level="DEBUG")

     for entity_id, event_new_state, c_date in result:
        try:
           #mtimestamp(int(float(c_date))) + timedelta(days=days_back)}")

           #Look for entities we've been instructed to ignore and skip them
           try:
              self.excludeList.index( entity_id )
              self.log(f"{entity_id} on exclude list so will ignore")
              continue
           except (ValueError, AttributeError):
              i=0   # entify wasn't in the list so this is a do nothing

           # For smart plugs that on a wall switch we need to consider unavailable as a transistion to off
           if event_new_state == 'unavailable':
              try:
                 self.plugsOnSwitch.index( entity_id )
                 event_new_state = 'off'
                 self.log(f"Switched unavailable to off for {entity_id}",level="DEBUG")
              except (ValueError, AttributeError):
                 i=0   # entify wasn't in the list so this is a do nothing


           schedule_event = False
           event_old_state = 'unknown'
           # we only care when an entity goes to on or off
           if event_new_state == 'on' or event_new_state == 'off':
              # see if we've seen the entity before
              if entity_id in self.status_tab:
                 # we have, so has the state changed?
                 if self.status_tab[ entity_id ] != event_new_state:
                    # Yes so then update table an schedule event
                    self.log(f"Updating {entity_id} from state {self.status_tab[ entity_id ]} to {event_new_state}",level="DEBUG")
                    event_old_state = self.status_tab[ entity_id ]
                    self.status_tab[ entity_id ] = event_new_state
                    schedule_event = True
              else:
                 # we have not so add it to the table
                 self.log(f"First seen {entity_id}, adding to state table with state {event_new_state}")
                 self.status_tab[ entity_id ] = event_new_state
                 schedule_event = True

           if schedule_event:
              # pull time from database entry.
              # events are in UTC so we need to convert to local time
              event_trig_at = ""
              try:
                event_trig_at = datetime.fromtimestamp(int(float(c_date))) + timedelta(days=days_back)
                #if databaseType == 'sqlite3':
                #    event_trig_at = datetime.fromtimestamp(int(float(c_date))) + timedelta(days=days_back)
                #if databaseType == 'MariaDB':
                #    event_trig_at = datetime.fromtimestamp(int(float(c_date))) + timedelta(days=days_back)
              except TypeError:
                self.log("Date field from database didn't parse correctly so skipping record",level="WARNING")
                continue

              #events are in UTC so we need to convert to local time
              #event_trig_at += timedelta(minutes=self.get_tz_offset())

              self.log(f"Scheduling {entity_id} from {event_old_state} to {event_new_state} at {event_trig_at}")
              self.run_at(self.executeEvent, event_trig_at, entity_id = entity_id, event_new_state = event_new_state)
        except KeyError:
           self.log(f"Failed to parse ({entity_id}, {event_new_state}, {c_date})",level="WARNING")

     conn.close()


  def executeEvent(self, kwargs):
     replay_enable = self.get_state(self.enableTag)
     if replay_enable == self.enableVal:
        self.log(f"Turn {self.devType}/turn_{kwargs['event_new_state']} {kwargs['entity_id']} {kwargs['event_new_state']}")
        self.call_service(f"{self.devType}/turn_{kwargs['event_new_state']}", entity_id = kwargs['entity_id'])
        self.log(f"Turned {kwargs['entity_id']} {kwargs['event_new_state']}")
     else:
        self.log(f"Did not turn {kwargs['entity_id']} {kwargs['event_new_state']} because {self.enableTag} is not on")

# ReplayLightsHistory [![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
This is an AppDaemon App for Home Assistant that is designed to replay your lights behavior when no one is home.  There are multiple other approaches out there that try to simulate behavior, which is hard.  This approach simply uses your smart devices previous behavior to control their pending behavior. As the code exist today it has been tested with lights and smart switches.  The smart switches include TP Link smart switches and plugs, as they are both labeled switch entities in Home Assistant. It has also been used with shelly 2 switches.  It currently can only be configured to control one category of entities, which is specified in the configuration information.

Manually installing this AppDaemon App is relatively simply.  The replay_lights.py file needs to be placed in the appdaemon/apps/ directory on your Home assistant install.  Then you need to added lines to the appdaemon/apps/apps.yaml file to enable this application. At a minimum you would add these lines to the file apps/yaml file:

replay_lights:
  module: replay_lights
  class: ReplayLights

A maximum configuration can include the following lines, modified for your install:
```
replay_lights:
  hassDir: '/home/jondoe/.homeassistant'
  databaseType: sqlite3
  databaseHost: "localhost"
  databaseUser: "homeassistant"
  databasePassword: "PASSWORD"
  databaseSchema: "homeassistant"
  module: replay_lights
  class: ReplayLights
  numberOfDaysBack: 7
  deviceType: "light"
  enableTag: "alarm_control.home_alarm"
  enableVal: "armed_away"
  smartControlledByDumb: "switch.master_bed,switch.living_room_lamp"
  excludeList: "switch.garage,switch.garagecam"
  log_level: INFO
```

example_apps.yaml in the repo includes similar records

All of the parameters are optional.  Their use follows:

* hassDir - Home Assistant config directory (assumed to have home-assistant_v2.db in there). Defaults /config.

* databaseType - Defines database type either sqlite3 which is default or MariaDB

* databaseHost - Hostname or IP address of host where MariaDB is installed (optional, default localhost)

* databaseUser -  User for MariaDB defaults to homeassistant

* databasePassword - Password for MariaDB

* databaseSchema - Name of DB schema akka database name. This is normally same as user name. (optional, default homeassistant)

* numberOfDaysBack – this value that indicates how many days back in time the application should look for behavior that is to be replayed. This value can also be provided as a Home Assistant input number entity named input_number.replay_days_back.  The advantage of specifying the value as an input number is that you can then change the value via the Home Assistant Lovelace interface.  From a precedent perspective the application first looks for the input number entity, it looks for numberOfDaysBack from the apps.yaml file and finally if neither of these value is defined it uses the default of 7 days back.

* deviceType – this has been tested with “switch” and “light”. It’s possible that it could work with other entity types.  If not specified in the configuration, the default is “switch”.  You can determine this value by looking at the entities off the configuration panel in your Home Assistant user interface.  All of the devices you want to control will start with this label.  

* enableTag – This value, along with enableVal, determine if automated control of the lights is enabled.  This is the name of the Home Assistant entity that the app looks at to determine if it should actually turn something off or on. The example_groups.yaml file shows how you might set up a Home Assistant group of persons entities to control this app’s behavior. The value for this field would be set to “group.persons”. You could then set the enableVal to “away”, and if all persons in this group are away the app will control the devices.  The default value is a Home Assistant input boolean, "input_boolean.light_replay_enabled", that you need to create in your Home Assistant configuration.yaml file if you aren’t using some other entity, like the group.persons entity mentioned above, or the alarm control panel entity shown in the example configuration file above. 

* enableVal – This is the “state” value the “enableTag” must have in order for the app to actually turn something on or off. For the default enableTag, "input_boolean.light_replay_enabled", a state value of “on” would indicate that the app should controls the smart devices. As mentioned above if you created a group of persons and you wanted control to happen when they were all away from home then this parameter would be set to “away”.  The default for this field is “on”

* smartControlledByDumb – If you have smart light bulbs or smart plugs there is a possibility that a dumb switch could be inline.  If used the dumb switch would could remove power from the device.  If someone turns the dumb switch off then the device will be assigned a status of “unavailable” in Home Assistant instead of off.  This parameter tells the application which devices can be disabled by dumb switches.  This is a comma separated list.  In the example configuration above it shows two smart plugs that could also be powered off via a dumb switch.  If you have no devices in this situation then this parameter isn’t required.

* excludeList - This is a comma separated list of switches you don't want included in the replay action, such as a switch on your garage or maybe a basement light you don't want to have turned on while you're out.

* log_level - This is the log level for the application. It overrides the AppDaemon log level and set a custom log level only for this application. Supported log levels: INFO, WARNING, ERROR, CRITICAL, DEBUG, NOTSET.

NOTE: A recent update added the ability to use MariaDB as an alternative to sqlite3.  This change requires the python package to be included in your appdaemon docker container.  You include PyMySQL by adding it to the addons.json file found in the home assistant base directory.  The easist way to make this modification is directly from the Home Assistant GUI.  From Supervisor -> AppDaemon -> Configuration you can update the configuration to look like this:
```
system_packages: []
python_packages:
  - PyMySQL
init_commands: []
```
For the change to take effect you need to restart AppDaemon, which can be done from the AppDaemon Info tab.

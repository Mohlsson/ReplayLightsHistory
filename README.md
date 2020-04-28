# ReplayLightsHistory
This is an AppDaemon App for Home Assistant that is designed to replays your lights behavior when no one is home.  There are multiple other approaches out there that try to simulate behavior, which is hard.  This approach simply uses your smart devices previous behavior to control their pending behavior. As the code exist today it has been tested with lights and smart switches.  The smart switches include TP Link smart switches and plugs, as they are both labeled switch entities in Home Assistant. It currently can only be configured to control one category of entities, which is specified in the configuration information.

Manually installing this AppDaemon App is relatively simply.  The replay_lights.py file needs to be placed in the appdaemon/apps/ directory on your Home assistant install.  Then you need to added lines to the appdaemon/apps/apps.yaml file to enable this application. At a minimum you would add these lines to the file apps/yaml file:

replay_lights:
  module: replay_lights
  class: ReplayLights

A maximum configuration can include the following lines, modified for your install:

replay_lights:
  module: replay_lights
  class: ReplayLights
  numberOfDaysBack: 7
  deviceType: "light"
  enableTag: "alarm_control.home_alarm"
  enableVal: "armed_away"
  smartControlledByDumb: "switch.master_bed,switch.living_room_lamp"

example_apps.yaml in the repo includes similar records

All of the parameters are optional.  Their use follows:

* numberOfDaysBack – this value that indicates how many days back in time the application should look for behavior that is to be replayed. This value can also be provided as a Home Assistant input number entity named input_number.replay_days_back.  The advantage of specifying the value as an input number is that you can then change the value via the Home Assistant Lovelace interface.  From a precedent perspective the application first looks for the input number entity, it looks for numberOfDaysBack from the apps.yaml file and finally if neither of these value is defined it uses the default of 7 days back.

* deviceType – this has been tested with “switch” and “light”. It’s possible that it could work with other entity types.  If not specified in the configuration, the default is “switch”.  You can determine this value by looking at the entities off the configuration panel in your Home Assistant user interface.  All of the devices you want to control will start with this label.  

* enableTag – This value, along with enableVal, determine if automated control of the lights is enabled.  This is the name of the Home Assistant entity that the app looks at to determine if it should actually turn something off or on. The example_groups.yaml file shows how you might set up a Home Assistant group of persons entities to control this app’s behavior. The value for this field would be set to “group.persons”. You could then set the enableVal to “away”, and if all persons in this group are away the app will control the devices.  The default value is a Home Assistant input boolean, "input_boolean.light_replay_enabled", that you need to create in your Home Assistant configuration.yaml file if you aren’t using some other entity, like the group.persons entity mentioned above, or the alarm control panel entity shown in the example configuration file above. 

* enableVal – This is the “state” value the “enableTag” must have in order for the app to actually turn something on or off. For the default enableTag, "input_boolean.light_replay_enabled", a state value of “on” would indicate that the app should controls the smart devices. As mentioned above if you created a group of persons and you wanted control to happen when they were all away from home then this parameter would be set to “away”.  The default for this field is “on”

* smartControlledByDumb – If you have smart light bulbs or smart plugs there is a possibility that a dumb switch could be inline.  If used the dumb switch would could remove power from the device.  If someone turns the dumb switch off then the device will be assigned a status of “unavailable” in Home Assistant instead of off.  This parameter tells the application which devices can be disabled by dumb switches.  This is a comma separated list.  In the example configuration above it shows two smart plugs that could also be powered off via a dumb switch.  If you have no devices in this situation then this parameter isn’t required.
     

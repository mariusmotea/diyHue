#####
Alarm
#####

Is possible to receive email notification when one motion sensor is triggered while alarm is active.
To configure the alarm you must first edit the file config.json and add your smtp credentials.
On first execution HueEmulator.py will send a test email and if this is successful sent a new virtual light named "Alarm" will be automatically created.
You will need to create a dummy room to control this virtual light.
Turn this light on/off to enable/disable the alarm.

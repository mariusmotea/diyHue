Alarm
=====

It is possible to receive email notifications when one motion sensor is triggered while the alarm is active.
To configure the alarm you must first edit the file config.json and add your SMTP credentials.
On first execution HueEmulator.py will send a test email and if this is successfully setup a new virtual light named "Alarm".
You will need to go in Hue application => Settings => Lights and from there you can activate/deactivate the alarm by touching the light Alarm.

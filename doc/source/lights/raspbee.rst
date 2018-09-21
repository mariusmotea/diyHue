.. _raspbee:

Raspbee
=======

The Raspbee module is used with Deconz, the software dedicated for this module that provides an API similar to the Hue API

ZigBee Devices With Built In Support
------------------------------------

* Trandri Remote
* Tradfri Wireless Dimmer
* Tradfri Motion Sensor
* Xiaomi Aquara Motion Sensor

\*Other devices can still be manually configured to perform actions with custom Hue rules

Deconz installation
-------------------

* Execute raspi-config and turn off the serial login as this will enter in conflict with deconz (do not disable also the hardware serial port)
* Follow the steps from here: https://github.com/dresden-elektronik/deconz-rest-plugin for the deconz.deb package download and installation (no need to install dev package or compile the code)
* Edit the Deconz systemd script to bind on port 8080: ``sudo nano /etc/systemd/system/deconz.service`` replace ``--http-port=80`` with ``--http-port=8080 --upnp=0 --ws-port=8081``
* Start the Deconz service, browse to ``http://{hue emulator ip}:8080`` and add all zigbee devices.
  This is done by clicking "Open network" in settings and then reset the devices. Don't configure any device in deconz.
* Start hue emulator (you should see in the logs the import of all zigbee devices)
* Click "Unlock Gateway" in the Deconz settings to allow hue emulator to register, then open ``http://{hue emulator ip}/deconz`` to automatically register the bridge emulator with Deconz.
  In order to configure IKEA switches you must first configure the rooms

Sensors and Switches Configuration
----------------------------------

* Tradfri Motion Sensors will be added as Hue Motion Sensors and must be configured from the Hue application.
  With the original rules in place it will work like a Hue Motion Sensor (ex: dim the light with 30 second before turning off)
* Tradfri Dimmers and Tradfri Remotes must be configured from ``http://{hue emulator ip}/deconz``
  Tradfri Remotes can be configured to work on a specified room (the same as it was developed to) or to act as if it is a Hue Dimmer Switch or Hue Tap Switch, where they must be configured from the Hue application.
  When this happens the Tradfri Remote will not be displayed anymore in the Deconz configuration page and can be added back only by removing it from Hue application.
  The Tradfri Remote has 5 buttons, while both hue switches have only 4 so for the Tap Switch the top button doesn't perform any action.
  For the Dimming Switch, the center button is "On", up/down are brightness up/down and both left/right buttons will turn of the light.
  The reason I added the feature to transform the Tradfri Remote into a Hue Switch is because it can then switch scenes where color lights are used, while the Tradfri Remote was designed just to change the brightness and color temperature.

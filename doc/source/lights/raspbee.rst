.. _raspbee:

Raspbee
#######

Raspbee module is used with Deconz, the software dedicated for this module that provide an api similar to hue api

ZigBee devices with built in support
====================================

* Trandri Remote
* Tradfri Wireless Dimmer
* Tradfri Motion Sensor
* Xiaomi Aquara Motion Sensor

\*other devices can still be manually configured to perform actions with custom hue rules

Deconz installation
===================

* Execute raspi-config and turn off the serial login as this will enter in conflict with deconz (do not disable also the hardware serial port)
* Follow the steps from here: https://github.com/dresden-elektronik/deconz-rest-plugin for deconz.deb package download and installation (no need to install dev package or compile the code)
* Edit deconz systemd script to bind on port 8080: ``sudo vim /etc/systemd/system/deconz.service`` replace ``--http-port=80`` with ``--http-port=8080 --upnp=0 --ws-port=8081``
* Start deconz service, browse to http://{hue emulator ip}:8080 and add all zigbee devices.
  This is done by clicking "Open network" in settings and then reset the devices. Don't configure any device in deconz.
* Start hue emulator (must see in output the import of all zigbee devices)
* Click "Unlock Gateway" in settings to allow hue emulator to register, then open http://{hue emulator ip}/deconz to automatically register bridge emulator with deconz.
  In order to configure IKEA switches you must configure first the rooms.

Sensors and switches configuration
==================================

* Tradfri Motion Sensor will be added as Hue Motion Sensor and must be configured from Hue application.
  With the original rules in place it will work like a Hue Motion Sensor (ex: dim the light with 30 second before to turn off)
* Trafri Dimmer and Tradfri Remote must be configured from http://{hue emulator ip}/deconz.
  Tradfri Remote can be configured to work on a specified room like it was developed or to act as if is a Hue Dimmer Switch or Hue Tap Switch, case where they must be configured from Hue application.
  When this will happen the Tradfri Remote will not be displayed anymore in deconz configuration page and can be added back only by removing it from Hue application.
  Because Tradfri Remote has 5 buttons, while both hue switches have only 4, for Tap Switch the top button don't perform any action, and for Dimmin Switch, center button is "On", up/down are bri up/bri down and both left/right buttons will turn of the light.
  The reason why i add the future to transform the Tradfri Remote into a Hue Switch is because it can switch scenes where color lights are used, while the Tradfri Remote was designed just to change the brightness and color temperature.

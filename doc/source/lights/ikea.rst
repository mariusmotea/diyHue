IKEA Tradfri
============

There are two ways to interact with IKEA Tradfri devices, one method is to use the Tradfri Gateway and you will be able to control just the lights.
The second method is to use the Raspbee module that offers the flowing advantages:

* The ability to setup multiple sensors and switched in same room, while the Tradfri application only gives the possibility to configure just one switch or sensor per group (room).
* Add custom rules for sensors and switches
* Tradfri Motion Sensors are emulated as Hue Motion Sensor giving the possibility to choose different scenes based on the time (ex: max brightness between 08:00 - 23:00 and Nightlight scene between 23:00 and 08:00) Also the light will be dimmed for 30 seconds before being turned off and you can configure from Hue application how much time the light will stay on after motion was triggered.
* The Tradfri Remote can be emulated as a Hue Dimmer Switch or Hue Tap Switch that can apply color scenes.

Import Trafri Gateway Lights
----------------------------

Open ``http://{bridgeIP}/tradfri`` Type in the Ikea bridge IP and security key and click "Save".
You should then see all the lights paired with Tradfri bridge in Hue application.
Important: You must make sure you are using the correct coap-client-linux binary for your system architecture or this will fail.

Raspbee Module Setup
--------------------

For instructions on controlling Ikea Tradfri lights with the Raspbee module, see the :ref:`raspbee` module page.

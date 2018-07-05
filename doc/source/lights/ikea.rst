IKEA Tradfri
############

There are two ways to interact with IKEA Tradfri devices, one method is to use the Tradfri Gateway and you will be able to control just the lights, second method is to use the Raspbee module that offer the flowing advantages:

* can setup multiple sensors and switched on same room, while Tradfri application give the possibility to configure just one switch or sensor per group (room).
* add custom rules for sensors and switches
* Tradfri Motion Sensors will be emulated as Hue Motion Sensor that give the possibility to choose different scenes based on time (ex: max brightness between 08:00 - 23:00 and Nightlight scene between 23:00 and 08:00) also the light will be dimmed with 30 seconds before to be turned off and to configure from Hue application how much time the light will stay on after motion was triggered.
* Tradfri Remote can be emulated as Hue Dimmer Switch or Hue Tap Switch that can apply color scenes.

Setup Trafri Gateway in Bridge Emulator
=======================================

Open http://{bridgeIP}/tradfri, type Ikea bridge ip and security key and click "Save". If everything was fine you will see all lights paired with Tradfri bridge in Hue application. Important: coap-client-linux binary is compiled for arm devices like raspberry pi. If you will use an x86 computer then you will need to recompile this.

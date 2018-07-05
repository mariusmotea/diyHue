MiLight Hub
###########

With the circuit from `here <https://github.com/sidoh/esp8266_milight_hub>`_ you will be able to control MiLight bulbs what work on a proprietary 2.4 ghz protocol. This project provide a REST api that was integrated in Bridge Emulator.

Add MiLight lights in Bridge Emulator
=====================================

Open http://{bridgeIP}/milight, complete the form and click Save. You need to repet this step for every light as there is no way to retrieve the list of lights from milight hub.

Convert MiLight bulbs to Wifi
=============================

Is possible to convert MiLight bulbs to wifi using any ESP8266 module.
I convert one RGB-CCT bulb with ESP-12S module (picture available) in less than 30 minutes.
From original board you will need just the 3.3v regulator (not recommended because of low power) and the led drivers (NPN transistors for colored leds, MOSFET for white leds) + nearby resistors that are connected to transistors base/gate, other components can be disconnected/removed, mandatory disconnect the IC that control the leds because will enter in conflict with ESP module.
I connect GPIO12/13/14 to resistors that point to the base of RGB transistors and GPIO4/5 directly to MOSFET gates (not thru resistors because these are connected to ground). For stability an extra capacitor is required on power line.

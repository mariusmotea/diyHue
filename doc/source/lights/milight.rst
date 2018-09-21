MiLight Hub
===========

With the circuit from `here <https://github.com/sidoh/esp8266_milight_hub>`_ you will be able to control MiLight bulbs that work using a proprietary 2.4 GHz protocol.
The linked project provides a REST API that was integrated into diyHue.

Import MiLight lights
---------------------

Open ``http://{bridgeIP}/milight``, complete the form and click Save. You need to repeat this step for every light as there is no way to retrieve the list of lights from the MiLight hub.

Convert MiLight bulbs to Wi-Fi
-----------------------------

It is also possible to convert MiLight bulbs to WiFi using any ESP8266 module.
I have successfully converted one RGB-CCT bulb with an ESP-12S module (picture available) in less than 30 minutes.
From original circuit board you will just need the 3.3V regulator (not recommended because of low power), the led drivers (NPN transistors for colored leds, MOSFET for white leds) and any nearby resistors that are connected to the transistors base/gate, other components can be disconnected/removed.
You must remove the IC that controls the LED's or it will conflict with the ESP8266 module.
I connected GPIO12/13/14 to the resistors that point to the base of RGB transistors and GPIO4/5 directly to the MOSFET gates (not through the resistors because these are connected to ground).
For stability an extra capacitor is required on the power line.
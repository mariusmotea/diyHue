DIY Lights
==========

The following devices are currently supported:

* Generic PWM CCT lights (2 channels) - ex Milight bicolor
* generic PWM RGB lights (3 channels)
* generic PWM RGBW lights (4 channels) - ex. Feican bulbs
* generic PWM RGB-CCT lights (5 chnnels - ex Milight FUT015)
* SK6812 Neopixels
* WS2812B Neopixels
* All ZigBee lights - check :ref:`raspbee` module page

A lot of Wi-Fi lights from the market are ESP8266 based and can be used very easily with this project by flashing the firmware with one provided.
Almost all dimmable lights that are not ESP8266 based (ex MiLight bulbs) can be converted to Wi-Fi with one ESP-12S module by connecting the outputs directly to led drivers (picture available).
If you decide to convert a MiLight bulb to ESP-12S, then I recommend to use a `micro step down buck converter <https://www.aliexpress.com/item/3pcs-1A-DC-5V-6V-9V-12V-24V-to-3-3V-DC-DC-Step-Down-Buck/32765853201.html?spm=a2g0s.9042311.0.0.kDdB4j>`_ in order to avoid overheating issues.

All lights are two way synchronized so any change made by 3rd party device will also be added to the bridge emulator on the first request to each light group.
By default any light that become unreachable will be marked as unreachable and will be displayed as off.
This is because a lot of people still use classic light switches.

Light GUI
---------

.. figure:: /_static/images/lightGUI.png

All lights have an internal web GUI that can be accesses with any browser and offers the following options:

* Turn the light on/off
* Set startup option:

  * Light Off (default)
  * Light On
  * Last State (Turns the light on to the same state as it was the last time it was on)

* Change the scene. This will change also the power on scene
* Change any light parameter (bri, color, ct, xy, etc)

Flashing Firmware
-----------------

Neopixels
~~~~~~~~~

Before compiling the code, you must set the ``lightsCount`` and ``pixelCount`` variables.
``lightsCount`` is the number of virtual lights to create from your NeoPixel strip.
``pixelCount`` is the number of NeoPixel LED's per light. ``transitionLeds`` represents the number of LEDs used for smooth transitions of colours between lights.
I recommend using atleast 3 lights, one light at every 20 - 50 LED's so you can enjoy Hue scenes and Hue Entertainment.
The data pin of the LED's must be connected to RX pin of the ESP8266 board. Make sure to disconnect this when uploading or it could fail.

.. figure:: /_static/images/strip_wiring_to_wemos_d1_mini.jpg

Generic lights
~~~~~~~~~~~~~~

If your device is factory ESP8266 based, then you must specify the pins used in that devices before compiling the code.
If you don't know what pins are used or what color is controlled on a pin then try random pins with OTA firmware upgrades until you find the correct pins.
I recommend using the MiLight FUT15 bulbs converted to ESP-12S because of it's high brightness and good color reproduction.

.. figure:: /_static/images/MiLight_RGB_CCT_converted_to_ESP-12S.jpg

Connecting the lights to a Wi-Fi network
----------------------------------------

All lights are using `WiFiManager <https://github.com/tzapu/WiFiManager>`_ and on power up, will broadcast for 2 minutes with the SSID set in the ``light_name`` variable (the defaultis  ``Hue .....``)
Connect to this network with you phone or computer and browse to ``http://192.168.4.1``
From here you can choose the SSID of the network you would like the light to connect to and enter its password.
After the light is present on your network open the official Hue application and scan for new lights.
In case no lights are found, check if the nmap package is installed.
Note: The app will often say no lights found but the lights will then appear a few seconds after this notification. So be patient!

Lights API
----------

The lights use the same Hue protocol however, the values are not sent in json, like in the Hue protocol, but directly in GET request::

  "http://{light ip}/set?light=1&r=0&g=60&b=255&transitiontime=2000"
  "http://{light ip}/discover"

Arguments that can be passed in the URL:

* "on": 1 to set light on, 0 to set the light off.
* "r", "g", "b": Set the light color using RGB values between 0 and 255.
* "x" and "y": Values between 0.0 and 1.0 to set the light color using a CIE chart.
* "ct": Value between 153 (max warm white) and 500 (max could white) http://en.wikipedia.org/wiki/Mired
* hue: Value between 0 and 65535, representing the hue of the light.
* sat: Set the saturation of the light. 255 is the most saturated and 0 is the least saturated.
* bri: Set the brightness of the light, 255 is the maximum brightness, 1 is the minimum, 0 will turn the light on to previous state
* transitiontime: Duration of the transition from the light’s current state to the new state. The default is 4 representing 0.4 seconds.
* bri_inc: Increase or decrease the brightness with a specified value

Firmware upgrade
----------------

You can upgrade the firmware very easily with Adruino OTA.

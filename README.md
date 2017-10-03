## diyHue [![Codacy Badge](https://api.codacy.com/project/badge/Grade/2cbcab2ae7194ce287cbdf4719980ea6)](https://www.codacy.com/app/thehappydinoa/diyHue?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=thehappydinoa/diyHue&amp;utm_campaign=Badge_Grade)
This project emulates a Philips Hue Bridge that is able to control ZigBee lights (using Raspbee module or original Hue Bridge or IKEA Tradfri Gateway), Mi-Light bulbs (using MiLight Hub), Neopixel strips (WS2812B and SK6812) and any cheep ESP8266 based bulb from market by replacing firmware with custom one. Is written in python and will run on all small boxes like RaspberryPi. There are provided sketches for Hue Dimmer Switch, Hue Tap Switch and Hue Motion Sensor. Lights are two-way synchronized so any change made from original Philips/Tradfri sensors and switches will be applied also to bridge emulator.

![diyHue ecosystem](https://raw.githubusercontent.com/mariusmotea/diyHue/develop/Images/hue-map.png)

### Requirements:
 - python
 - nmap package for esp8266 lights autodiscover ```sudo apt install namp```
 - python ws4py package only if zigbee module is used ```sudo pip install ws4py```


## TO DO
 - ~~Working directly with ZigBee lights, switches and sensors with RaspBee module~~
 - ~~control IKEA Trådfri lights from HUE applications~~
 - ~~Create ESP8266 bridge device to add MI Lights to Hue Bridge emulator.~~
 - On/Off control for other home devices using virtual lights
 - Alarm (~~email notification~~ + eps8266 horn)
 - Alexa Intergration

## Working futures:
  - Control lights (all functions)
  - Control groups (all functions)
  - Scenes (all functions)
  - Routines
  - Wake up
  - Go to sleep
  - Switches (custom esp8266 switches)
  - Autodiscover lights

## Not working:
  - Home & Away futures (require remote api that is not public)  

Check [Wiki page](https://github.com/mariusmotea/diyHue/wiki) for more details  

[![Youtube Demo](https://img.youtube.com/vi/c6MsG3oIehY/0.jpg)](https://www.youtube.com/watch?v=c6MsG3oIehY)

I push updates fast so if you want to notified just add this repo to watch

Contributions are welcomed  

Credits:
  - probonopd https://github.com/probonopd/ESP8266HueEmulator
  - sidoh https://github.com/sidoh/esp8266_milight_hub
  - StefanBruens https://github.com/StefanBruens/ESP8266_new_pwm

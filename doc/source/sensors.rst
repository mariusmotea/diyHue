#######
Sensors
#######

For ZigBee sensors and switches check :ref:`raspbee` module

SWITCHES
########

Dimmer Switch and Tap Switch are almost identical, the only difference is that dimmer switch can control the lights also without the bridge (for this reason bridgeIp is declared as array to setup more ip's), and the buttons codes are different.

Circuit diagram
===============

.. figure:: /_static/images/Hue_Tap-Dimmer_switch_circuit_prototype.png


Device prototype
================

.. figure:: /_static/images/Switch1.jpg

How is working
==============

On sensor power on there will be a GET request sent to bridge,
ex: http://{bridgeIP}/switch?mac=xx:xx:xx:xx:xx:xx&devicetype=ZLLSwitch.
Bridge will check based on mac address if the switch is already registered or not.
If not it will register and then it will be available for configuration in Hue application.
After 3-5 seconds ESP8266 will enter in deep sleep mode and will consume less than 20uA.
On every button press there will be a short negative pulse on ESP8266 RST pin that will wake up the device, read input pins to check what button is pressed and send a request like this: http://{bridgeIP}/switch?mac=xx:xx:xx:xx:xx:xx&button=1000.
Bridge will process all rules and perform the action configured for this button.

MOTION SENSOR
#############

Circuit diagram
===============

.. figure:: /_static/images/Hue_Motion_sensor_circuit_prototype_v2.png

Device prototype
================

.. figure:: /_static/images/Motion_Sensor_1.jpg

How is working
==============

Exactly like switches the sensor will be registered on power on with GET request http://{bridgeIP}/switch?mac=xx:xx:xx:xx:xx:xx&devicetype=ZLLPresence and configuration will be done from Hue application.
ESP8266 will wake up from deep sleep on every PIR positive signal on GPIO5 pin and at every 20 minutes to send light sensor data.
Request example: http://{bridgeIP}/switch?mac=xx:xx:xx:xx:xx:xx&lightlevel=46900&dark=false&daylight=true&presence=true.
Is important to choose a low power PIR that can run on batteries for many months.
The PIR used in my example is HC-SR501, most common used in DIY projects.
To increase the battery life i remove the voltage regulator to 3.3V because this become useless on batteries.
GPIO4 will output +3V only when light level is measured to lower power consumption.

import json
import socket
import logging

from yeelight import Bulb

from huebridgeemulator.device.light import Light, LightState, LightAddress
from huebridgeemulator.tools.colors import convert_xy, convert_rgb_xy
# Should we use yeelight python lib ??
# https://www.yeelight.com/download/Yeelight_Inter-Operation_Spec.pdf

class YeelightLight(Light):

    _RESOURCE_TYPE = "lights"
    _MANDATORY_ATTRS = ('address', 'state', 'type', 'name', 'uniqueid',
                        'modelid', 'manufacturername', 'swversion')
    _OPTIONAL_ATTRS = ()

    def __init__(self, raw_data, index=None):
        Light.__init__(self, raw_data, index)
        self._con = None

    def _connect(self):
        self._con = Bulb(self.address.ip,
                         effect="smooth",
                         duration=self._DEFAULT_DURATION)
        self._con.start_music()
        if self.logger.getEffectiveLevel() <= logging.DEBUG:
            # Get device info
            output = {}
            output['model'] = self._con.model
            output['model_specs'] = self._con.get_model_specs()
            output['properties'] = self._con.get_properties()
            self.logger.debug(output)

    def update_status(self):
        self.logger.debug(self.serialize())
        if self._con is None:
            self._connect()
        properties = self._con.get_properties()
        self.state.bri = int(properties['bright'])
        # {'power': 'on', 'bright': '33', 'ct': '2169', 'rgb': '5442304', 'hue': '0', 'sat': '0', 'color_mode': '1', 'flowing': '0', 'delayoff': '0', 'music_on': '0', 'name': None}
        # {'on': True, 'bri': 83, 'xy': [0.520562, 0.310907], 'colormode': 'xy', 'reachable': True}
        self.state.on = properties['power'] == 'on'
        if properties['color_mode'] == '1':
            # RGB mode
            self.state.colormode = "xy"
            properties['rgb']
            hex_rgb = "%6x" % int(properties['rgb'])
            r = hex_rgb[:2]
            if r == "  ":
                r = "00"
            g = hex_rgb[3:4]
            if g == "  ":
                g = "00"
            b = hex_rgb[-2:]
            if b == "  ":
                b = "00"
            self.state.xy = convert_rgb_xy(int(r,16), int(g,16), int(b,16))
        elif properties['color_mode'] == '2':
            # Color Temp mode
            self.state.colormode = "ct"
            self.state.ct =  int(1000000 / int(properties['ct']))
        elif properties['color_mode'] == '3':
            # HS mode (also called HSV mode) How can we set the light in HSV mode ?
            self.state.colormode = "hs"
            self.state.hue = int(propreties['hue'] * 182)
            self.state.sat = int(int(propreties['sat']) * 2.54)
        else:
            self.logger.error("Unknown color mode: %s", properties['color_mode'])
            raise Exception("Unknown color mode")

    def send_request(self, data):
        if self._con is None:
            self._connect()
        # TODO use python lib function instead of `send_comand` method
        payload = {}
        transitiontime = self._DEFAULT_DURATION
        if "transitiontime" in data:
            transitiontime = data["transitiontime"] * 100
        for key, value in data.items():
            if key == "on":
                if value:
                    payload["set_power"] = ["on", "smooth", transitiontime]
                else:
                    payload["set_power"] = ["off", "smooth", transitiontime]
            elif key == "bri":
                payload["set_bright"] = [int(value / 2.55) + 1, "smooth", transitiontime]
            elif key == "ct":
                payload["set_ct_abx"] = [int(1000000 / value), "smooth", transitiontime]
            elif key == "hue":
                payload["set_hsv"] = [int(value / 182), int(self.state.sat / 2.54), "smooth", transitiontime]
            elif key == "sat":
                payload["set_hsv"] = [int(value / 2.54), int(self.state.hue / 2.54), "smooth", transitiontime]
            elif key == "xy":
                color = convert_xy(value[0], value[1], self.state.bri)
                payload["set_rgb"] = [(color[0] * 65536) + (color[1] * 256) + color[2], "smooth", transitiontime] #according to docs, yeelight needs this to set rgb. its r * 65536 + g * 256 + b
            elif key == "alert" and value != "none":
                payload["start_cf"] = [ 4, 0, "1000, 2, 5500, 100, 1000, 2, 5500, 1, 1000, 2, 5500, 100, 1000, 2, 5500, 1"]

        for api_method, params in payload.items():
            try:
                self._con.send_command(api_method, params)
            except Exception as exp:
                self.logger.error("Unexpected error: %s", exp)
                raise exp


class YeelightLightAddress(LightAddress):
    protocol = "yeelight"
    _MANDATORY_ATTRS = ('id', 'ip')

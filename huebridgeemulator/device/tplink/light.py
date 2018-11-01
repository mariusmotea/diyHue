"""Module to handle TPLink lights."""
import copy
import logging
import socket

from pyHS100 import SmartBulb, smartdevice

from huebridgeemulator.device.light import Light, LightAddress
from huebridgeemulator.tools.colors import (
    color_temperature_mired_to_kelvin,
    color_temperature_kelvin_to_mired,
    color_RGB_to_hsv,
    color_xy_to_RGB,
    color_hs_to_xy)
# Should we use yeelight python lib ??
# https://www.yeelight.com/download/Yeelight_Inter-Operation_Spec.pdf


class TPLinkLight(Light):
    """TPLink light class."""

    _RESOURCE_TYPE = "lights"
    _MANDATORY_ATTRS = ('address', 'state', 'type', 'name', 'uniqueid',
                        'modelid', 'manufacturername', 'swversion')
    _OPTIONAL_ATTRS = ()

    def _connect(self):
        self._con = SmartBulb(self.address.ip)
        if self.logger.getEffectiveLevel() <= logging.DEBUG:
            # Get device info
            self.logger.debug(self._con.get_sysinfo())

    def set_name(self, name):
        self.name = name
        # The following line doesn't work for now for LB130
        self._con.alias = name

    def update_status(self):
        self.logger.debug(self.serialize())
        if self._con is None:
            self._connect()
        sysinfo = self._con.get_sysinfo()
        self.swversion = sysinfo["sw_ver"]
        light_state = copy.copy(sysinfo['light_state'])
        if 'dft_on_state' in sysinfo['light_state']:
            del light_state['dft_on_state']
            light_state.update(sysinfo['light_state']['dft_on_state'])
        self.state.bri = light_state['brightness'] * 2.54
        self.state.on = light_state['on_off'] == 1
        if light_state['color_temp'] > 0:
            # Color Temp mode
            self.state.colormode = "ct"
            self.state.ct = color_temperature_kelvin_to_mired(light_state['color_temp'])
        elif light_state['color_temp'] == 0:
            # TPLINK use only hs mode
            # So we convert directly to xy
            self.state.colormode = "xy"
            self.state.hue = int(light_state['hue'])
            self.state.sat = int(light_state['saturation'])
            self.state.xy = color_hs_to_xy(self.state.hue, self.state.sat)
        else:
            self.logger.error("Unknown color mode: %s", light_state['color_temp'])
            raise Exception("Unknown color mode")

    def send_request(self, data):
        if self._con is None:
            self._connect()
        # TODO use python lib function instead of `send_comand` method
        payload = {}
        self.logger.debug(data)
        for key, value in data.items():
            if key == "on":
                if value:
                    payload["on_off"] = 1
                else:
                    payload["on_off"] = 0
            elif key == "bri":
                payload["brightness"] = int(value / 2.54)
            elif key == "ct":
                kelvin = color_temperature_mired_to_kelvin(value)
                if kelvin < self._con.valid_temperature_range[0]:
                    kelvin = self._con.valid_temperature_range[0]
                elif kelvin > self._con.valid_temperature_range[1]:
                    kelvin = self._con.valid_temperature_range[1]
                payload["color_temp"] = kelvin
            elif key == "hue":
                payload["hue"] = value
            elif key == "sat":
                payload["sat"] = value
            elif key == "xy":
                rgb = color_xy_to_RGB(value[0], value[1])
                hsv = color_RGB_to_hsv(rgb[0], rgb[1], rgb[2])
                payload["color_temp"] = 0
                payload["hue"] = int(hsv[0])
                payload["sat"] = int(hsv[1])
            elif key == "alert" and value != "none":
                # TODO what is it ?
                payload["start_cf"] = [4, 0,
                                       ("1000, 2, 5500, 100, 1000, 2, 5500, 1, "
                                        "1000, 2, 5500, 100, 1000, 2, 5500, 1")]

        self.logger.debug("Set light state: %s", payload)
        try:
            self._con.set_light_state(payload)
        except (smartdevice.SmartDeviceException, socket.timeout) as exp:
            # TODO set light as not reachable
            pass


class TPLinkLightAddress(LightAddress):
    """TPLink light address class."""
    protocol = "tplink"
    _MANDATORY_ATTRS = ('id', 'ip')

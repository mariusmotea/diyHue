"""Module to handle Yeelight lights."""
import logging

from yeelight import Bulb

from huebridgeemulator.device.light import Light, LightAddress
from huebridgeemulator.tools.colors import convert_xy, convert_rgb_xy
# Should we use yeelight python lib ??
# https://www.yeelight.com/download/Yeelight_Inter-Operation_Spec.pdf


class TradfriLight(Light):
    """Tradfri light class."""

    _RESOURCE_TYPE = "lights"
    # TODO
    _MANDATORY_ATTRS = ('address', 'state', 'type', 'name', 'uniqueid',
                        'modelid', 'manufacturername', 'swversion')
    # TODO
    _OPTIONAL_ATTRS = ()

    def set_name(self, name):
        self.name = name
        # TODO
        # self._con.set_name(name)

    def _connect(self):
        pass
        # TODO
        # self._con = ???

    def update_status(self):
        self.logger.debug(self.serialize())
        if self._con is None:
            self._connect()
        # TODO use ikea tradfri python lib
        command_line = ('./coap-client-linux -m get -u "{}" -k "{}" '
                        '"coaps://{}:5684/15001/{}"'.format(
                            self.address.identity,
                            self.address.preshared_key,
                            self.address.ip,
                            self.address.device_id))
        light_data = json.loads(check_output(command_line, shell=True)
                                .decode('utf-8').split("\n")[3])
        self.state.on = bool(light_data["3311"][0]["5850"])
        self.state.bri = light_data["3311"][0]["5851"]
        if "5706" in light_data["3311"][0]:
            if light_data["3311"][0]["5706"] == "f5faf6":
                self.state.ct = 170
            elif light_data["3311"][0]["5706"] == "f1e0b5":
                self.state.ct = 320
            elif light_data["3311"][0]["5706"] == "efd275":
                self.state.ct = 470
        else:
            self.state.ct = 470

    def send_request(self, data):
        if self._con is None:
            self._connect()
        # TODO
       

class TradfriLightAddress(LightAddress):
    """Tradfri light address class."""

    protocol = "ikea_tradfri"
    _MANDATORY_ATTRS = ('id', 'ip', 'identity', 'preshared_key')

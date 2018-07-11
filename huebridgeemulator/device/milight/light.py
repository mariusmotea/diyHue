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
        # TODO use milight python lib
        url = "http://{}/gateways/{}/{}/{}".format(
            self.address.ip,
            self.address.device_id,
            self.address.mode,
            self.address.group)
        light_data = json.loads(sendRequest(url, "GET", "{}"))
        # if light_data["state"] == "ON":
        #     bridge_config["lights"][light]["state"]["on"] = True
        # else:
        #     bridge_config["lights"][light]["state"]["on"] = False
        # Replaced by the next two lines
        bridge_config["lights"][light]["state"]["on"] = \
            bool(light_data["state"] == "ON")
        if "brightness" in light_data:
            bridge_config["lights"][light]["state"]["bri"] = light_data["brightness"]
        if "color_temp" in light_data:
            bridge_config["lights"][light]["state"]["colormode"] = "ct"
            bridge_config["lights"][light]["state"]["ct"] = \
                light_data["color_temp"] * 1.6
        elif "bulb_mode" in light_data and light_data["bulb_mode"] == "color":
            bridge_config["lights"][light]["state"]["colormode"] = "xy"
            bridge_config["lights"][light]["state"]["xy"] = \
                convert_rgb_xy(light_data["color"]["r"],
                               light_data["color"]["g"],
                               light_data["color"]["b"])


    def send_request(self, data):
        if self._con is None:
            self._connect()
        # TODO
       

class TradfriLightAddress(LightAddress):
    """Tradfri light address class."""

    protocol = "ikea_tradfri"
    _MANDATORY_ATTRS = ('id', 'ip', 'device_id', 'mode', 'group')

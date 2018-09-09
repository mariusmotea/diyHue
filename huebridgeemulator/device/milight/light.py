"""Module to handle Yeelight lights."""
import requests

from huebridgeemulator.device.light import Light, LightAddress
from huebridgeemulator.tools.colors import convert_xy, convert_rgb_xy
# Should we use milight python lib ??
# https://github.com/McSwindler/python-milight


class MilightLight(Light):
    """Milight light class."""

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
        self._con = requests.Session()

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
        response = self._con.get(url)
        light_data = response.data()
#        light_data = json.loads(sendRequest(url, "GET", "{}"))
        # if light_data["state"] == "ON":
        #     bridge_config["lights"][light]["state"]["on"] = True
        # else:
        #     bridge_config["lights"][light]["state"]["on"] = False
        # Replaced by the next two lines
        self.state.on = bool(light_data["state"] == "ON")
        if "brightness" in light_data:
            self.state.bri = light_data["brightness"]
        if "color_temp" in light_data:
            self.state.colormode = "ct"
            self.state.ct = light_data["color_temp"] * 1.6
        elif "bulb_mode" in light_data and light_data["bulb_mode"] == "color":
            self.state.colormode = "xy"
            self.state.xy = convert_rgb_xy(light_data["color"]["r"],
                                           light_data["color"]["g"],
                                           light_data["color"]["b"])

    def send_request(self, data):
        if self._con is None:
            self._connect()
        url = "http://{}/gateways/{}/{}/{}".format(self.address.ip, self.address.device_id,
                                                   self.address.mode, self.address.group)
        payload = {}
        for key, value in data.items():
            if key == "on":
                payload["status"] = value
            elif key == "bri":
                payload["brightness"] = value
            elif key == "ct":
                payload["color_temp"] = int(value / 1.6 + 153)
            elif key == "hue":
                payload["hue"] = value / 180
            elif key == "sat":
                payload["saturation"] = value * 100 / 255
            elif key == "xy":
                payload["color"] = {}
                (payload["color"]["r"],
                 payload["color"]["g"],
                 payload["color"]["b"]) = convert_xy(value[0], value[1], self.state.bri)
        self._con.put(url, data=payload)


class MilightLightAddress(LightAddress):
    """Milight light address class."""

    protocol = "milight"
    _MANDATORY_ATTRS = ('id', 'ip', 'device_id', 'mode', 'group')

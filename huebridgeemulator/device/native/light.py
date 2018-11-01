"""Module to handle Native lights."""
import requests

from huebridgeemulator.device.light import Light, LightAddress
# Should we use domoticz python lib ??


class NativeLight(Light):
    """Native light class."""

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
        url = "http://{}/json.htm?type=devices&rid={}".format(self.address.ip,
                                                              self.address.light_nr)
        response = self._con.get(url)
        light_data = response.json()
        for key, value in light_data.items():
            setattr(self.state, key, value)

    def send_request(self, data):
        if self._con is None:
            self._connect()
        url = "http://{}/set?light={}".format(self.address.ip, self.address.light_nr)
        for key, value in data.items():
            if key == "xy":
                url += "&x=" + str(value[0]) + "&y=" + str(value[1])
            else:
                url += "&" + key + "=" + str(value)
        self._con.get(url)


class NativeLightAddress(LightAddress):
    """Native light address class."""

    protocol = "native"
    _MANDATORY_ATTRS = ('id', 'ip', 'device_id', 'mode', 'group')

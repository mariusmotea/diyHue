"""Module to handle Domoticz lights."""
import requests

from huebridgeemulator.device.light import Light, LightAddress
# Should we use domoticz python lib ??


class DomoticzLight(Light):
    """Domoticz light class."""

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
                                                              self.address.light_id)
        response = self._con.get(url)
        light_data = response.json()
        if light_data["result"][0]["Status"] == "Off":
            self.state.on = False
        else:
            self.state.on = True
        self.state.bri = str(round(float(light_data["result"][0]["Level"])/100*255))

    def send_request(self, data):
        if self._con is None:
            self._connect()

        url = ("http://{}/json.htm?type=command&"
               "param=switchlight&idx={}".format(self.address.ip, self.address.light_id))
        for key, value in data.items():
            if key == "on":
                if value:
                    url += "&switchcmd=On"
                else:
                    url += "&switchcmd=Off"
            elif key == "bri":
                # domoticz range from 0 to 100 (for zwave devices) instead of 0-255 of bridge
                url += "&switchcmd=Set%20Level&level=" + str(round(float(value)/255*100))
        self._con.get(url)


class DomoticzLightAddress(LightAddress):
    """Domoticz light address class."""

    protocol = "domoticz"
    _MANDATORY_ATTRS = ('id', 'ip', 'device_id', 'mode', 'group')

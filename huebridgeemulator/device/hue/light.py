"""Module to handle Hue lights.

.. todo:: Use python `aiohue` lib
"""
import json
import requests

from huebridgeemulator.device.light import Light, LightState, LightAddress


class HueLight(Light):
    """Hue light class."""

    _RESOURCE_TYPE = "lights"
    _MANDATORY_ATTRS = ('address', 'state', 'type', 'name', 'uniqueid',
                        'modelid', 'manufacturername', 'swversion',
                        'capabilities', 'config', 'productname', 'swupdate')
    _OPTIONAL_ATTRS = ('swconfigid', 'productid')

    def update_status(self):
        url = "http://{}/api/{}/lights/{}".format(
            self.address.ip,
            self.address.username,
            self.address.light_id)
        ret = requests.get(url)
        self.state = LightState(ret.json()['state'])

    def _connect(self):
        pass

    def set_name(self, name):
        self.name = name
        url = "http://{}/api/{}/lights/{}".format(
            self.address.ip,
            self.address.username,
            self.address.light_id)
        data = {"name": name}
        requests.put(url, data=data)

    def send_request(self, data):
        url = "http://{}/api/{}/lights/{}/state".format(
            self.address.ip,
            self.address.username,
            self.address.light_id)
        ret = requests.put(url, data=json.dumps(data))
        return ret.json()


class HueLightAddress(LightAddress):
    """Hue light address class."""
    protocol = "hue"
    _MANDATORY_ATTRS = ('ip', 'light_id', 'username')
    # `light_id` example: "0x00000000033447b4"
    # `ip` example: "192.168.2.161",
    # `username` example: "0XMFqiVHCRmg26lQcYLDStizqNEyfjSd3nfGmzLv"

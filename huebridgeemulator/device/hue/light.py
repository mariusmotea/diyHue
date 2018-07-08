"""

.. todo:: Use python hue lib
"""
import json
import requests

from huebridgeemulator.device.light import Light, LightState, LightAddress
from huebridgeemulator.tools.colors import convert_xy


class HueLight(Light):

    _RESOURCE_TYPE = "lights"
    _MANDATORY_ATTRS = ('address', 'state', 'type', 'name', 'uniqueid', 'modelid', 'manufacturername', 'swversion', 
                        'capabilities', 'config', 'productname', 'swupdate')
    _OPTIONAL_ATTRS = ('swconfigid', 'productid')

    def update_status(self):
        url = "http://{}/api/{}/lights/{}".format(
            self.address.ip,
            self.address.username,
            self.address.light_id)
        ret = requests.get(url)
        self.state = LightState(ret.json()['state'])

    def send_request(self, data, method="put"):
        url = "http://" + self.address.ip + "/api/" + self.address.username + "/lights/" + self.address.light_id + "/state"
        ret = getattr(requests, method)(url, data=json.dumps(data))
        return ret.json()


class HueLightAddress(LightAddress):
    protocol = "hue"
    _MANDATORY_ATTRS = ('ip', 'light_id', 'username')
    # `light_id` example: "0x00000000033447b4"
    # `ip` example: "192.168.2.161",
    # `username` example: "0XMFqiVHCRmg26lQcYLDStizqNEyfjSd3nfGmzLv"

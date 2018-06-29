import json
import requests

from huebridgeemulator.device.light import Light, LightState, LightAddress
from huebridgeemulator.tools.colors import convert_xy


class HueLight(Light):

    def __init__(self, index, address, raw):
        Light.__init__(self, index, address, raw)

    def set_address(self, address):
        # address
        self.address = HueLightAddress(address)

    def send_request(self, data):
        url = "http://" + self.address.ip + "/api/" + self.address.username + "/lights/" + self.address.light_id + "/state"
        requests.put(url, data=json.dumps(data))

    def read_config(self, raw):
        self._raw = raw
        self.capabilities = raw['capabilities']
        self.config = raw['config']
        self.productname = raw['productname']
        self.swupdate = raw['swupdate']
        self.swconfigid = raw.get('swconfigid')
        self.productid = raw.get('productid')

    def serialize(self):
        ret = {"capabilities": self.capabilities,
               "config": self.config,
               "productname": self.productname,
               "swupdate": self.swupdate,
               "state": self.state.serialize(),
               }
        if self.swconfigid is not None:
            ret["swconfigid"] = self.swconfigid
        if self.productid is not None:
            ret["productid"] = self.productid
        return ret



class HueLightAddress(LightAddress):

    def __init__(self, address):
        address["protocol"] = "hue"
        # Example: "yeelight"
        LightAddress.__init__(self, address)
        # Example: "0x00000000033447b4"
        self.light_id = address["light_id"]
        # Example: "192.168.2.161",
        self.ip = address["ip"]
        # Example: "0XMFqiVHCRmg26lQcYLDStizqNEyfjSd3nfGmzLv"
        self.username = address["username"]


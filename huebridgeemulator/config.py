from collections import defaultdict
from huebridgeemulator.tools import getIpAddress
from uuid import getnode as get_mac
import json
import sys

import yaml


def loadConfig(filename):  #load and configure alarm virtual light
    #load config files
    try:
        with open(filename, 'r') as fp:
            bridge_config = json.load(fp)
            print("Config loaded")
    except Exception as exp:
        print("CRITICAL! Config file was not loaded: %s" % exp)
        sys.exit(1)

    # Move this
    if bridge_config["alarm_config"]["mail_username"] != "":
        print("E-mail account configured")
        if "virtual_light" not in bridge_config["alarm_config"]:
            print("Send test email")
            if sendEmail("dummy test"):
                print("Mail succesfully sent\nCreate alarm virtual light")
                new_light_id = nextFreeId("lights")
                bridge_config["lights"][new_light_id] = {"state": {"on": False, "bri": 200, "hue": 0, "sat": 0, "xy": [0.690456, 0.295907], "ct": 461, "alert": "none", "effect": "none", "colormode": "xy", "reachable": True}, "type": "Extended color light", "name": "Alarm", "uniqueid": "1234567ffffff", "modelid": "LLC012", "swversion": "66009461"}
                bridge_config["alarm_config"]["virtual_light"] = new_light_id
            else:
                print("Mail test failed")
    # end move this

    return bridge_config

def saveConfig(filename, bridge_config):
    with open(filename, 'w') as fp:
        json.dump(bridge_config, fp, sort_keys=True, indent=4, separators=(',', ': '))


class Config(object):
    """Configuration class."""

    def __init__(self, filepath):

        self.filepath = filepath
        # TODO: is this useless ?
        self.bridge = defaultdict(lambda:defaultdict(str))
        self._mac = '%012x' % get_mac()
        self.load()
        self._startup()
        

    def _startup(self):
        ip_pices = getIpAddress().split(".")
        self.bridge["config"]["ipaddress"] = getIpAddress()
        self.bridge["config"]["gateway"] = ip_pices[0] + "." +  ip_pices[1] + "." + ip_pices[2] + ".1"
        self.bridge["config"]["mac"] = self._mac[0] + self._mac[1] + ":" + self._mac[2] + self._mac[3] + ":" + self._mac[4] + self._mac[5] + ":" + self._mac[6] + self._mac[7] + ":" + self._mac[8] + self._mac[9] + ":" + self._mac[10] + self._mac[11]
        self.bridge["config"]["bridgeid"] = (self._mac[:6] + 'FFFE' + self._mac[6:]).upper()


    def load(self):
        """Read configuration from file"""
        # TODO add yaml
        with open(self.filepath, 'r') as cfs:
            self.bridge = json.load(cfs)


    def save(self):
        """Write configuration from file"""
        # TODO add yaml
        with open(self.filepath, 'w') as cfs:
            json.dump(self.bridge, cfs, sort_keys=True, indent=4, separators=(',', ': '))

    def nextFreeId(self, element):
        i = 1
        while (str(i)) in self.bridge[element]:
            i += 1
        return str(i)



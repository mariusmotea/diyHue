from collections import defaultdict
import copy
from uuid import getnode as get_mac
from datetime import datetime
import json
import sys

import yaml
import pytz
import netifaces
from netifaces import AF_INET, AF_LINK
from tzlocal import get_localzone

from huebridgeemulator.tools import getIpAddress
from huebridgeemulator.device.light import LightState
from huebridgeemulator.device.yeelight.light import YeelightLight, YeelightLightAddress
from huebridgeemulator.device.hue.light import HueLight
from huebridgeemulator.scene import Scene
from huebridgeemulator.const import REGISTRY_CAPABILITIES, REGISTRY_BASE_CONFIG


RESOURCE_TYPES = [
  "alarm_config",
  "capabilities",
  "config",
  "deconz",
  "groups",
  "lights",
  "lights_address",
  "linkbutton",
  "resourcelinks",
  "rules",
  "scenes",
  "schedules",
  "sensors"
]





class Registry(object):
    """Configuration class."""

    # Registry capabilities
    capabilities = REGISTRY_CAPABILITIES
    # Registry base config
    _base_config = REGISTRY_BASE_CONFIG

    def __init__(self, filepath=None):
        self.filepath = filepath
        self._mac = '%012x' % get_mac()
        # TODO Alarm_config
        self.alarm_config = {}
        # registry config
        self.config = copy.copy(self._base_config)
        # TODO deconz
        self.deconz = {}
        # groups registry
        self.groups = {}
        # lights registry (and light_address
        self.lights = {}
        # TODO linkbutton
        self.linkbutton = {}
        # TODO resourcelinks
        self.resourcelinks = {}
        # TODO rules
        self.rules = {}
        # scenes registry
        self.scenes = {}
        # TODO schedules registry
        self.schedules = {}
        # TODO sensors registry
        self.sensors = {}
        # just added lights
        self._new_lights = {}
        # Load from file
        if filepath is not None:
            self.load()
            self._startup()

    def _startup(self):
        ip_pices = getIpAddress().split(".")
        default_inf = netifaces.gateways()['default'][netifaces.AF_INET][1]
        # self.bridge["config"]["ipaddress"] = getIpAddress()
        self.config['ipaddress'] = netifaces.ifaddresses(default_inf)[AF_INET][0]['addr']
        self.config['netmask'] = netifaces.ifaddresses(default_inf)[AF_INET][0]['netmask']
        #self.bridge["config"]["gateway"] = ip_pices[0] + "." +  ip_pices[1] + "." + ip_pices[2] + ".1"
        self.config['gateway'] = netifaces.gateways()['default'][netifaces.AF_INET][0]
        # self.bridge["config"]["mac"] = self._mac[0] + self._mac[1] + ":" + self._mac[2] + self._mac[3] + ":" + self._mac[4] + self._mac[5] + ":" + self._mac[6] + self._mac[7] + ":" + self._mac[8] + self._mac[9] + ":" + self._mac[10] + self._mac[11]
        self.config['mac'] = netifaces.ifaddresses('wlp3s0')[AF_LINK][0]['addr']
        # self.bridge["config"]["bridgeid"] = (self._mac[:6] + 'FFFE' + self._mac[6:]).upper()
        self.config['bridgeid'] = self.config.mac[:6] + 'FFFE' + self.config.mac[6:].upper()
        self.config['timezone'] = get_localzone().zone
        self.config['localtime'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        self.config['UTC'] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")

    def set_filepath(self, filepath):
        self.filepath = filepath
        # Load from file
        if filepath is not None:
            self.load()
            self._startup()

    def load(self):
        """Read configuration from file"""
        # TODO add yaml
        with open(self.filepath, 'r') as cfs:
            raw_file = json.load(cfs)
            # Config
            for key, value in raw_file['config'].items():
                self.config[key] = value
            # Lights
            for index, light_address in raw_file['lights_address'].items():
                light = self.bridge['lights'][index]
                # Handle other light type
                if light_address['protocol'] == 'yeelight':
                    light['state'] = LightState(light['state'])
                    light['address'] = YeelightLightAddress(light_address)
                    new_light = YeelightLight(light)
                    self.lights[index] = new_light
                elif light_address['protocol'] == 'hue':
                    new_light = HueLight(index=index, address=light_address, raw=light)
                    self.lights[index] = new_light
            # Scenes
            for index, scene in self.bridge['scenes'].items():
                self.scenes[index] = Scene(scene)

    def save(self):
        """Write configuration to file."""
        output = {}
        # TODO Alarm config
        output['alarm_config'] = self.alarm_config
        # Capabilities
        output['capabilities'] = self.capabilities
        # Config
        output['config'] = self.config
        # TODO Deconz
        output['deconz'] = self.deconz
        # TODO groups
        output['groups'] = self.groups
        # Light and light addresses
        output['lights'] = {}
        for index, light in output['lights'].items():
            output['lights_address'][index] = light['address']
            output['lights'][index] = light
            if 'address' in output['lights'][index]:
                del(output['lights'][index]['address'])
            output['lights'][index]['state'] = output['lights'][index]['state'].serialize()
        # TODO linkbutton
        output['linkbutton'] = self.linkbutton
        # TODO resourcelinks
        output['resourcelinks'] = self.resourcelinks
        # TODO rules
        output['rules'] = self.rules
        # Scenes
        output['scenes'] = {}
        for index, scene in self.scenes.items():
            output['scenes'][index] = scenes.serialize()
        # TODO schedules
        output['schedules'] = self.schedules
        # TODO sensors
        output['sensors'] = self.sensors
        with open(self.filepath, 'w') as cfs:
            json.dump(output, cfs, sort_keys=True, indent=4, separators=(',', ': '))

    def backup(self):
        """Backup configuration."""
        filepath = "{}-backup-{}.json".format(self.filepath,
                                              datetime.now().strftime("%Y-%m-%d"))
        with open(filepath, 'w') as cfs:
            json.dump(self.bridge, cfs, sort_keys=True, indent=4, separators=(',', ': '))

    def nextFreeId(self, element):
        i = 1
        while (str(i)) in self.bridge[element]:
            i += 1
        return str(i)

    def add_new_resource(self, resource):
        resource_type = resource._RESOURCE_TYPE
        if resource_type is None:
            raise
        getattr(self, resource_type)[resource.index] = resource
        if resource_type == "lights":
            self._new_lights.update({resource.index: {"name": resource.name}})
            self._new_lights.update({"lastscan": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")})

    def get_new_lights(self):
        return self._new_lights

    def clear_new_lights(self):
        self._new_lights.clear()

    def get_resource(self, type, index):
        """Get light from index"""
        if type not in ["scenes", "lights"]:
            raise Exception("Bad resources type {}".format(type))
        self.save()
        return getattr(self, type)[index]

    def get_lights(self):
        """Return all lights."""
        ret = {}
        for index, light in self.lights.items():
            ret[index] = light.serialize()
        return ret

    def get_json_lights(self):
        """Return all lights in JSON format."""
        return json.dumps(self.get_lights())


# Improve that
registry = Registry()

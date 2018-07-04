from collections import defaultdict
import time
import copy
from uuid import getnode as get_mac
from datetime import datetime
import json
import sys
import os

import yaml
import pytz
import netifaces
from netifaces import AF_INET, AF_LINK
from tzlocal import get_localzone

from huebridgeemulator.tools import getIpAddress
from huebridgeemulator.device.light import LightState
from huebridgeemulator.device.yeelight.light import YeelightLight, YeelightLightAddress
from huebridgeemulator.device.hue.light import HueLight, HueLightAddress
from huebridgeemulator.alarm_config import AlarmConfig
from huebridgeemulator.scene import Scene
from huebridgeemulator.sensor import Sensor, generate_daylight_sensor
from huebridgeemulator.group import Group
from huebridgeemulator.linkbutton import LinkButton
from huebridgeemulator.const import (REGISTRY_CAPABILITIES, REGISTRY_BASE_CONFIG,
    RESOURCE_TYPES, REGISTRY_ALARM_CONFIG, REGISTRY_DECONZ, REGISTRY_LINKBUTTON)


class Registry(object):
    """Configuration class."""

    # Registry capabilities
    capabilities = REGISTRY_CAPABILITIES
    # Registry base config
    _base_config = REGISTRY_BASE_CONFIG

    def __init__(self, filepath=None):
        self.filepath = filepath
        self._mac = '%012x' % get_mac()
        # Alarm_config
        self.alarm_config = {}
        # registry config
        self.config = copy.copy(self._base_config)
        # deconz
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
        # ip_pices = getIpAddress().split(".")
        default_inf = netifaces.gateways()['default'][netifaces.AF_INET][1]
        # self.bridge["config"]["ipaddress"] = getIpAddress()
        self.config['ipaddress'] = netifaces.ifaddresses(default_inf)[AF_INET][0]['addr']
        self.config['netmask'] = netifaces.ifaddresses(default_inf)[AF_INET][0]['netmask']
        # self.bridge["config"]["gateway"] = ip_pices[0] + "." +  ip_pices[1] + "." + ip_pices[2] + ".1"
        self.config['gateway'] = netifaces.gateways()['default'][netifaces.AF_INET][0]
        # self.bridge["config"]["mac"] = self._mac[0] + self._mac[1] + ":" + self._mac[2] + self._mac[3] + ":" + self._mac[4] + self._mac[5] + ":" + self._mac[6] + self._mac[7] + ":" + self._mac[8] + self._mac[9] + ":" + self._mac[10] + self._mac[11]
        self.config['mac'] = netifaces.ifaddresses('wlp3s0')[AF_LINK][0]['addr']
        # self.bridge["config"]["bridgeid"] = (self._mac[:6] + 'FFFE' + self._mac[6:]).upper()
        self.config['bridgeid'] = (self.config['mac'].replace(":", "")[:6] +
                                   'FFFE' +
                                   self.config['mac'].replace(":", "")[6:]).upper()
        self.config['timezone'] = get_localzone().zone
        self.config['localtime'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        self.config['UTC'] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")

    def set_filepath(self, filepath):
        self.filepath = filepath
        # Load from file
        if self.filepath is not None:
            self.load()
            self._startup()

    def load(self):
        """Read configuration from file"""
        if not os.path.exists(self.filepath):
            # File doesn't exists
            # alarm_config
            self.alarm_config = AlarmConfig(REGISTRY_ALARM_CONFIG)
            # Config
            self.config = self._base_config
            #
            self.deconz = REGISTRY_DECONZ
            # link button
            self.linkbutton = LinkButton(REGISTRY_LINKBUTTON)
            # Sensor
            sensor = generate_daylight_sensor()
            self.sensors[sensor.index] = sensor
            # Save to file
            self.save()
        # TODO add yaml
        print("L"*555)
        print(1)
        with open(self.filepath, 'r') as cfs:
            raw_file = json.load(cfs)
            # alarm_config
            self.alarm_config = AlarmConfig(raw_file['alarm_config'])
            # Config
            for key, value in raw_file['config'].items():
                self.config[key] = value
            # Deconz
            self.deconz = raw_file['deconz']
            # Groups
            for index, group in raw_file['groups'].items():
                self.groups[index] = Group(group, index)
            # Lights
            for index, light_address in raw_file['lights_address'].items():
                light = raw_file['lights'][index]
                # Handle other light type
                if light_address['protocol'] == 'yeelight':
                    light['state'] = LightState(light['state'])
                    light['address'] = YeelightLightAddress(light_address)
                    new_light = YeelightLight(light, index)
                    self.lights[index] = new_light
                elif light_address['protocol'] == 'hue':
                    light['state'] = LightState(light['state'])
                    light['address'] = HueLightAddress(light_address)
                    new_light = HueLight(light, index)
                    self.lights[index] = new_light
            # linkButton
            self.linkbutton = LinkButton(raw_file['linkbutton'])
            # Scenes
            for index, scene in raw_file['scenes'].items():
                self.scenes[index] = Scene(scene, index)

            # Sensors
            for index, sensor in raw_file['sensors'].items():
                self.sensors[index] = Sensor(sensor)

    def save(self, output_file=None):
        """Write configuration to file."""
        output = {}
        # Alarm config
        output['alarm_config'] = self.alarm_config.serialize()
        # Capabilities
        output['capabilities'] = self.capabilities
        # Config
        output['config'] = self.config
        # TODO Deconz
        output['deconz'] = self.deconz
        # TODO groups
        output['groups'] = {}
        for index, group in self.groups.items():
            output['groups'][index] = group.serialize()
        # Light and light addresses
        output['lights_address'] = {}
        output['lights'] = {}
        for index, light in self.lights.items():
            output['lights_address'][index] = light.address.serialize()
            output['lights'][index] = light.serialize()
            if 'address' in output['lights'][index]:
                del(output['lights'][index]['address'])
        # linkbutton
        output['linkbutton'] = self.linkbutton.serialize()
        # TODO resourcelinks
        output['resourcelinks'] = self.resourcelinks
        # TODO rules
        output['rules'] = self.rules
        # Scenes
        output['scenes'] = {}
        for index, scene in self.scenes.items():
            output['scenes'][index] = scene.serialize()
        # TODO schedules
        output['schedules'] = self.schedules
        # TODO sensors
        output['sensors'] = {}
        for index, sensor in self.sensors.items():
            output['sensors'][index] = sensor.serialize()
        # Save
        if output_file is None:
            output_file = self.filepath
        with open(output_file, 'w') as cfs:
            json.dump(output, cfs, sort_keys=True, indent=4, separators=(',', ': '))

    def backup(self):
        """Backup configuration."""
        filepath = "{}-backup-{}.json".format(self.filepath,
                                              datetime.now().strftime("%Y-%m-%d"))
        self.save(output_file=filepath)

    def nextFreeId(self, element):
        if not hasattr(self, element):
            raise
        element_registry = getattr(self, element)
        if element_registry:
            last_index = max([int(index) for index in element_registry.keys()])
            next_index = last_index + 1
        else:
            next_index = 1
        # TODO index should be a int not a str
        return str(next_index)

    def generate_sensors_state(self, sensors_state):
        for sensor in self.sensors:
            if sensor not in sensors_state and "state" in self.sensors[sensor]:
                sensors_state[sensor] = {"state": {}}
                for key in self.sensors[sensor]["state"].keys():
                    if key in ["lastupdated", "presence", "flag", "dark", "daylight", "status"]:
                        sensors_state[sensor]["state"].update({key: "2017-01-01T00:00:00"})
        return sensors_state




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

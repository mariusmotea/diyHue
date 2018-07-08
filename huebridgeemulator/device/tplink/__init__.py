import socket
import random
import json

from pyHS100 import Discover, SmartBulb, SmartDeviceException

from huebridgeemulator.const import LIGHT_TYPES
from huebridgeemulator.device.tplink.light import TPLinkLight, TPLinkLightAddress
from huebridgeemulator.device.light import LightState



def discoverTPLink(registry):
    for light_ip in Discover.discover():
        new_light = SmartBulb(light_ip)
        try:
            new_light.state
        except SmartDeviceException:
            continue
        properties = new_light.get_sysinfo()
        device_exist = False
        # Check if the device exists
        for index, light in registry.lights.items():
            if light.address.protocol == "tplink" and light.address.id == properties["deviceId"]:
                device_exist = True
                light.address.ip = light_ip
                # TODO LOGGER
                print("light id " + light_ip + " already exist, updating ip...")
                break
        if (not device_exist):
            light_name = "Tplink id " + properties["deviceId"][-8:] if not properties["alias"] else properties["alias"]
            print("Add TPLink: " + light_name)
            modelid = None
            # TODO Why do we need to save it as a Philips model ??
            if properties["model"].startswith('LB130'):
                modelid = "LCT015"
            # elif ...
            # Add support for other tplink bulb
            if modelid is None:
                raise Exception("TPLink bulb %s not supported yet".format(properties["model"]))
            address = {"ip": light_ip, "id": properties["deviceId"]}
            raw_light = {"type": LIGHT_TYPES[modelid]["type"],
                         "name": light_name,
                         "uniqueid": properties["mic_mac"],
                         "modelid": modelid,
                         "manufacturername": "tplink",
                         "state": LightState(LIGHT_TYPES[modelid]["state"]),
                         "address": TPLinkLightAddress(address),
                         "swversion": properties["sw_ver"]}
            new_light = TPLinkLight(raw_light)
            registry.lights[new_light.index] = new_light
            registry.add_new_light(new_light)

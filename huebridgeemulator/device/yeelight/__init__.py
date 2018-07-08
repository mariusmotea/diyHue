import socket
import random
import json

from yeelight import discover_bulbs, Bulb

from huebridgeemulator.const import LIGHT_TYPES
from huebridgeemulator.device.yeelight.light import YeelightLight, YeelightLightAddress
from huebridgeemulator.device.light import LightState
from huebridgeemulator.logger import light_scan_logger


def discoverYeelight(registry):
    raw_lights = discover_bulbs()
    for raw_light in raw_lights:
        device_exist = False
        for index, light in registry.lights.items():
            rawlight_id = raw_light['capabilities']['id']
            if light.address.protocol == "yeelight" and light.address.id == rawlight_id:
                device_exist = True
                light.address.ip = raw_light["ip"]
                light_scan_logger.debug("Yeelight id %s already exist, updating ip...",
                                        rawlight_id)
                break

        if (not device_exist):
            properties = Bulb(raw_light["ip"]).get_properties()
            properties['id'] = raw_light['capabilities']['id']
            light_name = "YeeLight id " + properties["id"][-8:] if properties["name"] == "" else properties["name"]
            light_scan_logger.debug("Add YeeLight: %s", properties["id"])
            modelid = "LWB010"
            # TODO Why do we need to save it as a Philips model ??
            if properties["rgb"]:
                modelid = "LCT015"
            elif properties["ct"]:
                modelid = "LTW001"
            address = {"ip": raw_light["ip"], "id": properties["id"], "protocol": "yeelight"}
            data = {"type": LIGHT_TYPES[modelid]["type"],
                    "name": light_name,
                    "uniqueid": "4a:e0:ad:7f:cf:" + str(random.randrange(0, 99)) + "-1",
                    "modelid": modelid,
                    "manufacturername": "yeelight",
                    "state": LightState(LIGHT_TYPES[modelid]["state"]),
                    "address": YeelightLightAddress(address),
                    "swversion": LIGHT_TYPES[modelid]["swversion"]}
            new_light = YeelightLight(data)
            registry.lights[new_light.index] = new_light
            registry.add_new_light(new_light)

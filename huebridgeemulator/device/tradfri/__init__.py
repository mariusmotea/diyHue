"""Base functions for Tradfri lights.

.. todo:: Use Python Tradfri lib
"""
import json
from datetime import datetime
from subprocess import check_output

from huebridgeemulator.logger import light_scan_logger


def discover_tradfri(registry):
    """Discover Tradfri lights on your local network.

    .. todo:: need to be recoded
    """
    if hasattr(registry, "tradfri"):
        command_line = ('./coap-client-linux -m get -u "{}" '
                        '-k "{}" "coaps://{}:5684/15001"').format(
                            registry.tradfri["identity"],
                            registry.tradfri["psk"],
                            registry.tradfri["ip"])
        tradri_devices = json.loads(check_output(command_line, shell=True)
                                    .decode('utf-8').split("\n")[3])
        light_scan_logger.debug(tradri_devices)
        lights_found = 0
        for device in tradri_devices:
            command_line = ('./coap-client-linux -m get -u "{}" -k "{}" '
                            '"coaps://{}:5684/15001/{}"').format(
                                registry.tradfri["identity"],
                                registry.tradfri["psk"],
                                registry.tradfri["ip"],
                                str(device))
            device_parameters = json.loads(check_output(command_line, shell=True)
                                           .decode('utf-8').split("\n")[3])
            if "3311" in device_parameters:
                new_light = True
                for light in registry.lights.values():
                    if light.address.protocol == "ikea_tradfri" \
                            and light.address.device_id == device:
                        new_light = False
                        break
                if new_light:
                    lights_found += 1
                    # register new tradfri lightdevice_id
                    light_scan_logger.debug("register tradfi light {}", device_parameters["9001"])
                    new_light_id = registry.next_free_id("lights")
                    # TODO use TradfriLight Object
                    registry.lights[new_light_id] = {
                        "state": {"on": False,
                                  "bri": 200,
                                  "hue": 0,
                                  "sat": 0,
                                  "xy": [0.0, 0.0],
                                  "ct": 461,
                                  "alert": "none",
                                  "effect": "none",
                                  "colormode": "ct",
                                  "reachable": True},
                        "type": "Extended color light",
                        "name": device_parameters["9001"],
                        "uniqueid": "1234567" + str(device),
                        "modelid": "LLM010",
                        "swversion": "66009461"}
                    registry._new_lights.update({new_light_id: {
                        "name": device_parameters["9001"]}})
                    registry.lights[new_light_id].address = {
                        "device_id": device,
                        "preshared_key": registry.tradfri["psk"],
                        "identity": registry.tradfri["identity"],
                        "ip": registry.tradfri["ip"],
                        "protocol": "ikea_tradfri"}
        return lights_found
    return 0


def add_tradfri_dimmer(registry, sensor_id, group_id):
    """????

    .. todo:: Recoding
    """
    rules = [
        {"actions": [{
             "address": "/groups/" + group_id + "/action",
             "body": {"on": True, "bri": 1},
             "method": "PUT"}],
         "conditions": [
             {"address": "/sensors/" + sensor_id + "/state/lastupdated",
              "operator": "dx"},
             {"address": "/sensors/" + sensor_id + "/state/buttonevent",
              "operator": "eq",
              "value": "2002"},
             {"address": "/groups/" + group_id + "/state/any_on",
              "operator": "eq",
              "value": "false"}],
         "name": "Remote " + sensor_id + " turn on"},
        {"actions": [
            {"address": "/groups/" + group_id + "/action",
             "body": {"on": False},
             "method": "PUT"}],
         "conditions": [
            {"address": "/sensors/" + sensor_id + "/state/lastupdated",
             "operator": "dx"},
            {"address": "/sensors/" + sensor_id + "/state/buttonevent",
             "operator": "eq",
             "value": "4002"},
            {"address": "/groups/" + group_id + "/state/any_on",
             "operator": "eq",
             "value": "true"},
            {"address": "/groups/" + group_id + "/action/bri",
             "operator": "eq",
             "value": "1"}],
         "name": "Dimmer Switch " + sensor_id + " off"},
        {"actions": [
            {"address": "/groups/" + group_id + "/action",
             "body": {"on": False},
             "method": "PUT"}],
         "conditions": [
            {"address": "/sensors/" + sensor_id + "/state/lastupdated",
             "operator": "dx"},
            {"address": "/sensors/" + sensor_id + "/state/buttonevent",
             "operator": "eq",
             "value": "3002"},
            {"address": "/groups/" + group_id + "/state/any_on",
             "operator": "eq",
             "value": "true"},
            {"address": "/groups/" + group_id + "/action/bri",
             "operator": "eq",
             "value": "1"}],
         "name": "Remote " + sensor_id + " turn off"},
        {"actions": [
            {"address": "/groups/" + group_id + "/action",
             "body": {
                "bri_inc": 32,
                "transitiontime": 9},
             "method": "PUT"}],
         "conditions": [
            {"address": "/groups/" + group_id + "/state/any_on",
             "operator": "eq",
             "value": "true"},
            {"address": "/sensors/" + sensor_id + "/state/buttonevent",
             "operator": "eq",
             "value": "2002"},
            {"address": "/sensors/" + sensor_id + "/state/lastupdated",
             "operator": "dx"}],
         "name": "Dimmer Switch " + sensor_id + " rotate right"},
        {"actions": [
            {"address": "/groups/" + group_id + "/action",
             "body":
                {"bri_inc": 56,
                 "transitiontime": 9},
             "method": "PUT"}],
         "conditions": [
            {"address": "/groups/" + group_id + "/state/any_on",
             "operator": "eq",
             "value": "true"},
            {"address": "/sensors/" + sensor_id + "/state/buttonevent",
             "operator": "eq",
             "value": "1002"},
            {"address": "/sensors/" + sensor_id + "/state/lastupdated",
             "operator": "dx"}],
         "name": "Dimmer Switch " + sensor_id + " rotate fast right"},
        {"actions": [
            {"address": "/groups/" + group_id + "/action",
             "body": {
                 "bri_inc": -32,
                 "transitiontime": 9},
             "method": "PUT"}],
         "conditions": [
            {"address": "/groups/" + group_id + "/action/bri",
             "operator": "gt",
             "value": "1"},
            {"address": "/sensors/" + sensor_id + "/state/buttonevent",
             "operator": "eq",
             "value": "3002"},
            {"address": "/sensors/" + sensor_id + "/state/lastupdated",
             "operator": "dx"}],
         "name": "Dimmer Switch " + sensor_id + " rotate left"},
        {"actions": [
            {"address": "/groups/" + group_id + "/action",
             "body": {
                "bri_inc": -56,
                "transitiontime": 9},
             "method": "PUT"}],
         "conditions": [
            {"address": "/groups/" + group_id + "/action/bri",
             "operator": "gt",
             "value": "1"},
            {"address": "/sensors/" + sensor_id + "/state/buttonevent",
             "operator": "eq",
             "value": "4002"},
            {"address": "/sensors/" + sensor_id + "/state/lastupdated",
             "operator": "dx"}],
         "name": "Dimmer Switch " + sensor_id + " rotate left"}]
    resourcelink_id = registry.next_free_id("resourcelinks")
    registry.resourcelinks[resourcelink_id] = {
        "classid": 15555,
        "description": "Rules for sensor " + sensor_id,
        "links": ["/sensors/" + sensor_id],
        "name": "Emulator rules " + sensor_id,
        "owner": list(registry.config["whitelist"])[0]}
    for rule in rules:
        rule_id = registry.next_free_id("rules")
        registry.rules[rule_id] = rule
        registry.rules[rule_id].update({
            "creationtime": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
            "lasttriggered": None,
            "owner": list(registry.config["whitelist"])[0],
            "recycle": True,
            "status": "enabled",
            "timestriggered": 0})
        registry.resourcelinks[resourcelink_id]["links"].append("/rules/" + rule_id)


def add_tradfri_ct_remote(registry, sensor_id, group_id):
    """????

    .. todo:: Recoding
    """
    rules = [
        {"actions": [
            {"address": "/groups/" + group_id + "/action",
             "body": {"on": True},
             "method": "PUT"}],
         "conditions": [
            {"address": "/sensors/" + sensor_id + "/state/lastupdated",
             "operator": "dx"},
            {"address": "/sensors/" + sensor_id + "/state/buttonevent",
             "operator": "eq",
             "value": "1002"},
            {"address": "/groups/" + group_id + "/state/any_on",
             "operator": "eq",
             "value": "false"}],
         "name": "Remote " + sensor_id + " button on"},
        {"actions": [
            {"address": "/groups/" + group_id + "/action",
             "body": {"on": False},
             "method": "PUT"}],
         "conditions": [
            {"address": "/sensors/" + sensor_id + "/state/lastupdated",
             "operator": "dx"},
            {"address": "/sensors/" + sensor_id + "/state/buttonevent",
             "operator": "eq",
             "value": "1002"},
            {"address": "/groups/" + group_id + "/state/any_on",
             "operator": "eq",
             "value": "true"}],
         "name": "Remote " + sensor_id + " button off"},
        {"actions": [
            {"address": "/groups/" + group_id + "/action",
             "body": {"bri_inc": 30, "transitiontime": 9},
             "method": "PUT"}],
         "conditions": [
            {"address": "/sensors/" + sensor_id + "/state/buttonevent",
             "operator": "eq",
             "value": "2002"},
            {"address": "/sensors/" + sensor_id + "/state/lastupdated",
             "operator": "dx"}],
         "name": "Dimmer Switch " + sensor_id + " up-press"},
        {"actions": [
            {"address": "/groups/" + group_id + "/action",
             "body": {"bri_inc": 56, "transitiontime": 9},
             "method": "PUT"}],
         "conditions": [
            {"address": "/sensors/" + sensor_id + "/state/buttonevent",
             "operator": "eq",
             "value": "2001"},
            {"address": "/sensors/" + sensor_id + "/state/lastupdated",
             "operator": "dx"}],
         "name": "Dimmer Switch " + sensor_id + " up-long"},
        {"actions": [
            {"address": "/groups/" + group_id + "/action",
             "body": {"bri_inc": -30, "transitiontime": 9},
             "method": "PUT"}],
         "conditions": [
            {"address": "/sensors/" + sensor_id + "/state/buttonevent",
             "operator": "eq",
             "value": "3002"},
            {"address": "/sensors/" + sensor_id + "/state/lastupdated",
             "operator": "dx"}],
         "name": "Dimmer Switch " + sensor_id + " dn-press"},
        {"actions": [
            {"address": "/groups/" + group_id + "/action",
             "body": {"bri_inc": -56, "transitiontime": 9},
             "method": "PUT"}],
         "conditions": [
            {"address": "/sensors/" + sensor_id + "/state/buttonevent",
             "operator": "eq",
             "value": "3001"},
            {"address": "/sensors/" + sensor_id + "/state/lastupdated",
             "operator": "dx"}],
         "name": "Dimmer Switch " + sensor_id + " dn-long"},
        {"actions": [
            {"address": "/groups/" + group_id + "/action",
             "body": {"ct_inc": 50, "transitiontime": 9},
             "method": "PUT"}],
         "conditions": [
            {"address": "/sensors/" + sensor_id + "/state/buttonevent",
             "operator": "eq",
             "value": "4002"},
            {"address": "/sensors/" + sensor_id + "/state/lastupdated",
             "operator": "dx"}],
         "name": "Dimmer Switch " + sensor_id + " ctl-press"},
        {"actions": [
            {"address": "/groups/" + group_id + "/action",
             "body": {"ct_inc": 100, "transitiontime": 9},
             "method": "PUT"}],
         "conditions": [
            {"address": "/sensors/" + sensor_id + "/state/buttonevent",
             "operator": "eq",
             "value": "4001"},
            {"address": "/sensors/" + sensor_id + "/state/lastupdated",
             "operator": "dx"}],
         "name": "Dimmer Switch " + sensor_id + " ctl-long"},
        {"actions": [
            {"address": "/groups/" + group_id + "/action",
             "body": {"ct_inc": -50, "transitiontime": 9},
             "method": "PUT"}],
         "conditions": [
            {"address": "/sensors/" + sensor_id + "/state/buttonevent",
             "operator": "eq",
             "value": "5002"},
            {"address": "/sensors/" + sensor_id + "/state/lastupdated",
             "operator": "dx"}],
         "name": "Dimmer Switch " + sensor_id + " ct-press"},
        {"actions": [
            {"address": "/groups/" + group_id + "/action",
             "body": {"ct_inc": -100, "transitiontime": 9},
             "method": "PUT"}],
         "conditions": [
            {"address": "/sensors/" + sensor_id + "/state/buttonevent",
             "operator": "eq",
             "value": "5001"},
            {"address": "/sensors/" + sensor_id + "/state/lastupdated",
             "operator": "dx"}],
         "name": "Dimmer Switch " + sensor_id + " ct-long"}]
    resourcelink_id = registry.next_free_id("resourcelinks")
    registry.resourcelinks[resourcelink_id] = {
        "classid": 15555,
        "description": "Rules for sensor " + sensor_id,
        "links": ["/sensors/" + sensor_id],
        "name": "Emulator rules " + sensor_id,
        "owner": list(registry.config["whitelist"])[0]}
    for rule in rules:
        rule_id = registry.next_free_id("rules")
        registry.rules[rule_id] = rule
        registry.rules[rule_id].update(
            {"creationtime": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
             "lasttriggered": None,
             "owner": list(registry.config["whitelist"])[0],
             "recycle": True,
             "status": "enabled",
             "timestriggered": 0})
        registry.resourcelinks[resourcelink_id]["links"].append("/rules/" + rule_id)


def add_tradfri_scene_remote(registry, sensor_id, group_id):
    """????

    .. todo:: Recoding
    """
    rules = [
        {"actions": [
            {"address": "/groups/" + group_id + "/action",
             "body": {"on": True},
             "method": "PUT"}],
         "conditions": [
            {"address": "/sensors/" + sensor_id + "/state/lastupdated",
             "operator": "dx"},
            {"address": "/sensors/" + sensor_id + "/state/buttonevent",
             "operator": "eq",
             "value": "1002"},
            {"address": "/groups/" + group_id + "/state/any_on",
             "operator": "eq",
             "value": "false"}],
         "name": "Remote " + sensor_id + " button on"},
        {"actions": [
            {"address": "/groups/" + group_id + "/action",
             "body": {"on": False},
             "method": "PUT"}],
         "conditions": [
            {"address": "/sensors/" + sensor_id + "/state/lastupdated",
             "operator": "dx"},
            {"address": "/sensors/" + sensor_id + "/state/buttonevent",
             "operator": "eq",
             "value": "1002"},
            {"address": "/groups/" + group_id + "/state/any_on",
             "operator": "eq",
             "value": "true"}],
         "name": "Remote " + sensor_id + " button off"},
        {"actions": [
            {"address": "/groups/" + group_id + "/action",
             "body": {"bri_inc": 30, "transitiontime": 9},
             "method": "PUT"}],
         "conditions": [
            {"address": "/sensors/" + sensor_id + "/state/buttonevent",
             "operator": "eq",
             "value": "2002"},
            {"address": "/sensors/" + sensor_id + "/state/lastupdated",
             "operator": "dx"}],
         "name": "Dimmer Switch " + sensor_id + " up-press"},
        {"actions": [
            {"address": "/groups/" + group_id + "/action",
             "body": {"bri_inc": 56, "transitiontime": 9},
             "method": "PUT"}],
         "conditions": [
            {"address": "/sensors/" + sensor_id + "/state/buttonevent",
             "operator": "eq",
             "value": "2001"},
            {"address": "/sensors/" + sensor_id + "/state/lastupdated",
             "operator": "dx"}],
         "name": "Dimmer Switch " + sensor_id + " up-long"},
        {"actions": [
            {"address": "/groups/" + group_id + "/action",
             "body": {"bri_inc": -30, "transitiontime": 9},
             "method": "PUT"}],
         "conditions": [
            {"address": "/sensors/" + sensor_id + "/state/buttonevent",
             "operator": "eq",
             "value": "3002"},
            {"address": "/sensors/" + sensor_id + "/state/lastupdated",
             "operator": "dx"}],
         "name": "Dimmer Switch " + sensor_id + " dn-press"},
        {"actions": [
            {"address": "/groups/" + group_id + "/action",
             "body": {"bri_inc": -56, "transitiontime": 9},
             "method": "PUT"}],
         "conditions": [
            {"address": "/sensors/" + sensor_id + "/state/buttonevent",
             "operator": "eq",
             "value": "3001"},
            {"address": "/sensors/" + sensor_id + "/state/lastupdated",
             "operator": "dx"}],
         "name": "Dimmer Switch " + sensor_id + " dn-long"},
        {"actions": [
            {"address": "/groups/" + group_id + "/action",
             "body": {"scene_inc": -1},
             "method": "PUT"}],
         "conditions": [
            {"address": "/sensors/" + sensor_id + "/state/buttonevent",
             "operator": "eq",
             "value": "4002"},
            {"address": "/sensors/" + sensor_id + "/state/lastupdated",
             "operator": "dx"}],
         "name": "Dimmer Switch " + sensor_id + " ctl-press"},
        {"actions": [
            {"address": "/groups/" + group_id + "/action",
             "body": {"scene_inc": -1},
             "method": "PUT"}],
         "conditions": [
            {"address": "/sensors/" + sensor_id + "/state/buttonevent",
             "operator": "eq",
             "value": "4001"},
            {"address": "/sensors/" + sensor_id + "/state/lastupdated",
             "operator": "dx"}],
         "name": "Dimmer Switch " + sensor_id + " ctl-long"},
        {"actions": [
            {"address": "/groups/" + group_id + "/action",
             "body": {"scene_inc": 1},
             "method": "PUT"}],
         "conditions": [
            {"address": "/sensors/" + sensor_id + "/state/buttonevent",
             "operator": "eq",
             "value": "5002"},
            {"address": "/sensors/" + sensor_id + "/state/lastupdated",
             "operator": "dx"}],
         "name": "Dimmer Switch " + sensor_id + " ct-press"},
        {"actions": [
            {"address": "/groups/" + group_id + "/action",
             "body": {"scene_inc": 1},
             "method": "PUT"}],
         "conditions": [
            {"address": "/sensors/" + sensor_id + "/state/buttonevent",
             "operator": "eq",
             "value": "5001"},
            {"address": "/sensors/" + sensor_id + "/state/lastupdated",
             "operator": "dx"}],
         "name": "Dimmer Switch " + sensor_id + " ct-long"}]
    resourcelink_id = registry.next_free_id("resourcelinks")
    registry.resourcelinks[resourcelink_id] = {
        "classid": 15555,
        "description": "Rules for sensor " + sensor_id,
        "links": ["/sensors/" + sensor_id],
        "name": "Emulator rules " + sensor_id,
        "owner": list(registry.config["whitelist"])[0]}
    for rule in rules:
        rule_id = registry.next_free_id("rules")
        registry.rules[rule_id] = rule
        registry.rules[rule_id].update({
            "creationtime": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
            "lasttriggered": None,
            "owner": list(registry.config["whitelist"])[0],
            "recycle": True,
            "status": "enabled",
            "timestriggered": 0})
        registry.resourcelinks[resourcelink_id]["links"].append("/rules/" + rule_id)

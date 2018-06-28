from datetime import datetime
from uuid import getnode as get_mac
import hashlib
import random
import json

import requests
import hug
from jinja2 import FileSystemLoader, Environment

from huebridgeemulator.tools import generateSensorsState
from huebridgeemulator.web.templates import get_template
from huebridgeemulator.http.websocket import scanDeconz
from huebridgeemulator.tools.light import scanForLights, updateGroupStats
from threading import Thread
import time

import huebridgeemulator.web.ui

@hug.get('/api/{uid}/groups/{resource_id}')
def api_get_groups_id(uid, resource_id, request, response):
    """print specified object config."""
    print("api_groups_id")
    bridge_config = request.context['conf_obj'].bridge
    if uid in bridge_config["config"]["whitelist"]:
        return bridge_config['groups']


@hug.get('/api/{uid}/groups/new')
def api_get_groups_new(uid, request, response):
    """return new lights and sensors only."""
    print("api_groups_new")
    bridge_config = request.context['conf_obj'].bridge
    if uid in bridge_config["config"]["whitelist"]:
        print(request.context['conf_obj'].get_new_lights())
        response = request.context['conf_obj'].get_new_lights()
        request.context['conf_obj'].clear_new_lights()
        return response


@hug.get('/api/{uid}/groups')
def api_get_groups(uid, request, response):
    print("api_groups")
    bridge_config = request.context['conf_obj'].bridge
    return bridge_config['groups']

@hug.get('/api/{uid}/groups/0')
def api_get_groups_0(uid, request, response):
    print("api_groups_0")
    bridge_config = request.context['conf_obj'].bridge
    if uid in bridge_config["config"]["whitelist"]:
        any_on = False
        all_on = True
        for group_state in bridge_config["groups"].keys():
            if bridge_config["groups"][group_state]["state"]["any_on"] == True:
                any_on = True
            else:
                all_on = False
        return {"name": "Group 0",
                "lights": [l for l in bridge_config["lights"]],
                "type": "LightGroup",
                "state": {"all_on": all_on,
                          "any_on  ": any_on},
                "recycle": False,
                "action": {"on": True,
                           "bri": 254,
                            "hue": 47258,
                            "sat": 253,
                            "effect": "none",
                            "xy": [0.1424, 0.0824],
                            "ct": 153,
                            "alert": "none",
                            "colormode": "xy"}
                }
    return [{"error": {"type": 1, "address": request.path, "description": "unauthorized user" }}]

@hug.post('/api/{uid}/groups')
def api_post_groups(uid, body, request, response):
    bridge_config = request.context['conf_obj'].bridge
    if uid in bridge_config["config"]["whitelist"]:
        post_dictionary = body
        print("create objectcreate objectcreate objectcreate objectcreate object")
        print(request.path)
        # find the first unused id for new object
        new_object_id = request.context['conf_obj'].nextFreeId('groups')
        post_dictionary.update({"action": {"on": False}, "state": {"any_on": False, "all_on": False}})
        generateSensorsState(bridge_config, request.context['sensors_state'])
        bridge_config['groups'][new_object_id] = post_dictionary
        request.context['conf_obj'].save()
        print(json.dumps([{"success": {"id": new_object_id}}], sort_keys=True, indent=4, separators=(',', ': ')))
        return [{"success": {"id": new_object_id}}]
    else:
        return [{"error": {"type": 1, "address": request.path, "description": "unauthorized user" }}]
    

@hug.delete('/api/{uid}/groups/{resource_id}')
def api_delete_groups_id(uid, resource_id, request, response):
    bridge_config = request.context['conf_obj'].bridge
    if uid in bridge_config["config"]["whitelist"]:
        del bridge_config['groups'][resource_id]
        request.context['conf_obj'].save()
        return [{"success": "/groups/" + resource_id + " deleted."}]

#/api/a7161538be80d40b3de98dece6e91f90/groups/1/action
@hug.put('/api/{uid}/groups/{resource_id}/action')
def api_put_groups_id_action(uid, resource_id, body, request, response):
    bridge_config = request.context['conf_obj'].bridge
    put_dictionary = body
    if uid in bridge_config["config"]["whitelist"]:
        print("CCCCCCCCCCCCCCCCCCCCCCCCC")
        print(put_dictionary)
        if "scene" in put_dictionary: #scene applied to group
            #send all unique ip's in thread mode for speed
            lightsIps = []
            processedLights = []
            for light in bridge_config["scenes"][put_dictionary["scene"]]["lights"]:
                bridge_config["lights"][light]["state"].update(bridge_config["scenes"][put_dictionary["scene"]]["lightstates"][light])
                if bridge_config["lights_address"][light]["ip"] not in lightsIps:
                    lightsIps.append(bridge_config["lights_address"][light]["ip"])
                    processedLights.append(light)
                    current_light = request.context['conf_obj'].get_resource("lights", light)
                    if current_light.address.protocol in ("yeelight", "hue"):
                        Thread(target=current_light.send_request, args=[bridge_config["scenes"][put_dictionary["scene"]]["lightstates"][light]]).start()
                    else:
                        Thread(target=sendLightRequest, args=[request.context['conf_obj'], light, bridge_config["scenes"][put_dictionary["scene"]]["lightstates"][light]]).start()
            time.sleep(0.2) #give some time for the device to process the threaded request
            #now send the rest of the requests in non threaded mode
            for light in bridge_config["scenes"][put_dictionary["scene"]]["lights"]:
                if light not in processedLights:
                    current_light = request.context['conf_obj'].get_resource("lights", light)
                    if current_light.manufacturername in ("yeelight", "hue"):
                        current_light.send_request(bridge_config["scenes"][put_dictionary["scene"]]["lightstates"][light])
                    else:
                        sendLightRequest(request.context['conf_obj'], light, bridge_config["scenes"][put_dictionary["scene"]]["lightstates"][light])
                updateGroupStats(request.context['conf_obj'], light)
        elif "bri_inc" in put_dictionary:
            bridge_config["groups"][resource_id]["action"]["bri"] += int(put_dictionary["bri_inc"])
            if bridge_config["groups"][resource_id]["action"]["bri"] > 254:
                bridge_config["groups"][resource_id]["action"]["bri"] = 254
            elif bridge_config["groups"][resource_id]["action"]["bri"] < 1:
                bridge_config["groups"][resource_id]["action"]["bri"] = 1
            bridge_config["groups"][resource_id]["state"]["bri"] = bridge_config["groups"][resource_id]["action"]["bri"]
            del put_dictionary["bri_inc"]
            put_dictionary.update({"bri": bridge_config["groups"][resource_id]["action"]["bri"]})
            for light in bridge_config["groups"][resource_id]["lights"]:
                bridge_config["lights"][light]["state"].update(put_dictionary)
                sendLightRequest(request.context['conf_obj'], light, put_dictionary)
        elif "ct_inc" in put_dictionary:
            bridge_config["groups"][resource_id]["action"]["ct"] += int(put_dictionary["ct_inc"])
            if bridge_config["groups"][resource_id]["action"]["ct"] > 500:
                bridge_config["groups"][resource_id]["action"]["ct"] = 500
            elif bridge_config["groups"][resource_id]["action"]["ct"] < 153:
                bridge_config["groups"][resource_id]["action"]["ct"] = 153
            bridge_config["groups"][resource_id]["state"]["ct"] = bridge_config["groups"][resource_id]["action"]["ct"]
            del put_dictionary["ct_inc"]
            put_dictionary.update({"ct": bridge_config["groups"][resource_id]["action"]["ct"]})
            for light in bridge_config["groups"][resource_id]["lights"]:
                bridge_config["lights"][light]["state"].update(put_dictionary)
                sendLightRequest(request.context['conf_obj'], light, put_dictionary)
        elif "scene_inc" in put_dictionary:
            switchScene(resource_id, put_dictionary["scene_inc"])
        elif resource_id == "0": #if group is 0 the scene applied to all lights
            for light in bridge_config["lights"].keys():
                if "virtual_light" not in bridge_config["alarm_config"] or light != bridge_config["alarm_config"]["virtual_light"]:
                    bridge_config["lights"][light]["state"].update(put_dictionary)
                    current_light = request.context['conf_obj'].get_resource("lights", light)
                    if current_light.manufacturername in ("yeelight", "hue"):
                        current_light.send_request(put_dictionary)
                    else:
                        sendLightRequest(request.context['conf_obj'], light, put_dictionary)

            for group in bridge_config["groups"].keys():
                bridge_config["groups"][group][url_pices[5]].update(put_dictionary)
                if "on" in put_dictionary:
                    bridge_config["groups"][group]["state"]["any_on"] = put_dictionary["on"]
                    bridge_config["groups"][group]["state"]["all_on"] = put_dictionary["on"]
        else: # the state is applied to particular group (resource_id)
            if "on" in put_dictionary:
                bridge_config["groups"][resource_id]["state"]["any_on"] = put_dictionary["on"]
                bridge_config["groups"][resource_id]["state"]["all_on"] = put_dictionary["on"]
            bridge_config["groups"][resource_id]["action"].update(put_dictionary)
            #send all unique ip's in thread mode for speed
            lightsIps = []
            processedLights = []
            for light in bridge_config["groups"][resource_id]["lights"]:
                bridge_config["lights"][light]["state"].update(put_dictionary)
                if bridge_config["lights_address"][light]["ip"] not in lightsIps:
                    lightsIps.append(bridge_config["lights_address"][light]["ip"])
                    processedLights.append(light)
                    current_light = request.context['conf_obj'].get_resource("lights", light)
                    if current_light.address.protocol in ("yeelight", "hue"):
                        Thread(target=current_light.send_request, args=[put_dictionary]).start()
                    else:
                        Thread(target=sendLightRequest, args=[request.context['conf_obj'], light, put_dictionary]).start()
            time.sleep(0.2) #give some time for the device to process the threaded request
            #now send the rest of the requests in non threaded mode
            for light in bridge_config["groups"][resource_id]["lights"]:
                if light not in processedLights:
                    sendLightRequest(request.context['conf_obj'], light, put_dictionary)
        request.context['conf_obj'].save()

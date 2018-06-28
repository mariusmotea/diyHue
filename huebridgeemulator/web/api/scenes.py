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
from huebridgeemulator.tools.light import scanForLights
from threading import Thread
import time

import huebridgeemulator.web.ui

@hug.get('/api/{uid}/scenes/{resource_id}')
def api_get_scenes_id(uid, resource_id, request, response):
    """print specified object config."""
    print("api_get_scenes_id")
    bridge_config = request.context['conf_obj'].bridge
    if uid in bridge_config["config"]["whitelist"]:
        return bridge_config['scenes']


@hug.get('/api/{uid}/scenes')
def api_get_scenes(uid, request, response):
    print("api_get_scenes")
    bridge_config = request.context['conf_obj'].bridge
    if uid in bridge_config["config"]["whitelist"]:
        return bridge_config['scenes']


@hug.post('/api/{uid}/scenes')
def api_post_scenes(uid, body, request, response):
    print("api_post_scenes")
    bridge_config = request.context['conf_obj'].bridge
    if uid in bridge_config["config"]["whitelist"]:
        post_dictionary = body
        # find the first unused id for new object
        new_object_id = request.context['conf_obj'].nextFreeId('scenes')
        post_dictionary.update({"lightstates": {}, "version": 2, "picture": "", "lastupdated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"), "owner" :uid})
        if "locked" not in post_dictionary:
            post_dictionary["locked"] = False
        generateSensorsState(bridge_config, request.context['sensors_state'])
        bridge_config['scenes'][new_object_id] = post_dictionary
        request.context['conf_obj'].save()
        print(json.dumps([{"success": {"id": new_object_id}}], sort_keys=True, indent=4, separators=(',', ': ')))
        return [{"success": {"id": new_object_id}}]
    else:
        return [{"error": {"type": 1, "address": request.path, "description": "unauthorized user" }}]


@hug.delete('/api/{uid}/scenes/{resource_id}')
def api_delete_scenes_id(uid, resource_id, request, response):
    print("api_delete_scenes_id")
    bridge_config = request.context['conf_obj'].bridge
    if uid in bridge_config["config"]["whitelist"]:
        del bridge_config['scenes'][resource_id]
        request.context['conf_obj'].save()
        return [{"success": "/scenes/" + resource_id + " deleted."}]


@hug.put('/api/{uid}/scenes/{resource_id}/lightstates/{light_id}')
def api_put_scenes_id_light_id(uid, resource_id, light_id, body, request, response):
    print("api_put_scenes_id_light_id")
    bridge_config = request.context['conf_obj'].bridge
    put_dictionary = body
    if uid in bridge_config["config"]["whitelist"]:
        # WHY ????
        try:
            bridge_config['scenes'][resource_id]['lightstates'][light_id].update(put_dictionary)
        except KeyError:
            bridge_config['scenes'][resource_id]['lightstates'][light_id] = put_dictionary
        # Those lines are useless because of the next one ...
        bridge_config['scenes'][resource_id]['lightstates'][light_id] = put_dictionary
        response_location = "/scenes/" + resource_id + "/lightstates/" + light_id + "/"
    response_dictionary = []
    for key, value in put_dictionary.items():
        response_dictionary.append({"success":{response_location + key: value}})
    print(json.dumps(response_dictionary, sort_keys=True, indent=4, separators=(',', ': ')))
    request.context['conf_obj'].save()
    return response_dictionary


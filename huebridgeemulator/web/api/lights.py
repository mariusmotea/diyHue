from datetime import datetime
from uuid import getnode as get_mac
import hashlib
import random
import json
from threading import Thread
import time

import requests
import hug
from jinja2 import FileSystemLoader, Environment

from huebridgeemulator.tools import generateSensorsState
from huebridgeemulator.web.templates import get_template
from huebridgeemulator.http.websocket import scanDeconz
from huebridgeemulator.tools.light import scanForLights
from huebridgeemulator.tools.group import update_group_status
from huebridgeemulator.device.light import LightState
from huebridgeemulator.logger import http_logger
import huebridgeemulator.web.ui
from huebridgeemulator.web.tools import authorized


@hug.get('/api/{uid}/lights/new', requires=authorized)
def api_get_lights_new(uid, request, response):
    """return new lights and sensors only."""
    registry = request.context['registry']
    response = registry.get_new_lights()
    registry.clear_new_lights()
    http_logger.debug("Return new lights and sensors: %s", response)  
    return response


# TODO Add decorator to check if uid in bridge_config["config"]["whitelist"]
@hug.get('/api/{uid}/lights/{resource_id}', requires=authorized)
def api_get_lights_id(uid, resource_id, request, response):
    """print specified object config."""
    # USELESS FOR NOW
    bridge_config = request.context['conf_obj'].bridge
    return request.context['conf_obj'].get_json_lights()


@hug.get('/api/{uid}/lights', requires=authorized)
def api_get_lights(uid, request, response):
    registry = request.context['conf_obj']
    output = {}
    for index, light in registry.lights.items():
            output[index] = light.serialize()
    return output


@hug.post('/api/{uid}/lights', requires=authorized)
def api_post_lights(uid, body, request, response):
    registry = request.context['registry']
    import ipdb;ipdb.set_trace()
    # Improve this if
    if not bool(body):
        Thread(target=scanForLights,
               args=[registry,
                     request.context['new_lights']]).start()
        # TODO wait this thread but add a timeout
        time.sleep(7)
        return [{"success": {"/" + uid: "Searching for new devices"}}]
    else: #create object
        #TODO check if this block is used 
        raise
        post_dictionary = body
        # find the first unused id for new object
        new_object_id = registry.nextFreeId('lights')
        
        generateSensorsState(bridge_config, request.context['sensors_state'])
        bridge_config['lights'][new_object_id] = post_dictionary
        request.context['conf_obj'].save()
        print(json.dumps([{"success": {"id": new_object_id}}], sort_keys=True, indent=4, separators=(',', ': ')))
        return [{"success": {"id": new_object_id}}]

    
@hug.put('/api/{uid}/lights/{resource_id}', requires=authorized)
def api_put_lights_id(uid, resource_id, body, request, response):
    """Update light settings.

    For now we can change only the lighti name.
    """
    registry = request.context['registry']
    light = registry.lights[resource_id]
    light.set_name(body['name'])
    registry.save()
    return [{"success": {"id": light.index}}]


@hug.delete('/api/{uid}/lights/{resource_id}', requires=authorized)
def api_delete_lights_id(uid, resource_id, request, response):
    registry = request.context['registry']
    del registry.lights[resource_id]
    for light_id in list(registry.deconz["lights"]):
        if registry.deconz["lights"][light_id]["bridgeid"] == resource_id:
            del registry.deconz["lights"][light]
    registry.save()
    return [{"success": "/lights/" + resource_id + " deleted."}]


@hug.put('/api/{uid}/lights/{resource_id}/state', requires=authorized)
def api_put_lights_id(uid, resource_id, body, request, response):
    registry = request.context['registry']
    put_dictionary = body
    for key in put_dictionary.keys():
        if key in ["ct", "xy"]: #colormode must be set by bridge
            registry.lights[resource_id].state.colormode = key
        elif key in ["hue", "sat"]:
            registry.lights[resource_id].state.colormode = "hs"

    update_group_status(registry, resource_id)

    current_light = registry.lights[resource_id]
    current_light.send_request(put_dictionary)
    #if not url_pices[4] == "0": #group 0 is virtual, must not be saved in bridge configuration
    if not resource_id == "0": #group 0 is virtual, must not be saved in bridge configuration
        for key, value in put_dictionary.items():
            setattr(registry.lights[resource_id].state, key, value)
    response_location = "/lights/" + resource_id + "/state/"
    response_dictionary = []
    for key, value in put_dictionary.items():
        response_dictionary.append({"success":{response_location + key: value}})
    registry.save()
    return response_dictionary

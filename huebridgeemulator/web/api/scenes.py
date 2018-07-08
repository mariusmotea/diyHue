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
from huebridgeemulator.scene import Scene
from threading import Thread
import time

import huebridgeemulator.web.ui
from huebridgeemulator.web.tools import authorized


@hug.get('/api/{uid}/scenes/{resource_id}', requires=authorized)
def api_get_scenes_id(uid, resource_id, request, response):
    """print specified object config."""
    registry = request.context['registry']
    output = {}
    for index, scene in registry.scenes.items():
        output[index] = scene.serialize()
    return output


@hug.get('/api/{uid}/scenes', requires=authorized)
def api_get_scenes(uid, request, response):
    bridge_config = request.context['conf_obj'].bridge
    return bridge_config['scenes']


@hug.post('/api/{uid}/scenes', requires=authorized)
def api_post_scenes(uid, body, request, response):
    registry = request.context['registry']
    post_dictionary = body
    post_dictionary.update({"lightstates": {},
                            "version": 2,
                            "picture": "",
                            "lastupdated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
                            "owner" :uid})
    if "locked" not in post_dictionary:
        post_dictionary["locked"] = False
    registry.generate_sensors_state(request.context['sensors_state'])
    new_scene = Scene(post_dictionary)
    registry.scenes[new_scene.index] = new_scene
    request.context['conf_obj'].save()
    return [{"success": {"id": new_scene.index}}]


@hug.delete('/api/{uid}/scenes/{resource_id}', requires=authorized)
def api_delete_scenes_id(uid, resource_id, request, response):
    registry = request.context['registry']
    del registry.scenes[resource_id]
    registry.save()
    return [{"success": "/scenes/" + resource_id + " deleted."}]


@hug.put('/api/{uid}/scenes/{resource_id}/lightstates/{light_id}', requires=authorized)
def api_put_scenes_id_light_id(uid, resource_id, light_id, body, request, response):
    registry = request.context['registry']
    scene = registry.scenes[resource_id]
    put_dictionary = body
    # WHY ????
    try:
        scene.lightstates[light_id].update(put_dictionary)
    except KeyError:
        scene.lightstates[light_id] = put_dictionary
    # Those lines are useless because of the next one ...
    scene.lightstates[light_id] = put_dictionary
    response_location = "/scenes/" + resource_id + "/lightstates/" + light_id + "/"
    response_dictionary = []
    for key, value in put_dictionary.items():
        response_dictionary.append({"success":{response_location + key: value}})
    response_dictionary.append({"success":{"/scenes/{}/name".format(resource_id): scene.name}})
    print("FFFFFFFFFFFFFFFFFFFFF")
    print(response_dictionary)
#    print(json.dumps(response_dictionary, sort_keys=True, indent=4, separators=(',', ': ')))
    registry.save()
    return response_dictionary

@hug.put('/api/{uid}/scenes/{resource_id}', requires=authorized)
def api_put_scenes_id_light_id(uid, resource_id, body, request, response):
    registry = request.context['registry']
    put_dictionary = body
    scene = registry.scenes[resource_id]
    if "storelightstate" in put_dictionary:
        for lighd_id in scene.lightstates:
            light = registry.lights[light_id]
            scene.lightstates[light_id] = {}
            scene.lightstates[light_id]["on"] = light.state.on
            scene.lightstates[light_id]["bri"] = light.state.bri
#            bridge_config["scenes"][resource_id]["lightstates"][light] = {}
#            bridge_config["scenes"][resource_id]["lightstates"][light]["on"] = bridge_config["lights"][light]["state"]["on"]
#            bridge_config["scenes"][resource_id]["lightstates"][light]["bri"] = bridge_config["lights"][light]["state"]["bri"]
            if light.state.colormode in ("ct", "xy"):
                scene.lightstates[light_id][light.state.colormode] = getattr(light.state, light.state.colormode)
#            if bridge_config["lights"][light]["state"]["colormode"] in ["ct", "xy"]:
 #               bridge_config["scenes"][resource_id]["lightstates"][light][bridge_config["lights"][light]["state"]["colormode"]] = bridge_config["lights"][light]["state"][bridge_config["lights"][light]["state"]["colormode"]]
            elif light.state.colormode == "hs" and "hue" in scene.lightstates[light_id]:
                scene.lightstates[light_id]["hue"] = light.state.hue
                scene.lightstates[light_id]["sat"] = light.state.sat
#            elif bridge_config["lights"][light]["state"]["colormode"] == "hs" and "hue" in bridge_config["scenes"][resource_id]["lightstates"][light]:
#                bridge_config["scenes"][resource_id]["lightstates"][light]["hue"] = bridge_config["lights"][light]["state"]["hue"]
#                bridge_config["scenes"][resource_id]["lightstates"][light]["sat"] = bridge_config["lights"][light]["state"]["sat"]
#        bridge_config["scenes"][resource_id].update(put_dictionary)
    for key, value in put_dictionary.items():
        if key not in 'storelightstate':
            setattr(scene, key, value)
#    import ipdb;ipdb.set_trace()
    print("HHHHHHHHHHHHHHHHHHHHHHHHHHH")

    registry.save()
    response_dictionary = []
    response_location = "/scenes/{}/".format(resource_id)
    for key, value in put_dictionary.items():
        response_dictionary.append({"success":{response_location + key: value}})
    response_dictionary.append({"success":{"/scenes/{}/storelightstate".format(resource_id): True}})
#    response_dictionary = [{"success":{"/scenes/{}/name".format(resource_id): scene.name}}]
    print(response_dictionary)
    return response_dictionary


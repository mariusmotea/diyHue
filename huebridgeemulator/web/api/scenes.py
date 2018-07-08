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
from huebridgeemulator.scene import Scene
import huebridgeemulator.web.ui
from huebridgeemulator.web.tools import authorized
from huebridgeemulator.logger import http_logger


@hug.get('/api/{uid}/scenes/{resource_id}', requires=authorized)
def api_get_scenes_id(uid, resource_id, request, response):
    """print specified object config.

    .. note:: Why we return all objects ? we ask only for one ...
    """
    registry = request.context['registry']
    output = {}
    # Why we return all objects ? we ask only for one ...
    for index, scene in registry.scenes.items():
        output[index] = scene.serialize()
    return output


@hug.get('/api/{uid}/scenes', requires=authorized)
def api_get_scenes(uid, request, response):
    """Return all scenes.

    .. note:: not used for now
    """
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
    http_logger.debug(response_dictionary)
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
            if light.state.colormode in ("ct", "xy"):
                scene.lightstates[light_id][light.state.colormode] = getattr(light.state, light.state.colormode)
            elif light.state.colormode == "hs" and "hue" in scene.lightstates[light_id]:
                scene.lightstates[light_id]["hue"] = light.state.hue
                scene.lightstates[light_id]["sat"] = light.state.sat
    for key, value in put_dictionary.items():
        if key not in 'storelightstate':
            setattr(scene, key, value)

    registry.save()
    response_dictionary = []
    response_location = "/scenes/{}/".format(resource_id)
    for key, value in put_dictionary.items():
        response_dictionary.append({"success":{response_location + key: value}})
    response_dictionary.append({"success":{"/scenes/{}/storelightstate".format(resource_id): True}})
    http_logger.debug(response_dictionary)
    return response_dictionary


"""Sensor Hue API module."""
from threading import Thread
import time

import hug

from huebridgeemulator.tools import generateSensorsState
from huebridgeemulator.tools.light import scanForLights
from huebridgeemulator.web.tools import authorized


@hug.get('/api/{uid}/sensors/{resource_id}', requires=authorized)
def api_get_sensors_id(uid, resource_id, request, response):  # pylint: disable=W0613
    """Return selected sensor.

    .. todo:: test it
    """
    bridge_config = request.context['conf_obj'].bridge
    return bridge_config['sensors']


@hug.get('/api/{uid}/sensors/new', requires=authorized)
def api_get_sensors_new(uid, request, response):  # pylint: disable=W0613
    """Return new sensors only.

    .. todo:: test it
    """
    registry = request.context['registry']
    response = registry.get_new_lights()
    registry.clear_new_lights()
    return response


@hug.get('/api/{uid}/sensors')
def api_get_sensors(uid, request, response):  # pylint: disable=W0613
    """Return all sensors.

    .. todo:: test it
    """
    registry = request.context['registry']
    output = dict([(index, sensor.serialize())
                   for index, sensor in registry.sensors.items()])
    return output


@hug.post('/api/{uid}/sensor', requires=authorized)
def api_post_sensor(uid, body, request, response):  # pylint: disable=W0613
    """Search for new sensors.

    .. todo:: refactor it
    """
    Thread(target=scanForLights,
           args=[request.context['registry'],
                 request.context['new_lights']]).start()
    # TODO wait this thread but add a timeout
    time.sleep(7)
    return [{"success": {"/" + uid: "Searching for new devices"}}]


@hug.post('/api/{uid}/sensors', requires=authorized)
def api_post_sensors(uid, body, request, response):  # pylint: disable=W0613
    """Create a new sensor.

    .. todo:: refactor it
    """
    bridge_config = request.context['conf_obj'].bridge
    post_dictionary = body
    # find the first unused id for new object
    new_object_id = request.context['conf_obj'].next_free_id('sensors')
    if "state" not in post_dictionary:
        post_dictionary["state"] = {}
    if post_dictionary["modelid"] == "PHWA01":
        post_dictionary.update({"state": {"status": 0}})
    generateSensorsState(bridge_config, request.context['sensors_state'])
    bridge_config['sensors'][new_object_id] = post_dictionary
    request.context['conf_obj'].save()
    return [{"success": {"id": new_object_id}}]


@hug.delete('/api/{uid}/sensors/{resource_id}', requires=authorized)
def api_delete_sensors_id(uid, resource_id, request, response):  # pylint: disable=W0613
    """Delete a sensor.

    .. todo:: test id
    """
    registry = request.context['registry']
    del registry.sensors[resource_id]
    for sensor in list(registry.deconz["sensors"]):
        if registry.deconz["sensors"][sensor]["bridgeid"] == resource_id:
            del registry.deconz["sensors"][sensor]
    registry.save()
    return [{"success": "/sensors/" + resource_id + " deleted."}]

"""Group Hue API module."""
import time
from threading import Thread

import hug

from huebridgeemulator.tools.light import sendLightRequest
from huebridgeemulator.tools.group import update_group_status
from huebridgeemulator.device.light import LightState
from huebridgeemulator.web.tools import authorized
from huebridgeemulator.group import Group, ActionGroup, StateGroup


@hug.get('/api/{uid}/groups/{resource_id}', requires=authorized)
def api_get_groups_id(uid, resource_id, request, response):  # pylint: disable=W0613
    """Return specified group.

    .. todo:: Is this useful ?
    """
    bridge_config = request.context['conf_obj'].bridge
    return bridge_config['groups']


@hug.get('/api/{uid}/groups/new', requires=authorized)
def api_get_groups_new(uid, request, response):  # pylint: disable=W0613
    """return new lights and sensors only."""
    response = request.context['registry'].get_new_lights()
    request.context['registry'].clear_new_lights()
    return response


@hug.get('/api/{uid}/groups')
def api_get_groups(uid, request, response):  # pylint: disable=W0613
    """Return a group.

    .. todo:: We return all groups, should we return only the selected one ?
    """
    registry = request.context['registry']
    output = {}
    for index, group in registry.groups.items():
        output[index] = group.serialize()
    return output


@hug.get('/api/{uid}/groups/0', requires=authorized)
def api_get_groups_0(uid, request, response):  # pylint: disable=W0613
    """????

    .. todo:: Add description

    .. todo:: test it
    """
    registry = request.context['registry']
    any_on = False
    all_on = True
    for group in registry.groups.values():
        # pylint: disable=R1703
        if group.state.any_on:
            any_on = True
        else:
            all_on = False
        # pylint: enable=R1703
    return {"name": "Group 0",
            "lights": [l for l in registry.lights],
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


@hug.post('/api/{uid}/groups', requires=authorized)
def api_post_groups(uid, body, request, response):  # pylint: disable=W0613
    """Create a new group."""
    registry = request.context['registry']
    post_dictionary = body
    post_dictionary.update({"action": ActionGroup({"on": False}),
                            "state": StateGroup({"any_on": False, "all_on": False})})
    registry.generate_sensors_state(request.context['sensors_state'])
    new_group = Group(post_dictionary)
    registry.groups[new_group.index] = new_group
    registry.save()
    return [{"success": {"id": new_group.index}}]


@hug.put('/api/{uid}/groups/{resource_id}', requires=authorized)
def api_put_groups_id(uid, resource_id, body, request, response):  # pylint: disable=W0613
    """Update group."""
    registry = request.context['registry']
    group = registry.groups[resource_id]
    for key, value in body.items():
        setattr(group, key, value)
    registry.save()
    return [{"success": {"id": group.index}}]


@hug.delete('/api/{uid}/groups/{resource_id}', requires=authorized)
def api_delete_groups_id(uid, resource_id, request, response):  # pylint: disable=W0613
    """Delete group."""
    registry = request.context['registry']
    del registry.groups[resource_id]
    registry.save()
    return [{"success": "/groups/" + resource_id + " deleted."}]


@hug.put('/api/{uid}/groups/{resource_id}/action', requires=authorized)
# pylint: disable=W0613, R0912
def api_put_groups_id_action(uid, resource_id, body, request, response):
    # pylint: enable=W0613, R0912
    """Apply state to a group/room.

    .. todo:: Simplify this function bu reducing the number of lines.

        And remove pylint: disable=R0912
    """
    registry = request.context['registry']
    put_dictionary = body
    if "scene" in put_dictionary:  # Scene applied to group
        scene = registry.scenes[put_dictionary["scene"]]
        # Send all unique ip's in thread mode for speed
        lights_ips = []
        processed_lights = []
        for light_id in registry.scenes[scene.index].lights:
            light = registry.lights[light_id]
            light.state = LightState(scene.lightstates[light.index])
            if light.address.ip not in lights_ips:
                lights_ips.append(light.address.ip)
                processed_lights.append(light_id)
                Thread(target=light.send_request, args=[scene.lightstates[light.index]]).start()

        # TODO Remove this sleep and create a ThreadPool then wait for the completion of all thread
        time.sleep(0.2)  # Give some time for the device to process the threaded request
        # Now send the rest of the requests in non threaded mode
        for light_id in registry.scenes[scene.index].lights:
            if light_id not in processed_lights:
                light = registry.lights[light_id]
                if light.address.protocol in ("yeelight", "hue", "tplink"):
                    light.send_request(scene.lightstates[light.index])
                else:
                    sendLightRequest(registry, light.index, scene.lightstates[light.index])
            update_group_status(registry, light)
    elif "bri_inc" in put_dictionary:
        # TODO comments
        registry.groups[resource_id].action.bri += int(put_dictionary["bri_inc"])
        if registry.groups[resource_id].action.bri > 254:
            registry.groups[resource_id].action.bri = 254
        elif registry.groups[resource_id].action.bri < 1:
            registry.groups[resource_id].action.bri = 1
        registry.groups[resource_id].state.bri = registry.groups[resource_id].action.bri
        del put_dictionary["bri_inc"]
        put_dictionary.update({"bri": registry.groups[resource_id].action.bri})
        for light_id in registry.groups[resource_id].lights:
            registry.lights[light_id].state = LightState(put_dictionary)
            registry.lights[light_id].send_request(put_dictionary)
    elif "ct_inc" in put_dictionary:
        # TODO comments
        registry.groups[resource_id].action.ct += int(put_dictionary["ct_inc"])
        if registry.groups[resource_id].action.ct > 500:
            registry.groups[resource_id].action.ct = 500
        elif registry.groups[resource_id].action.ct < 153:
            registry.groups[resource_id].action.ct = 153
        registry.groups[resource_id].state.ct = registry.groups[resource_id].action.ct
        del put_dictionary["ct_inc"]
        put_dictionary.update({"ct": registry.groups[resource_id].action.ct})
        for light_id in registry.groups[resource_id].lights:
            registry.lights[light_id].state = LightState(put_dictionary)
            registry.lights[light_id].send_request(put_dictionary)
    elif "scene_inc" in put_dictionary:
        # TODO switchScene should be implemented in tools
        # switchScene(resource_id, put_dictionary["scene_inc"])
        raise Exception("`switchScene` should be implemented in tools")
    elif resource_id == "0":  # If group is 0 the scene applied to all lights
        for index, light in registry.lights.items():
            if not hasattr(registry.alarm_config, "virtual_light") \
                    or light != registry.alarm_config["virtual_light"]:
                new_state = LightState(put_dictionary)
                light.state = new_state
                if light.address.protocol in ("yeelight", "hue", "tplink"):
                    light.send_request(put_dictionary)
                else:
                    sendLightRequest(registry, index, put_dictionary)
        for index, group in registry.groups.items():
            # Update action
            for key, value in put_dictionary.items():
                setattr(group.action, key, value)
            if "on" in put_dictionary:
                group.state.any_on = put_dictionary["on"]
                group.state.all_on = put_dictionary["on"]
    else:  # the state is applied to particular group (resource_id)
        group = registry.groups[resource_id]
        if "on" in put_dictionary:
            group.state.any_on = put_dictionary["on"]
            group.state.all_on = put_dictionary["on"]
        # Update action
        for key, value in put_dictionary.items():
            setattr(group.action, key, value)
        # Send all unique ip's in thread mode for speed
        lights_ips = []
        processed_lights = []
        for light_id in group.lights:
            light = registry.lights[light_id]
            new_state = LightState(put_dictionary)
            light.state = new_state
            if light.address.ip not in lights_ips:
                lights_ips.append(light.address.ip)
                processed_lights.append(light_id)
                Thread(target=light.send_request, args=[put_dictionary]).start()
        time.sleep(0.2)  # Give some time for the device to process the threaded request
        # Now send the rest of the requests in non threaded mode
        for light_id in group.lights:
            light = registry.lights[light_id]
            if light_id not in processed_lights:
                if light.address.protocol in ("yeelight", "hue", "tplink"):
                    light.send_request(put_dictionary)
                else:
                    sendLightRequest(registry, light_id, put_dictionary)
    registry.save()

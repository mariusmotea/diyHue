"""Module serving all web pages."""

from datetime import datetime
import random
import json
import base64

import requests
import hug
from falcon import HTTP_404

from huebridgeemulator.web.templates import get_template, get_static
from huebridgeemulator.tools.deconz import scanDeconz
from huebridgeemulator.device.tradfri import (
    add_tradfri_scene_remote, add_tradfri_ct_remote, add_tradfri_dimmer)
from huebridgeemulator.device.hue.light import HueLight, HueLightAddress
from huebridgeemulator.device.hue import add_hue_switch
from huebridgeemulator.tools import send_email, rules_processor


MIMETYPES = {"json": "application/json",
             "map": "application/json",
             "html": "text/html",
             "xml": "application/xml",
             "js": "text/javascript",
             "css": "text/css",
             "png": "image/png"}


@hug.get('/', output=hug.output_format.html)
@hug.get('/{filename}.{ext}', output=hug.output_format.html)
@hug.get('/static/{filename}.{ext}', output=hug.output_format.html)
@hug.get('/static/js/{filename}.{ext}', output=hug.output_format.html)
@hug.get('/static/css/{filename}.{ext}', output=hug.output_format.html)
def root(request, response, filename="index", ext="html"):  # pylint: disable=W0613
    """Server static files"""
    if request.path == "/":
        return hug.redirect.to('index.html')
    try:
        response.set_header('Content-type', MIMETYPES.get(ext, "text/html"))
        return get_static(request.path)
    except FileNotFoundError:
        response.status = HTTP_404
    return ""


@hug.get('/config.js', output=hug.output_format.html)
def configjs(request, response):
    """Server config.js file."""
    registry = request.context['registry']
    if not registry.config["whitelist"]:
        key = "web-ui-" + str(random.randrange(0, 99999))
        registry.config["whitelist"][key] = {
            "create date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "last use date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "name": "WegGui User"}
    response.set_header('Content-type', 'text/javascript')
    return 'window.config = { API_KEY: "' + list(registry.config["whitelist"])[0] + '",};'


@hug.get('/debug/clip.html', output=hug.output_format.html)
def debug_clip(request, response):  # pylint: disable=W0613
    """????

    .. todo:: Missing template file content
    """
    template = get_template('clip.html.j2')
    return template.render({})


@hug.get('/save')
def save(request, response):  # pylint: disable=W0613
    """Save registry on the disk."""
    request.context['registry'].save()
    return "config saved"


# pylint: disable=C0103, E1120
authentication = hug.authentication.basic(hug.authentication.verify('Hue', 'Hue'))
# pylint: enable=C0103, E1120


#@hug.get('/hue/linkbutton', requires=authentication, output=hug.output_format.html)
@hug.get('/hue/linkbutton', output=hug.output_format.html)
def linkbutton(request, response):  # pylint: disable=W0613

    """Server Hue Link button.

    .. todo"" handle user/password change
    """
    print("EEE")
    registry = request.context['registry']
    template = get_template('webform_linkbutton.html.j2')
    if request.params.get('action') == "Activate":
        registry.config["linkbutton"] = False
        registry.linkbutton.lastlinkbuttonpushed = datetime.now().strftime("%s")
        registry.save()
        return template.render({"message": "You have 30 sec to connect your device"})
    elif request.params.get('action') == "Exit":
        return 'You are succesfully disconnected'
    elif request.params.get('action') == "ChangePassword":
        tmp_password = str(base64.b64encode(bytes(request.params["username"][0] +
                                                  ":" +
                                                  request.params["password"][0],
                                                  "utf8"))).split('\'')
        registry.linkbutton.linkbutton_auth = tmp_password[1]
        registry.save()
        return template.render({"message": "Your credentials are succesfully change. "
                                           "Please logout then login again"})
    return template.render({})


@hug.get('/hue', output=hug.output_format.html)
def hue(request, response):
    """Server hue web page to connect to a real Hue Bridge."""
    registry = request.context['registry']
    template = get_template('webform_hue.html.j2')
    if request.params.get('ip'):
        url = "http://" + request.params.get('ip') + "/api/"
        data = json.dumps({"devicetype": "Hue Emulator"})
        query = requests.post(url, data=data)
        response = query.json()
        if "success" in response[0]:
            url = "http://{}/api/{}/lights".format(request.params.get('ip'),
                                                   response[0]["success"]["username"])
            query = requests.get(url)
            hue_lights = query.json()
            lights_found = 0
            for hue_light_id in hue_lights.keys():
                # TODO test me
                #import ipdb;ipdb.set_trace()
                hue_light_address = HueLightAddress({"username": response[0]["success"]["username"],
                                                     "light_id": hue_light_id,
                                                     "ip": request.params.get('ip'),
                                                     "protocol": "hue"})
                hue_lights[hue_light_id]['address'] = hue_light_address
                new_light = HueLight(hue_lights[hue_light_id])
                registry.lights[new_light.index] = new_light
                lights_found += 1
            if lights_found == 0:
                return template.render({"message": "No lights where found"})
            return template.render({"message": "{} lights where found".format(lights_found)})
        return template.render({"message": "unable to connect to hue bridge"})
    return template.render({})


@hug.get('/tradfri')
def tradfri(request, response):  # pylint: disable=W0613
    """Request for tradfri

    .. todo:: refactor me and test me
    """
    return {}


@hug.get('/milight')
def milight(request, response):  # pylint: disable=W0613
    """Request for milight

    .. todo:: refactor me and test me
    """
    return {}


@hug.get('/deconz')
def deconz(request, response):  # pylint: disable=W0613
    """???

    .. todo:: description, refactoring and test
    """
    # pylint: disable
    template = get_template('webform_deconz.html.j2')
    bridge_config = request.context['conf_obj'].bridge
    # clean all rules related to deconz Switches
    # TODO improve this if condition
    if request.params:
        emulator_resourcelinkes = []
        for resourcelink in bridge_config["resourcelinks"].keys():
            # delete all previews rules of IKEA remotes
            if bridge_config["resourcelinks"][resourcelink]["classid"] == 15555:
                emulator_resourcelinkes.append(resourcelink)
                for link in bridge_config["resourcelinks"][resourcelink]["links"]:
                    pices = link.split('/')
                    if pices[1] == "rules":
                        try:
                            del bridge_config["rules"][pices[2]]
                        except Exception:  # pylint: disable=W0703
                            print("unable to delete the rule " + pices[2])
        for resourcelink in emulator_resourcelinkes:
            del bridge_config["resourcelinks"][resourcelink]
        for key in request.params.keys():
            if request.params[key][0] in ["ZLLSwitch", "ZGPSwitch"]:
                try:
                    del bridge_config["sensors"][key]
                except Exception:  # pylint: disable=W0703
                    pass
                hue_switch_id = add_hue_switch("", request.params[key][0])
                for sensor in bridge_config["deconz"]["sensors"].keys():
                    if bridge_config["deconz"]["sensors"][sensor]["bridgeid"] == key:
                        bridge_config["deconz"]["sensors"][sensor] = {
                            "hueType": request.params[key][0],
                            "bridgeid": hue_switch_id}
            elif not key.startswith("mode_"):
                if bridge_config["sensors"][key]["modelid"] == "TRADFRI remote control":
                    if request.params["mode_" + key][0] == "CT":
                        add_tradfri_ct_remote(key, request.params[key][0])
                    elif request.params["mode_" + key][0] == "SCENE":
                        add_tradfri_scene_remote(key, request.params[key][0])
                elif bridge_config["sensors"][key]["modelid"] == "TRADFRI wireless dimmer":
                    add_tradfri_dimmer(key, request.params[key][0])
                # store room id in deconz sensors
                for sensor in bridge_config["deconz"]["sensors"].keys():
                    if bridge_config["deconz"]["sensors"][sensor]["bridgeid"] == key:
                        bridge_config["deconz"]["sensors"][sensor]["room"] = request.params[key][0]
                        if bridge_config["sensors"][key]["modelid"] == "TRADFRI remote control":
                            bridge_config["deconz"]["sensors"][sensor]["opmode"] = \
                                request.params["mode_" + key][0]
    else:
        # TODO ADD Comments
        scanDeconz(request.context['registry'])
    return template.render({"deconz": bridge_config["deconz"],
                            "sensors": bridge_config["sensors"],
                            "groups": bridge_config["groups"]})


@hug.get('/switch')
def switch(request, response):  # pylint: disable=W0612
    """Request from an ESP8266 switch or sensor.

    .. todo:: refactoring and test
    """
    registry = request.context['registry']
    bridge_config = request.context['conf_obj'].bridge
    if "devicetype" in request.params:  # register device request
        sensor_is_new = True
        for sensor in bridge_config["sensors"]:
            # if sensor is already present
            if bridge_config["sensors"][sensor]["uniqueid"].startswith(request.params["mac"][0]):
                sensor_is_new = False
        if sensor_is_new:
            print("registering new sensor " + request.params["devicetype"][0])
            new_sensor_id = registry.next_free_id("sensors")
            if request.params["devicetype"][0] in ["ZLLSwitch", "ZGPSwitch"]:
                print(request.params["devicetype"][0])
                add_hue_switch(request.params["mac"][0], request.params["devicetype"][0])
            elif request.params["devicetype"][0] == "ZLLPresence":
                print("ZLLPresence")
                addHueMotionSensor(request.params["mac"][0])
            regsitry.generate_sensors_state(bridge_config, request.context['sensors_state'])
    else:  # switch action request
        for sensor in bridge_config["sensors"]:
            # match senser id based on mac address
            if bridge_config["sensors"][sensor]["uniqueid"].startswith(request.params["mac"][0]) \
                    and bridge_config["sensors"][sensor]["config"]["on"]:
                print("match sensor " + str(sensor))
                if bridge_config["sensors"][sensor]["type"] == "ZLLSwitch" or \
                        bridge_config["sensors"][sensor]["type"] == "ZGPSwitch":
                    bridge_config["sensors"][sensor]["state"].update({
                        "buttonevent": request.params["button"][0],
                        "lastupdated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")})
                    current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                    sensors_state[sensor]["state"]["lastupdated"] = current_time
                    rules_processor(bridge_config, sensor, current_time)
                elif bridge_config["sensors"][sensor]["type"] == "ZLLPresence" and \
                        "presence" in request.params:
                    if str(bridge_config["sensors"][sensor]["state"]["presence"]).lower() != request.params["presence"][0]:
                        sensors_state[sensor]["state"]["presence"] = \
                            datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                    bridge_config["sensors"][sensor]["state"].update({
                        "presence": True if request.params["presence"][0] == "true" else False,
                        "lastupdated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")})
                    rules_processor(bridge_config, sensor)
                    # if alarm is activ trigger the alarm
                    if "virtual_light" in bridge_config["alarm_config"] and \
                            bridge_config["lights"][bridge_config["alarm_config"]["virtual_light"]]["state"]["on"] and \
                            bridge_config["sensors"][sensor]["state"]["presence"]:
                        send_email(bridge_config["sensors"][sensor]["name"])
                        # triger_horn() need development
                elif bridge_config["sensors"][sensor]["type"] == "ZLLLightLevel" and "lightlevel" in request.params:
                    if str(bridge_config["sensors"][sensor]["state"]["dark"]).lower() != request.params["dark"][0]:
                        sensors_state[sensor]["state"]["dark"] = \
                            datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                    bridge_config["sensors"][sensor]["state"].update({
                        "lightlevel": int(request.params["lightlevel"][0]),
                        "dark": True if request.params["dark"][0] == "true" else False,
                        "daylight": True if request.params["daylight"][0] == "true" else False,
                        "lastupdated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")})
                    # Process the rules to perform the action configured by application
                    rules_processor(bridge_config, sensor)

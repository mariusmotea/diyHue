from datetime import datetime
from uuid import getnode as get_mac
import hashlib
import random
import json

import requests
import hug
from falcon import HTTP_404
from jinja2 import FileSystemLoader, Environment

from huebridgeemulator.tools import generateSensorsState
from huebridgeemulator.web.templates import get_template, get_static
from huebridgeemulator.http.websocket import scanDeconz


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
def root(request, response, filename="index", ext="html"):
    if request.path == "/":
        return hug.redirect.to('index.html')
    try:
        response.set_header('Content-type', MIMETYPES.get(ext, "text/html"))
        return get_static(request.path)
    except FileNotFoundError:
        response.status = HTTP_404
        return

@hug.get('/config.js',  output=hug.output_format.html)
def configjs(request, response):
    registry = request.context['registry']
    if len(registry.config["whitelist"]) == 0:
        key = "web-ui-" + str(random.randrange(0, 99999))
        registry.config["whitelist"][key] = {
            "create date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "last use date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "name": "WegGui User"}
    response.set_header('Content-type', 'text/javascript')
    return 'window.config = { API_KEY: "' + list(registry.config["whitelist"])[0] + '",};'


@hug.get('/debug/clip.html', output=hug.output_format.html)
def debug_clip(request, response):
    """????

    .. todo:: Missing template file content
    """
    template = get_template('clip.html.j2')
    return template.render({})

@hug.get('/save')
def save(request, response):
    request.context['conf_obj'].save()
    return "config saved"


authentication = hug.authentication.basic(hug.authentication.verify('Hue', 'Hue'))
@hug.get('/hue/linkbutton', requires=authentication, output=hug.output_format.html)
def linkbutton(request, response):
    # TODO Change user/password
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
        tmp_password = str(base64.b64encode(bytes(request.params["username"][0] + ":" + request.params["password"][0], "utf8"))).split('\'')
        registry.linkbutton.linkbutton_auth = tmp_password[1]
        registry.save()
        return template.render({"message": "Your credentials are succesfully change. Please logout then login again"})
    else:
        return template.render({})

@hug.get('/hue', output=hug.output_format.html)
def linkbutton(request, response):
    registry = request.context['registry']
    template = get_template('webform_hue.html.j2')
    if request.params.get('ip'):
        url = "http://" + request.params.get('ip') + "/api/"
        data = json.dumps({"devicetype": "Hue Emulator"})
        query = requests.post(url, data=data)
        response = query.json()
        if "success" in response[0]:
            url = "http://" +request.params.get('ip') + "/api/" + response[0]["success"]["username"] + "/lights"
            query = requests.get(url)
            hue_lights =  query.json()
#            hue_lights = json.loads(sendRequest("http://" + request.params["ip"][0] + "/api/" + response[0]["success"]["username"] + "/lights", "GET", "{}"))
            lights_found = 0
            for hue_light in hue_lights:
                # TODO
                import ipdb;ipdb.set_trace()
                hue_light['address'] =  {"username": response[0]["success"]["username"],
                                         "light_id": hue_light,
                                         "ip": request.params.get('ip'),
                                         "protocol": "hue"}
                new_light = HueLight(hue_light)
                registry.lights["lights"][new_light.index] = new_light
                bridge_config["lights_address"][new_light_id] = {"username": response[0]["success"]["username"], "light_id": hue_light, "ip": request.params.get('ip'), "protocol": "hue"}
                lights_found += 1
            if lights_found == 0:
                return template.render({"message": "No lights where found"})
            else:
                return template.render({"message": "{} lights where found".format(lights_found)})
        else:
            return template.render({"message": "unable to connect to hue bridge"})
    else:
        return template.render({})

@hug.get('/tradfri')
def tradfri(request, response):
    return {}

@hug.get('/milight')
def tradfri(request, response):
    return {}

@hug.get('/deconz')
def deconz(request, response):
    # NEED test
    template = get_template('webform_deconz.html.j2')
    bridge_config = request.context['conf_obj'].bridge
    #clean all rules related to deconz Switches
    # TODO improve this if condition
    if request.params:
        emulator_resourcelinkes = []
        for resourcelink in bridge_config["resourcelinks"].keys(): # delete all previews rules of IKEA remotes
            if bridge_config["resourcelinks"][resourcelink]["classid"] == 15555:
                emulator_resourcelinkes.append(resourcelink)
                for link in bridge_config["resourcelinks"][resourcelink]["links"]:
                    pices = link.split('/')
                    if pices[1] == "rules":
                        try:
                            del bridge_config["rules"][pices[2]]
                        except:
                            print("unable to delete the rule " + pices[2])
        for resourcelink in emulator_resourcelinkes:
            del bridge_config["resourcelinks"][resourcelink]
        for key in request.params.keys():
            if request.params[key][0] in ["ZLLSwitch", "ZGPSwitch"]:
                try:
                    del bridge_config["sensors"][key]
                except:
                    pass
                hueSwitchId = addHueSwitch("", request.params[key][0])
                for sensor in bridge_config["deconz"]["sensors"].keys():
                    if bridge_config["deconz"]["sensors"][sensor]["bridgeid"] == key:
                        bridge_config["deconz"]["sensors"][sensor] = {"hueType": request.params[key][0], "bridgeid": hueSwitchId}
            else:
                if not key.startswith("mode_"):
                    if bridge_config["sensors"][key]["modelid"] == "TRADFRI remote control":
                        if request.params["mode_" + key][0]  == "CT":
                            addTradfriCtRemote(key, request.params[key][0])
                        elif request.params["mode_" + key][0]  == "SCENE":
                            addTradfriSceneRemote(key, request.params[key][0])
                    elif bridge_config["sensors"][key]["modelid"] == "TRADFRI wireless dimmer":
                        addTradfriDimmer(key, request.params[key][0])
                    #store room id in deconz sensors
                    for sensor in bridge_config["deconz"]["sensors"].keys():
                        if bridge_config["deconz"]["sensors"][sensor]["bridgeid"] == key:
                            bridge_config["deconz"]["sensors"][sensor]["room"] = request.params[key][0]
                            if bridge_config["sensors"][key]["modelid"] == "TRADFRI remote control":
                                bridge_config["deconz"]["sensors"][sensor]["opmode"] = request.params["mode_" + key][0]
        else:
            # TODO ADD Comments
            scanDeconz()
        return template.render({"deconz": bridge_config["deconz"],
                                "sensors": bridge_config["sensors"],
                                "groups": bridge_config["groups"]})


@hug.get('/switch')
def switch(request, response):  # request from an ESP8266 switch or sensor
    # NEED test
    bridge_config = request.context['conf_obj'].bridge
    if "devicetype" in request.params:  # register device request
        sensor_is_new = True
        for sensor in bridge_config["sensors"]:
            if bridge_config["sensors"][sensor]["uniqueid"].startswith(request.params["mac"][0]): # if sensor is already present
                sensor_is_new = False
        if sensor_is_new:
            print("registering new sensor " + request.params["devicetype"][0])
            new_sensor_id = self._nextFreeId("sensors")
            if request.params["devicetype"][0] in ["ZLLSwitch","ZGPSwitch"]:
                print(request.params["devicetype"][0])
                addHueSwitch(request.params["mac"][0], request.params["devicetype"][0])
            elif request.params["devicetype"][0] == "ZLLPresence":
                print("ZLLPresence")
                addHueMotionSensor(request.params["mac"][0])
            generateSensorsState(bridge_config, request.context['sensors_state'])
    else:  # switch action request
        for sensor in bridge_config["sensors"]:
            if bridge_config["sensors"][sensor]["uniqueid"].startswith(request.params["mac"][0]) and bridge_config["sensors"][sensor]["config"]["on"]: #match senser id based on mac address
                print("match sensor " + str(sensor))
                if bridge_config["sensors"][sensor]["type"] == "ZLLSwitch" or bridge_config["sensors"][sensor]["type"] == "ZGPSwitch":
                    bridge_config["sensors"][sensor]["state"].update({"buttonevent": request.params["button"][0], "lastupdated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")})
                    current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                    sensors_state[sensor]["state"]["lastupdated"] = current_time
                    rulesProcessor(bridge_config, sensor, current_time)
                elif bridge_config["sensors"][sensor]["type"] == "ZLLPresence" and "presence" in request.params:
                    if str(bridge_config["sensors"][sensor]["state"]["presence"]).lower() != request.params["presence"][0]:
                        sensors_state[sensor]["state"]["presence"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                    bridge_config["sensors"][sensor]["state"].update({"presence": True if request.params["presence"][0] == "true" else False, "lastupdated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")})
                    rulesProcessor(bridge_config, sensor)
                    #if alarm is activ trigger the alarm
                    if "virtual_light" in bridge_config["alarm_config"] and bridge_config["lights"][bridge_config["alarm_config"]["virtual_light"]]["state"]["on"] and bridge_config["sensors"][sensor]["state"]["presence"] == True:
                        sendEmail(bridge_config["sensors"][sensor]["name"])
                        #triger_horn() need development
                elif bridge_config["sensors"][sensor]["type"] == "ZLLLightLevel" and "lightlevel" in request.params:
                    if str(bridge_config["sensors"][sensor]["state"]["dark"]).lower() != request.params["dark"][0]:
                        sensors_state[sensor]["state"]["dark"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                    bridge_config["sensors"][sensor]["state"].update({"lightlevel":int(request.params["lightlevel"][0]), "dark":True if request.params["dark"][0] == "true" else False, "daylight":True if request.params["daylight"][0] == "true" else False, "lastupdated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")})
                    rulesProcessor(bridge_config, sensor) #process the rules to perform the action configured by application

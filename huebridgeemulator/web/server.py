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

@hug.static('/')
def root():
    return ("web-ui/", )


@hug.get('/config.js',  output=hug.output_format.html)
def configjs(request, response):
#    import ipdb;ipdb.set_trace()
    bridge_config = request.context['conf_obj'].bridge

    if len(bridge_config["config"]["whitelist"]) == 0:
        bridge_config["config"]["whitelist"]["web-ui-" + str(random.randrange(0, 99999))] = {"create date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),"last use date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),"name": "WegGui User"}
    print('window.config = { API_KEY: "' + list(bridge_config["config"]["whitelist"])[0] + '",};')
    response.set_header('Content-type', 'text/javascript')
    return 'window.config = { API_KEY: "' + list(bridge_config["config"]["whitelist"])[0] + '",};'


@hug.get('/description.xml',  output=hug.output_format.html)
def hue_description(request, response):
    bridge_config = request.context['conf_obj'].bridge
    response.set_header('Content-type', 'application/xml')
#    description(bridge_config["config"]["ipaddress"], mac)
    template = get_template('description.xml.j2')
    return template.render({'ip': bridge_config["config"]["ipaddress"],
                            'mac': request.context['mac']})

@hug.get('/save')
def save(request, response):
    request.context['conf_obj'].save()
    return "config saved"


authentication = hug.authentication.basic(hug.authentication.verify('Hue', 'Hue'))
@hug.get('/hue/linkbutton', requires=authentication, output=hug.output_format.html)
def linkbutton(request, response):
    bridge_config = request.context['conf_obj'].bridge
    template = get_template('webform_linkbutton.html.j2')
    if request.params.get('action') == "Activate":
        bridge_config["config"]["linkbutton"] = False
        bridge_config["linkbutton"]["lastlinkbuttonpushed"] = datetime.now().strftime("%s")
        request.context['conf_obj'].save()
        return template.render({"message": "You have 30 sec to connect your device"})
    elif request.params.get('action') == "Exit":
        return 'You are succesfully disconnected'
    elif request.params.get('action') == "ChangePassword":
        tmp_password = str(base64.b64encode(bytes(request.params["username"][0] + ":" + request.params["password"][0], "utf8"))).split('\'')
        bridge_config["linkbutton"]["linkbutton_auth"] = tmp_password[1]
        request.context['conf_obj'].save()
        return template.render({"message": "Your credentials are succesfully change. Please logout then login again"})
    else:
        return template.render({})

@hug.get('/hue', output=hug.output_format.html)
def linkbutton(request, response):
    bridge_config = request.context['conf_obj'].bridge
    template = get_template('webform_hue.html.j2')
    if request.params.get('ip'):
#        import ipdb;ipdb.set_trace()
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
                new_light_id = request.context['conf_obj'].nextFreeId("lights")
                bridge_config["lights"][new_light_id] = hue_lights[hue_light]
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


@hug.get('/api/{uid}/{type}')
def api_get_lights(uid, type, request, response):
    """Print entire config."""
    bridge_config = request.context['conf_obj'].bridge
    if uid in bridge_config["config"]["whitelist"]:
        bridge_config["config"]["UTC"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
        bridge_config["config"]["localtime"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        bridge_config["config"]["whitelist"][uid]["last use date"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        return {"lights": bridge_config["lights"],
                "groups": bridge_config["groups"],
                "config": bridge_config["config"],
                "scenes": bridge_config["scenes"],
                "schedules": bridge_config["schedules"],
                "rules": bridge_config["rules"],
                "sensors": bridge_config["sensors"],
                "resourcelinks": bridge_config["resourcelinks"]}


@hug.get('/api/{uid}/{type}/{light_id}')
def api_get_light(uid, type, light_id, request, response):
    """print specified object config."""
    bridge_config = request.context['conf_obj'].bridge
    if uid in bridge_config["config"]["whitelist"]:
        if type == "lights":
            request.context['conf_obj'].get_json_lights()
        else:
            return bridge_config[type]


@hug.get('/api/{uid}/{type}/new')
def api_new_light(uid, type, request, response):
    """return new lights and sensors only."""
    bridge_config = request.context['conf_obj'].bridge
    if uid in bridge_config["config"]["whitelist"]:
        print(request.context['conf_obj'].get_new_lights())
        response = request.context['conf_obj'].get_new_lights()
        request.context['conf_obj'].clear_new_lights()
        return response

@hug.get('/api/{uid}/groups')
def api_get_groups(uid, request, response):
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

@hug.get('/api/{uid}/info/{info}')
def api_get_groups(uid, info, request, response):
    bridge_config = request.context['conf_obj'].bridge
    if uid in bridge_config["config"]["whitelist"]:
        return ridge_config["capabilities"][info]


# TODO
# if url_pices[2] in bridge_config["config"]["whitelist"]:
#        elif len(url_pices) == 6 or (len(url_pices) == 7 and url_pices[6] == ""):
#            self.wfile.write(bytes(json.dumps(bridge_config[type][url_pices[4]][url_pices[5]]), "utf8"))

@hug.get('/api/node')
@hug.get('/api/config')
@hug.get('/api/nouser')
def api_get_discover(request, response):
    """used by applications to discover the bridge."""
    bridge_config = request.context['conf_obj'].bridge
    return {"name": bridge_config["config"]["name"],
            "datastoreversion": 59,
            "swversion": bridge_config["config"]["swversion"],
            "apiversion": bridge_config["config"]["apiversion"],
            "mac": bridge_config["config"]["mac"],
            "bridgeid": bridge_config["config"]["bridgeid"],
            "factorynew": False,
            "modelid": bridge_config["config"]["modelid"]}



@hug.post('/updater')
def updater(request, response):
    # TODO
    return {}


#@hug.post('/api/{uid}/sensors')
@hug.post('/api/{uid}/{type}')
def api_lights(uid, type, body, request, response):
    bridge_config = request.context['conf_obj'].bridge
    if uid in bridge_config["config"]["whitelist"]:
        if type == "lights" or type == "sensor" and not bool(body):
            Thread(target=scanForLights,
                   args=[request.context['conf_obj'],
                         request.context['new_lights']]).start()
            # TODO wait this thread but add a timeout
            time.sleep(7)
            return [{"success": {"/" + uid: "Searching for new devices"}}]
        elif type == "":
            # WHY ???
            return [{"success": {"clientkey": "E3B550C65F78022EFD9E52E28378583"}}]
        else: #create object
            post_dictionary = body
            # find the first unused id for new object
            new_object_id = request.context['conf_obj'].nextFreeId(type)
            if type == "scenes":
                post_dictionary.update({"lightstates": {}, "version": 2, "picture": "", "lastupdated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"), "owner" :uid})
                if "locked" not in post_dictionary:
                    post_dictionary["locked"] = False
            elif type == "groups":
                post_dictionary.update({"action": {"on": False}, "state": {"any_on": False, "all_on": False}})
            elif type == "schedules":
                post_dictionary.update({"created": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"), "time": post_dictionary["localtime"]})
                if post_dictionary["localtime"].startswith("PT"):
                    post_dictionary.update({"starttime": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")})
                if not "status" in post_dictionary:
                    post_dictionary.update({"status": "enabled"})
            elif type == "rules":
                post_dictionary.update({"owner": uid, "lasttriggered" : "none", "creationtime": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"), "timestriggered": 0})
                if not "status" in post_dictionary:
                    post_dictionary.update({"status": "enabled"})
            elif type == "sensors":
                if "state" not in post_dictionary:
                    post_dictionary["state"] = {}
                if post_dictionary["modelid"] == "PHWA01":
                    post_dictionary.update({"state": {"status": 0}})
            elif type == "resourcelinks":
                post_dictionary.update({"owner" :uid})
            generateSensorsState(bridge_config, self.server.context['sensors_state'])
            bridge_config[type][new_object_id] = post_dictionary
            print(json.dumps([{"success": {"id": new_object_id}}], sort_keys=True, indent=4, separators=(',', ': ')))
            return [{"success": {"id": new_object_id}}]
    else:
        return [{"error": {"type": 1, "address": request.path, "description": "unauthorized user" }}]
        print(json.dumps([{"error": {"type": 1, "address": request.path, "description": "unauthorized user" }}],sort_keys=True, indent=4, separators=(',', ': ')))
    
@hug.post('/api')
def api_registration(body, request, response):
    bridge_config = request.context['conf_obj'].bridge
    response = []
    # new registration by linkbutton
    post_dictionary = body
    if "devicetype" in post_dictionary and not bridge_config["config"]["linkbutton"]:
        if int(bridge_config["linkbutton"]["lastlinkbuttonpushed"]) + 30 >= int(datetime.now().strftime("%s")):
            username = hashlib.new('ripemd160', post_dictionary["devicetype"][0].encode('utf-8')).hexdigest()[:32]
            bridge_config["config"]["whitelist"][username] = {"last use date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
                                                              "create date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
                                                              "name": post_dictionary["devicetype"]}
            response = [{"success": {"username": username}}]
            if "generateclientkey" in post_dictionary and post_dictionary["generateclientkey"]:
                response[0]["success"]["clientkey"] = "E3B550C65F78022EFD9E52E28378583"
            print(json.dumps(response, sort_keys=True, indent=4, separators=(',', ': ')))
        else:
            response = [{"error": {"type": 101, "address": request.path, "description": "link button not pressed" }}]

    bridge_config["config"].save()
    return response

#@hug.get('/api/{uid}/groups')
#def api_lights(request, response):
#    print("/api/{uid}/groups")
#    return {}




def rulesProcessor(bridge_config, sensor, current_time=datetime.now().strftime("%Y-%m-%dT%H:%M:%S")):
    bridge_config["config"]["localtime"] = current_time #required for operator dx to address /config/localtime
    actionsToExecute = []
    for rule in bridge_config["rules"].keys():
        if bridge_config["rules"][rule]["status"] == "enabled":
            rule_result = checkRuleConditions(rule, sensor, current_time)
            if rule_result[0]:
                if rule_result[1] == 0: #is not ddx rule
                    print("rule " + rule + " is triggered")
                    bridge_config["rules"][rule]["lasttriggered"] = current_time
                    bridge_config["rules"][rule]["timestriggered"] += 1
                    for action in bridge_config["rules"][rule]["actions"]:
                        actionsToExecute.append(action)
                else: #if ddx rule
                    print("ddx rule " + rule + " will be re validated after " + str(rule_result[1]) + " seconds")
                    Thread(target=ddxRecheck, args=[rule, sensor, current_time, rule_result[1], rule_result[2]]).start()
    for action in actionsToExecute:
        sendRequest("/api/" +    list(bridge_config["config"]["whitelist"])[0] + action["address"], action["method"], json.dumps(action["body"]))





def start(conf_obj, sensors_state):

    @hug.request_middleware()
    def create_context(request, response):
        request.context['conf_obj'] = conf_obj
        request.context['mac'] = '%012x' % get_mac()
        request.context['sensors_state'] = sensors_state

    # TODO add port
    api = hug.API(__name__)
    host = ''
    port = 80
    api.http.serve(host=host, port=port)

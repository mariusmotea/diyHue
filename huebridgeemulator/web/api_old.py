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



@hug.get('/description.xml',  output=hug.output_format.html)
def hue_description(request, response):
    print("/description.xml/description.xml/description.xml/description.xml/description.xml/description.xml")
    bridge_config = request.context['conf_obj'].bridge
    response.set_header('Content-type', 'application/xml')
#    description(bridge_config["config"]["ipaddress"], mac)
    template = get_template('description.xml.j2')
    return template.render({'ip': bridge_config["config"]["ipaddress"],
                            'mac': request.context['mac']})


@hug.get('/api/{uid}')
@hug.get('/api/{uid}/')
def api_get_config(uid, request, response):
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

    else:
        return [{"error": {"type": 1, "address": request.path, "description": "unauthorized user" }}]


@hug.get('/api/{uid}/{resource_type}/{resource_id}')
def api_get_light(uid, resource_type, resource_id, request, response):
    """print specified object config."""
    print("api_get_lightapi_get_lightapi_get_lightapi_get_light")
    bridge_config = request.context['conf_obj'].bridge
    if uid in bridge_config["config"]["whitelist"]:
        if resource_type == "lights":
            request.context['conf_obj'].get_json_lights()
        else:
            return bridge_config[resource_type]


@hug.get('/api/{uid}/{resource_type}/new')
def api_new_light(uid, resource_type, request, response):
    """return new lights and sensors only."""
    print("api_new_lightapi_new_lightapi_new_lightapi_new_lightapi_new_lightapi_new_light")
    bridge_config = request.context['conf_obj'].bridge
    if uid in bridge_config["config"]["whitelist"]:
        print(request.context['conf_obj'].get_new_lights())
        response = request.context['conf_obj'].get_new_lights()
        request.context['conf_obj'].clear_new_lights()
        return response


@hug.get('/api/{uid}/{resource_type}')
def api_get_lights(uid, resource_type, request, response):
    print("api_get_lightsapi_get_lightsapi_get_lightsapi_get_lightsapi_get_lights")
    if type == 'lights':
        return request.context['conf_obj'].get_json_lights()
    else:
        bridge_config = request.context['conf_obj'].bridge
        return bridge_config[resource_type]

@hug.get('/api/{uid}/groups/0')
def api_get_groups(uid, request, response):
    print("api_get_groupsapi_get_groupsapi_get_groupsapi_get_groupsapi_get_groupsapi_get_groups")
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
    print("api_get_groupsapi_get_groupsapi_get_groupsapi_get_groupsapi_get_groupsapi_get_groups")
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
@hug.get('/api/nouser/config')
def api_get_discover(request, response):
    """used by applications to discover the bridge."""
    print("api_get_discoverapi_get_discoverapi_get_discoverapi_get_discoverapi_get_discover")
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


@hug.post('/api/{uid}/{resource_type}')
def api_lights(uid, resource_type, body, request, response):
    bridge_config = request.context['conf_obj'].bridge
    if uid in bridge_config["config"]["whitelist"]:
        if resource_type == "lights" or resource_type == "sensor" and not bool(body):
            Thread(target=scanForLights,
                   args=[request.context['conf_obj'],
                         request.context['new_lights']]).start()
            # TODO wait this thread but add a timeout
            time.sleep(7)
            return [{"success": {"/" + uid: "Searching for new devices"}}]
        elif resource_type == "":
            # WHY ???
            return [{"success": {"clientkey": "E3B550C65F78022EFD9E52E28378583"}}]
        else: #create object
            post_dictionary = body
            print("create objectcreate objectcreate objectcreate objectcreate object")
            print(request.path)
            print(resource_type)
            # find the first unused id for new object
            new_object_id = request.context['conf_obj'].nextFreeId(resource_type)
            if resource_type == "scenes":
                post_dictionary.update({"lightstates": {}, "version": 2, "picture": "", "lastupdated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"), "owner" :uid})
                if "locked" not in post_dictionary:
                    post_dictionary["locked"] = False
            elif resource_type == "groups":
                post_dictionary.update({"action": {"on": False}, "state": {"any_on": False, "all_on": False}})
            elif resource_type == "schedules":
                post_dictionary.update({"created": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"), "time": post_dictionary["localtime"]})
                if post_dictionary["localtime"].startswith("PT"):
                    post_dictionary.update({"starttime": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")})
                if not "status" in post_dictionary:
                    post_dictionary.update({"status": "enabled"})
            elif resource_type == "rules":
                post_dictionary.update({"owner": uid, "lasttriggered" : "none", "creationtime": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"), "timestriggered": 0})
                if not "status" in post_dictionary:
                    post_dictionary.update({"status": "enabled"})
            elif resource_type == "sensors":
                if "state" not in post_dictionary:
                    post_dictionary["state"] = {}
                if post_dictionary["modelid"] == "PHWA01":
                    post_dictionary.update({"state": {"status": 0}})
            elif resource_type == "resourcelinks":
                post_dictionary.update({"owner" :uid})
            generateSensorsState(bridge_config, request.context['sensors_state'])
            bridge_config[resource_type][new_object_id] = post_dictionary
            request.context['conf_obj'].save()
            print(json.dumps([{"success": {"id": new_object_id}}], sort_keys=True, indent=4, separators=(',', ': ')))
            return [{"success": {"id": new_object_id}}]
    else:
        return [{"error": {"type": 1, "address": request.path, "description": "unauthorized user" }}]
    
@hug.post('/api')
@hug.post('/api/')
def api_registration(body, request, response):
    print("api_registrationapi_registrationapi_registrationapi_registrationapi_registrationapi_registration")
    bridge_config = request.context['conf_obj'].bridge
    response = []
    # new registration by linkbutton
    post_dictionary = body
    print("QQQ1")
    if "devicetype" in post_dictionary:
        if bridge_config["config"]["linkbutton"]: #  this must be a new device registration
            #  create new user hash
            username = hashlib.new('ripemd160', post_dictionary["devicetype"][0].encode('utf-8')).hexdigest()[:32]
            bridge_config["config"]["whitelist"][username] = {"last use date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),"create date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),"name": post_dictionary["devicetype"]}
            response = [{"success": {"username": username}}]
            if "generateclientkey" in post_dictionary and post_dictionary["generateclientkey"]:
                response[0]["success"]["clientkey"] = "E3B550C65F78022EFD9E52E28378583"
            print(json.dumps(response, sort_keys=True, indent=4, separators=(',', ': ')))
        elif not bridge_config["config"]["linkbutton"]:
            print("QQQ2")
            if int(bridge_config["linkbutton"]["lastlinkbuttonpushed"]) + 30 >= int(datetime.now().strftime("%s")):
                print("QQQ3")
                username = hashlib.new('ripemd160', post_dictionary["devicetype"][0].encode('utf-8')).hexdigest()[:32]
                bridge_config["config"]["whitelist"][username] = {"last use date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
                                                                  "create date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
                                                                  "name": post_dictionary["devicetype"]}
                response = [{"success": {"username": username}}]
                print("generateclientkey" in post_dictionary)
                print(post_dictionary["generateclientkey"])
                if "generateclientkey" in post_dictionary and post_dictionary["generateclientkey"]:
                    response[0]["success"]["clientkey"] = "E3B550C65F78022EFD9E52E28378583"
                print(json.dumps(response, sort_keys=True, indent=4, separators=(',', ': ')))
            else:
                print("QQQ4")
                response = [{"error": {"type": 101, "address": request.path, "description": "link button not pressed" }}]

    request.context['conf_obj'].save()
    return response

#@hug.get('/api/{uid}/groups')
#def api_lights(request, response):
#    print("/api/{uid}/groups")
#    return {}



@hug.delete('/api/{uid}/{resource_type}/{resource_id}')
def delete_resource(uid, resource_type, resource_id, request, response):
    bridge_config = request.context['conf_obj'].bridge
    if uid in bridge_config["config"]["whitelist"]:
        del bridge_config[resource_type][resource_id]
        if resource_type == "lights":
            del bridge_config["lights_address"][resource_id]
            for light in list(bridge_config["deconz"]["lights"]):
                if bridge_config["deconz"]["lights"][light]["bridgeid"] == resource_id:
                    del bridge_config["deconz"]["lights"][light]
        if resource_type == "sensors":
            for sensor in list(bridge_config["deconz"]["sensors"]):
                if bridge_config["deconz"]["sensors"][sensor]["bridgeid"] == resource_id:
                    del bridge_config["deconz"]["sensors"][sensor]
        request.context['conf_obj'].save()
        return [{"success": "/" + resource_type + "/" + resource_id + " deleted."}]




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

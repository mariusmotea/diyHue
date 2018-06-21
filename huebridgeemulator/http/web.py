#!/usr/bin/python3
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from time import strftime, sleep
from datetime import datetime, timedelta
from pprint import pprint
from subprocess import check_output
import json, socket, hashlib, random, sys, ssl
import requests
import urllib.request, urllib.parse
import base64
from threading import Thread
from collections import defaultdict
from uuid import getnode as get_mac
from urllib.parse import urlparse, parse_qs
from functions import *
from uuid import getnode as get_mac


from threading import Thread
from huebridgeemulator.config import saveConfig
from huebridgeemulator.tools import generateSensorsState
from huebridgeemulator.tools.light import scanForLights, updateGroupStats, sendLightRequest
from huebridgeemulator.http.client import sendRequest


class S(BaseHTTPRequestHandler):

    def _nextFreeId(self, element):
        bridge_config = self.server.context['conf_obj'].bridge
        i = 1
        while (str(i)) in bridge_config[element]:
            i += 1
        return str(i)

    def _set_headers(self):
        self.send_response(200)
        mimetypes = {"json": "application/json", "map": "application/json", "html": "text/html", "xml": "application/xml", "js": "text/javascript", "css": "text/css", "png": "image/png"}
        if self.path.endswith((".html",".json",".css",".map",".png",".js", ".xml")):
            self.send_header('Content-type', mimetypes[self.path.split(".")[-1]])
        elif self.path.startswith("/api"):
            self.send_header('Content-type', mimetypes["json"])
        else:
            self.send_header('Content-type', mimetypes["html"])
        self.end_headers()

    def _set_AUTHHEAD(self):
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm=\"Hue\"')
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        bridge_config = self.server.context['conf_obj'].bridge
        mac = self.server.context['mac']
        if self.path == '/' or self.path == '/index.html':
            # DONE
            self._set_headers()
            f = open('./web-ui/index.html')
            self.wfile.write(bytes(f.read(), "utf8"))
        elif self.path == '/config.js':
            # DONE
            self._set_headers()
            #create a new user key in case none is available
            if len(bridge_config["config"]["whitelist"]) == 0:
                bridge_config["config"]["whitelist"]["web-ui-" + str(random.randrange(0, 99999))] = {"create date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),"last use date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),"name": "WegGui User"}
            self.wfile.write(bytes('window.config = { API_KEY: "' + list(bridge_config["config"]["whitelist"])[0] + '",};', "utf8"))
        elif self.path.endswith((".css",".map",".png",".js")):
            # DONE
            self._set_headers()
            f = open('./web-ui' + self.path, 'rb')
            self.wfile.write(f.read())
        elif self.path == '/description.xml':
            # DONE
            self._set_headers()
            self.wfile.write(bytes(description(bridge_config["config"]["ipaddress"], mac), "utf8"))
        elif self.path == '/save':
            # DONE
            saveConfig(bridge_config)
            self.wfile.write(bytes("config saved", "utf8"))
        elif self.path.startswith("/tradfri"): #setup Tradfri gateway
            # TODO
            self._set_headers()
            get_parameters = parse_qs(urlparse(self.path).query)
            if "code" in get_parameters:
                #register new identity
                new_identity = "Hue-Emulator-" + str(random.randrange(0, 999))
                registration = json.loads(check_output("./coap-client-linux -m post -u \"Client_identity\" -k \"" + get_parameters["code"][0] + "\" -e '{\"9090\":\"" + new_identity + "\"}' \"coaps://" + get_parameters["ip"][0] + ":5684/15011/9063\"", shell=True).decode('utf-8').split("\n")[3])
                bridge_config["tradfri"] = {"psk": registration["9091"], "ip": get_parameters["ip"][0], "identity": new_identity}
                lights_found = scanTradfri()
                if lights_found == 0:
                    self.wfile.write(bytes(webformTradfri() + "<br> No lights where found", "utf8"))
                else:
                    self.wfile.write(bytes(webformTradfri() + "<br> " + str(lights_found) + " lights where found", "utf8"))
            else:
                self.wfile.write(bytes(webformTradfri(), "utf8"))
        elif self.path.startswith("/milight"): #setup milight bulb
            # TODO
            self._set_headers()
            get_parameters = parse_qs(urlparse(self.path).query)
            if "device_id" in get_parameters:
                #register new mi-light
                new_light_id = self._nextFreeId("lights")
                bridge_config["lights"][new_light_id] = {"state": {"on": False, "bri": 200, "hue": 0, "sat": 0, "xy": [0.0, 0.0], "ct": 461, "alert": "none", "effect": "none", "colormode": "ct", "reachable": True}, "type": "Extended color light", "name": "MiLight " + get_parameters["mode"][0] + " " + get_parameters["device_id"][0], "uniqueid": "1a2b3c4" + str(random.randrange(0, 99)), "modelid": "LCT001", "swversion": "66009461"}
                new_lights.update({new_light_id: {"name": "MiLight " + get_parameters["mode"][0] + " " + get_parameters["device_id"][0]}})
                bridge_config["lights_address"][new_light_id] = {"device_id": get_parameters["device_id"][0], "mode": get_parameters["mode"][0], "group": int(get_parameters["group"][0]), "ip": get_parameters["ip"][0], "protocol": "milight"}
                self.wfile.write(bytes(webform_milight() + "<br> Light added", "utf8"))
            else:
                self.wfile.write(bytes(webform_milight(), "utf8"))
        elif self.path.startswith("/hue"): #setup hue bridge
            if "linkbutton" in self.path: #Hub button emulated
                # DONE
                if self.headers['Authorization'] == None:
                    self._set_AUTHHEAD()
                    self.wfile.write(bytes('You are not authenticated', "utf8"))
                    pass
                elif self.headers['Authorization'] == 'Basic ' + bridge_config["linkbutton"]["linkbutton_auth"]:
                    get_parameters = parse_qs(urlparse(self.path).query)
                    if "action=Activate" in self.path:
                        self._set_headers()
                        bridge_config["config"]["linkbutton"] = False
                        bridge_config["linkbutton"]["lastlinkbuttonpushed"] = datetime.now().strftime("%s")
                        #saveConfig(bridge_config)
                        self.server.context['conf_obj'].save()
                        self.wfile.write(bytes(webform_linkbutton() + "<br> You have 30 sec to connect your device", "utf8"))
                    elif "action=Exit" in self.path:
                        self._set_AUTHHEAD()
                        self.wfile.write(bytes('You are succesfully disconnected', "utf8"))
                    elif "action=ChangePassword" in self.path:
                        self._set_headers()
                        tmp_password = str(base64.b64encode(bytes(get_parameters["username"][0] + ":" + get_parameters["password"][0], "utf8"))).split('\'')
                        bridge_config["linkbutton"]["linkbutton_auth"] = tmp_password[1]
                        saveConfig(bridge_config)
                        self.wfile.write(bytes(webform_linkbutton() + '<br> Your credentials are succesfully change. Please logout then login again', "utf8"))
                    else:
                        self._set_headers()
                        self.wfile.write(bytes(webform_linkbutton(), "utf8"))
                    pass
                else:
                    self._set_AUTHHEAD()
                    self.wfile.write(bytes(self.headers['Authorization'], "utf8"))
                    self.wfile.write(bytes('not authenticated', "utf8"))
                    pass
            else    :
                # DONE
                self._set_headers()
                get_parameters = parse_qs(urlparse(self.path).query)
                if "ip" in get_parameters:
                    response = json.loads(sendRequest("http://" + get_parameters["ip"][0] + "/api/", "POST", "{\"devicetype\":\"Hue Emulator\"}"))
                    if "success" in response[0]:
                        hue_lights = json.loads(sendRequest("http://" + get_parameters["ip"][0] + "/api/" + response[0]["success"]["username"] + "/lights", "GET", "{}"))
                        lights_found = 0
                        for hue_light in hue_lights:
                            new_light_id = self._nextFreeId("lights")
                            bridge_config["lights"][new_light_id] = hue_lights[hue_light]
                            bridge_config["lights_address"][new_light_id] = {"username": response[0]["success"]["username"], "light_id": hue_light, "ip": get_parameters["ip"][0], "protocol": "hue"}
                            lights_found += 1
                        if lights_found == 0:
                            self.wfile.write(bytes(webform_hue() + "<br> No lights where found", "utf8"))
                        else:
                            self.wfile.write(bytes(webform_hue() + "<br> " + str(lights_found) + " lights where found", "utf8"))
                    else:
                        self.wfile.write(bytes(webform_hue() + "<br> unable to connect to hue bridge", "utf8"))
                else:
                    self.wfile.write(bytes(webform_hue(), "utf8"))
        elif self.path.startswith("/deconz"): #setup imported deconz sensors
            # TODO
            self._set_headers()
            get_parameters = parse_qs(urlparse(self.path).query)
            #clean all rules related to deconz Switches
            if get_parameters:
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
                for key in get_parameters.keys():
                    if get_parameters[key][0] in ["ZLLSwitch", "ZGPSwitch"]:
                        try:
                            del bridge_config["sensors"][key]
                        except:
                            pass
                        hueSwitchId = addHueSwitch("", get_parameters[key][0])
                        for sensor in bridge_config["deconz"]["sensors"].keys():
                            if bridge_config["deconz"]["sensors"][sensor]["bridgeid"] == key:
                                bridge_config["deconz"]["sensors"][sensor] = {"hueType": get_parameters[key][0], "bridgeid": hueSwitchId}
                    else:
                        if not key.startswith("mode_"):
                            if bridge_config["sensors"][key]["modelid"] == "TRADFRI remote control":
                                if get_parameters["mode_" + key][0]  == "CT":
                                    addTradfriCtRemote(key, get_parameters[key][0])
                                elif get_parameters["mode_" + key][0]  == "SCENE":
                                    addTradfriSceneRemote(key, get_parameters[key][0])
                            elif bridge_config["sensors"][key]["modelid"] == "TRADFRI wireless dimmer":
                                addTradfriDimmer(key, get_parameters[key][0])
                            #store room id in deconz sensors
                            for sensor in bridge_config["deconz"]["sensors"].keys():
                                if bridge_config["deconz"]["sensors"][sensor]["bridgeid"] == key:
                                    bridge_config["deconz"]["sensors"][sensor]["room"] = get_parameters[key][0]
                                    if bridge_config["sensors"][key]["modelid"] == "TRADFRI remote control":
                                        bridge_config["deconz"]["sensors"][sensor]["opmode"] = get_parameters["mode_" + key][0]

            else:
                scanDeconz()
            self.wfile.write(bytes(webformDeconz({"deconz": bridge_config["deconz"], "sensors": bridge_config["sensors"], "groups": bridge_config["groups"]}), "utf8"))
        elif self.path.startswith("/switch"): #request from an ESP8266 switch or sensor
            # TODO
            self._set_headers()
            get_parameters = parse_qs(urlparse(self.path).query)
            pprint(get_parameters)
            if "devicetype" in get_parameters: #register device request
                sensor_is_new = True
                for sensor in bridge_config["sensors"]:
                    if bridge_config["sensors"][sensor]["uniqueid"].startswith(get_parameters["mac"][0]): # if sensor is already present
                        sensor_is_new = False
                if sensor_is_new:
                    print("registering new sensor " + get_parameters["devicetype"][0])
                    new_sensor_id = self._nextFreeId("sensors")
                    if get_parameters["devicetype"][0] in ["ZLLSwitch","ZGPSwitch"]:
                        print(get_parameters["devicetype"][0])
                        addHueSwitch(get_parameters["mac"][0], get_parameters["devicetype"][0])
                    elif get_parameters["devicetype"][0] == "ZLLPresence":
                        print("ZLLPresence")
                        addHueMotionSensor(get_parameters["mac"][0])
                    generateSensorsState(bridge_config, self.server.context['sensors_state'])
            else: #switch action request
                for sensor in bridge_config["sensors"]:
                    if bridge_config["sensors"][sensor]["uniqueid"].startswith(get_parameters["mac"][0]) and bridge_config["sensors"][sensor]["config"]["on"]: #match senser id based on mac address
                        print("match sensor " + str(sensor))
                        if bridge_config["sensors"][sensor]["type"] == "ZLLSwitch" or bridge_config["sensors"][sensor]["type"] == "ZGPSwitch":
                            bridge_config["sensors"][sensor]["state"].update({"buttonevent": get_parameters["button"][0], "lastupdated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")})
                            current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                            sensors_state[sensor]["state"]["lastupdated"] = current_time
                            rulesProcessor(sensor, current_time)
                        elif bridge_config["sensors"][sensor]["type"] == "ZLLPresence" and "presence" in get_parameters:
                            if str(bridge_config["sensors"][sensor]["state"]["presence"]).lower() != get_parameters["presence"][0]:
                                sensors_state[sensor]["state"]["presence"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                            bridge_config["sensors"][sensor]["state"].update({"presence": True if get_parameters["presence"][0] == "true" else False, "lastupdated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")})
                            rulesProcessor(sensor)
                            #if alarm is activ trigger the alarm
                            if "virtual_light" in bridge_config["alarm_config"] and bridge_config["lights"][bridge_config["alarm_config"]["virtual_light"]]["state"]["on"] and bridge_config["sensors"][sensor]["state"]["presence"] == True:
                                sendEmail(bridge_config["sensors"][sensor]["name"])
                                #triger_horn() need development
                        elif bridge_config["sensors"][sensor]["type"] == "ZLLLightLevel" and "lightlevel" in get_parameters:
                            if str(bridge_config["sensors"][sensor]["state"]["dark"]).lower() != get_parameters["dark"][0]:
                                sensors_state[sensor]["state"]["dark"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                            bridge_config["sensors"][sensor]["state"].update({"lightlevel":int(get_parameters["lightlevel"][0]), "dark":True if get_parameters["dark"][0] == "true" else False, "daylight":True if get_parameters["daylight"][0] == "true" else False, "lastupdated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")})
                            rulesProcessor(sensor) #process the rules to perform the action configured by application
        else:
            url_pices = self.path.split('/')
            if len(url_pices) < 3:
                #self._set_headers_error()
                self.send_error(404, 'not found')
                return
            else:
                self._set_headers()
            if url_pices[2] in bridge_config["config"]["whitelist"]: #if username is in whitelist
                bridge_config["config"]["UTC"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
                bridge_config["config"]["localtime"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                bridge_config["config"]["whitelist"][url_pices[2]]["last use date"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                if len(url_pices) == 3 or (len(url_pices) == 4 and url_pices[3] == ""): #print entire config
                    self.wfile.write(bytes(json.dumps({"lights": bridge_config["lights"], "groups": bridge_config["groups"], "config": bridge_config["config"], "scenes": bridge_config["scenes"], "schedules": bridge_config["schedules"], "rules": bridge_config["rules"], "sensors": bridge_config["sensors"], "resourcelinks": bridge_config["resourcelinks"]}), "utf8"))
                elif len(url_pices) == 4 or (len(url_pices) == 5 and url_pices[4] == ""): #print specified object config
                    if url_pices[3] == "lights":
                        self.wfile.write(bytes(self.server.context['conf_obj'].get_json_lights(), "utf8"))
#                        self.wfile.write(bytes(json.dumps(bridge_config[url_pices[3]]), "utf8"))
                    else:
                        self.wfile.write(bytes(json.dumps(bridge_config[url_pices[3]]), "utf8"))
                elif len(url_pices) == 5 or (len(url_pices) == 6 and url_pices[5] == ""):
                    if url_pices[4] == "new": #return new lights and sensors only
#                        self.server.context['new_lights'].update({"lastscan": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")})
                        print(self.server.context['conf_obj'].get_new_lights())
                        self.wfile.write(bytes(json.dumps(self.server.context['conf_obj'].get_new_lights()), "utf8"))
                        #self.wfile.write(bytes(json.dumps(self.server.context['new_lights']), "utf8"))
                        self.server.context['conf_obj'].clear_new_lights()
                    elif url_pices[3] == "groups" and url_pices[4] == "0":
                        any_on = False
                        all_on = True
                        for group_state in bridge_config["groups"].keys():
                            if bridge_config["groups"][group_state]["state"]["any_on"] == True:
                                any_on = True
                            else:
                                all_on = False
                        self.wfile.write(bytes(json.dumps({"name":"Group 0","lights": [l for l in bridge_config["lights"]],"type":"LightGroup","state":{"all_on":all_on,"any_on":any_on},"recycle":False,"action":{"on":True,"bri":254,"hue":47258,"sat":253,"effect":"none","xy":[0.1424,0.0824],"ct":153,"alert":"none","colormode":"xy"}}), "utf8"))
                    elif url_pices[3] == "info":
                        self.wfile.write(bytes(json.dumps(bridge_config["capabilities"][url_pices[4]]), "utf8"))
                    else:
                        self.wfile.write(bytes(self.server.context['conf_obj'].get_light(url_pices[4]).toJSON(), "utf8"))
#                        self.wfile.write(bytes(json.dumps(bridge_config[url_pices[3]][url_pices[4]]), "utf8"))
                elif len(url_pices) == 6 or (len(url_pices) == 7 and url_pices[6] == ""):
                    self.wfile.write(bytes(json.dumps(bridge_config[url_pices[3]][url_pices[4]][url_pices[5]]), "utf8"))
            elif (url_pices[2] == "nouser" or url_pices[2] == "none" or url_pices[2] == "config"): #used by applications to discover the bridge
                self.wfile.write(bytes(json.dumps({"name": bridge_config["config"]["name"],"datastoreversion": 59, "swversion": bridge_config["config"]["swversion"], "apiversion": bridge_config["config"]["apiversion"], "mac": bridge_config["config"]["mac"], "bridgeid": bridge_config["config"]["bridgeid"], "factorynew": False, "modelid": bridge_config["config"]["modelid"]}), "utf8"))
            else: #user is not in whitelist
                self.wfile.write(bytes(json.dumps([{"error": {"type": 1, "address": self.path, "description": "unauthorized user" }}]), "utf8"))


    def do_POST(self):
        bridge_config = self.server.context['conf_obj'].bridge
        self._set_headers()
        print ("in post method")
        print(self.path)
        self.data_string = b"{}" if self.headers['Content-Length'] is None else self.rfile.read(int(self.headers['Content-Length']))
        if self.path == "/updater":
            print("check for updates")
            update_data = json.loads(sendRequest("http://raw.githubusercontent.com/mariusmotea/diyHue/master/BridgeEmulator/updater", "GET", "{}"))
            for category in update_data.keys():
                for key in update_data[category].keys():
                    print("patch " + category + " -> " + key )
                    bridge_config[category][key] = update_data[category][key]
            self.wfile.write(bytes(json.dumps([{"success": {"/config/swupdate/checkforupdate": True}}]), "utf8"))
        else:
            post_dictionary = json.loads(self.data_string.decode('utf8'))
            print(self.data_string)
        url_pices = self.path.split('/')
        if len(url_pices) == 4: #data was posted to a location
            print("U"*789)
            print(url_pices)
            if url_pices[2] in bridge_config["config"]["whitelist"]:
                if ((url_pices[3] == "lights" or url_pices[3] == "sensors") and not bool(post_dictionary)):
                    # DONE
                    #if was a request to scan for lights of sensors
                    Thread(target=scanForLights, args=[self.server.context['conf_obj'], self.server.context['new_lights']]).start()
                    # TODO wait this thread but add a timeout
                    sleep(7) #give no more than 5 seconds for light scanning (otherwise will face app disconnection timeout)
                    self.wfile.write(bytes(json.dumps([{"success": {"/" + url_pices[3]: "Searching for new devices"}}]), "utf8"))
                elif url_pices[3] == "":
                    self.wfile.write(bytes(json.dumps([{"success": {"clientkey": "E3B550C65F78022EFD9E52E28378583"}}]), "utf8"))
                else: #create object
                    # find the first unused id for new object
                    new_object_id = self._nextFreeId(url_pices[3])
                    if url_pices[3] == "scenes":
                        post_dictionary.update({"lightstates": {}, "version": 2, "picture": "", "lastupdated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"), "owner" :url_pices[2]})
                        if "locked" not in post_dictionary:
                            post_dictionary["locked"] = False
                    elif url_pices[3] == "groups":
                        post_dictionary.update({"action": {"on": False}, "state": {"any_on": False, "all_on": False}})
                    elif url_pices[3] == "schedules":
                        post_dictionary.update({"created": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"), "time": post_dictionary["localtime"]})
                        if post_dictionary["localtime"].startswith("PT"):
                            post_dictionary.update({"starttime": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")})
                        if not "status" in post_dictionary:
                            post_dictionary.update({"status": "enabled"})
                    elif url_pices[3] == "rules":
                        post_dictionary.update({"owner": url_pices[2], "lasttriggered" : "none", "creationtime": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"), "timestriggered": 0})
                        if not "status" in post_dictionary:
                            post_dictionary.update({"status": "enabled"})
                    elif url_pices[3] == "sensors":
                        if "state" not in post_dictionary:
                            post_dictionary["state"] = {}
                        if post_dictionary["modelid"] == "PHWA01":
                            post_dictionary.update({"state": {"status": 0}})
                    elif url_pices[3] == "resourcelinks":
                        post_dictionary.update({"owner" :url_pices[2]})
                    generateSensorsState(bridge_config, self.server.context['sensors_state'])
                    bridge_config[url_pices[3]][new_object_id] = post_dictionary
                    print(json.dumps([{"success": {"id": new_object_id}}], sort_keys=True, indent=4, separators=(',', ': ')))
                    self.wfile.write(bytes(json.dumps([{"success": {"id": new_object_id}}], sort_keys=True, indent=4, separators=(',', ': ')), "utf8"))
            else:
                self.wfile.write(bytes(json.dumps([{"error": {"type": 1, "address": self.path, "description": "unauthorized user" }}],sort_keys=True, indent=4, separators=(',', ': ')), "utf8"))
                print(json.dumps([{"error": {"type": 1, "address": self.path, "description": "unauthorized user" }}],sort_keys=True, indent=4, separators=(',', ': ')))
        elif self.path.startswith("/api") and "devicetype" in post_dictionary and bridge_config["config"]["linkbutton"]: #this must be a new device registration
                #create new user hash
                username = hashlib.new('ripemd160', post_dictionary["devicetype"][0].encode('utf-8')).hexdigest()[:32]
                bridge_config["config"]["whitelist"][username] = {"last use date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),"create date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),"name": post_dictionary["devicetype"]}
                response = [{"success": {"username": username}}]
                if "generateclientkey" in post_dictionary and post_dictionary["generateclientkey"]:
                    response[0]["success"]["clientkey"] = "E3B550C65F78022EFD9E52E28378583"
                self.wfile.write(bytes(json.dumps(response), "utf8"))
                print(json.dumps(response, sort_keys=True, indent=4, separators=(',', ': ')))
        elif self.path.startswith("/api") and "devicetype" in post_dictionary and not bridge_config["config"]["linkbutton"]: #new registration by linkbutton
                if int(bridge_config["linkbutton"]["lastlinkbuttonpushed"])+30 >= int(datetime.now().strftime("%s")):
                    username = hashlib.new('ripemd160', post_dictionary["devicetype"][0].encode('utf-8')).hexdigest()[:32]
                    bridge_config["config"]["whitelist"][username] = {"last use date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),"create date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),"name": post_dictionary["devicetype"]}
                    response = [{"success": {"username": username}}]
                    if "generateclientkey" in post_dictionary and post_dictionary["generateclientkey"]:
                        response[0]["success"]["clientkey"] = "E3B550C65F78022EFD9E52E28378583"
                    self.wfile.write(bytes(json.dumps(response), "utf8"))
                    print(json.dumps(response, sort_keys=True, indent=4, separators=(',', ': ')))
                else:
                    self.wfile.write(bytes(json.dumps([{"error": {"type": 101, "address": self.path, "description": "link button not pressed" }}],sort_keys=True, indent=4, separators=(',', ': ')), "utf8"))
        self.end_headers()
#        import ipdb;ipdb.set_trace()
        self.server.context['conf_obj'].save()
        #saveConfig(bridge_config)

    def do_PUT(self):
        bridge_config = self.server.context['conf_obj'].bridge
        self._set_headers()
        print ("in PUT method")
        self.data_string = self.rfile.read(int(self.headers['Content-Length']))
        put_dictionary = json.loads(self.data_string.decode('utf8'))
        url_pices = self.path.split('/')
        print(self.path)
        print(self.data_string)
        if url_pices[2] in bridge_config["config"]["whitelist"]:
            if len(url_pices) == 4:
                bridge_config[url_pices[3]].update(put_dictionary)
                response_location = "/" + url_pices[3] + "/"
            if len(url_pices) == 5:
                if url_pices[3] == "schedules":
                    if "status" in put_dictionary and put_dictionary["status"] == "enabled" and bridge_config["schedules"][url_pices[4]]["localtime"].startswith("PT"):
                        put_dictionary.update({"starttime": (datetime.utcnow()).strftime("%Y-%m-%dT%H:%M:%S")})
                elif url_pices[3] == "scenes":
                    if "storelightstate" in put_dictionary:
                        for light in bridge_config["scenes"][url_pices[4]]["lightstates"]:
                            bridge_config["scenes"][url_pices[4]]["lightstates"][light] = {}
                            bridge_config["scenes"][url_pices[4]]["lightstates"][light]["on"] = bridge_config["lights"][light]["state"]["on"]
                            bridge_config["scenes"][url_pices[4]]["lightstates"][light]["bri"] = bridge_config["lights"][light]["state"]["bri"]
                            if bridge_config["lights"][light]["state"]["colormode"] in ["ct", "xy"]:
                                bridge_config["scenes"][url_pices[4]]["lightstates"][light][bridge_config["lights"][light]["state"]["colormode"]] = bridge_config["lights"][light]["state"][bridge_config["lights"][light]["state"]["colormode"]]
                            elif bridge_config["lights"][light]["state"]["colormode"] == "hs" and "hue" in bridge_config["scenes"][url_pices[4]]["lightstates"][light]:
                                bridge_config["scenes"][url_pices[4]]["lightstates"][light]["hue"] = bridge_config["lights"][light]["state"]["hue"]
                                bridge_config["scenes"][url_pices[4]]["lightstates"][light]["sat"] = bridge_config["lights"][light]["state"]["sat"]

                if url_pices[3] == "sensors":
                    pprint(put_dictionary)
                    for key, value in put_dictionary.items():
                        if type(value) is dict:
                            bridge_config[url_pices[3]][url_pices[4]][key].update(value)
                        else:
                            bridge_config[url_pices[3]][url_pices[4]][key] = value
                    rulesProcessor(url_pices[4])
                else:
                    bridge_config[url_pices[3]][url_pices[4]].update(put_dictionary)
                response_location = "/" + url_pices[3] + "/" + url_pices[4] + "/"
            if len(url_pices) == 6:
                if url_pices[3] == "groups": #state is applied to a group
                    if "scene" in put_dictionary: #scene applied to group
                        #send all unique ip's in thread mode for speed
                        lightsIps = []
                        processedLights = []
                        for light in bridge_config["scenes"][put_dictionary["scene"]]["lights"]:
                            bridge_config["lights"][light]["state"].update(bridge_config["scenes"][put_dictionary["scene"]]["lightstates"][light])
                            if bridge_config["lights_address"][light]["ip"] not in lightsIps:
                                lightsIps.append(bridge_config["lights_address"][light]["ip"])
                                processedLights.append(light)
                                current_light = self.server.context['conf_obj'].get_light(light)
                                if current_light.manufacturername == "yeelight":
                                    Thread(target=current_light.send_request, args=[put_dictionary]).start()
                                else:
                                    Thread(target=sendLightRequest, args=[self.server.context['conf_obj'], light, bridge_config["scenes"][put_dictionary["scene"]]["lightstates"][light]]).start()
                        sleep(0.2) #give some time for the device to process the threaded request
                        #now send the rest of the requests in non threaded mode
                        for light in bridge_config["scenes"][put_dictionary["scene"]]["lights"]:
                            if light not in processedLights:
                                current_light = self.server.context['conf_obj'].get_light(light)
                                if current_light.manufacturername == "yeelight":
                                    current_light.send_request(bridge_config["scenes"][put_dictionary["scene"]]["lightstates"][light])
                                else:
                                    sendLightRequest(self.server.context['conf_obj'], light, bridge_config["scenes"][put_dictionary["scene"]]["lightstates"][light])
                            updateGroupStats(self.server.context['conf_obj'], light)

                    elif "bri_inc" in put_dictionary:
                        bridge_config["groups"][url_pices[4]]["action"]["bri"] += int(put_dictionary["bri_inc"])
                        if bridge_config["groups"][url_pices[4]]["action"]["bri"] > 254:
                            bridge_config["groups"][url_pices[4]]["action"]["bri"] = 254
                        elif bridge_config["groups"][url_pices[4]]["action"]["bri"] < 1:
                            bridge_config["groups"][url_pices[4]]["action"]["bri"] = 1
                        bridge_config["groups"][url_pices[4]]["state"]["bri"] = bridge_config["groups"][url_pices[4]]["action"]["bri"]
                        del put_dictionary["bri_inc"]
                        put_dictionary.update({"bri": bridge_config["groups"][url_pices[4]]["action"]["bri"]})
                        for light in bridge_config["groups"][url_pices[4]]["lights"]:
                            bridge_config["lights"][light]["state"].update(put_dictionary)
                            sendLightRequest(self.server.context['conf_obj'], light, put_dictionary)
                    elif "ct_inc" in put_dictionary:
                        bridge_config["groups"][url_pices[4]]["action"]["ct"] += int(put_dictionary["ct_inc"])
                        if bridge_config["groups"][url_pices[4]]["action"]["ct"] > 500:
                            bridge_config["groups"][url_pices[4]]["action"]["ct"] = 500
                        elif bridge_config["groups"][url_pices[4]]["action"]["ct"] < 153:
                            bridge_config["groups"][url_pices[4]]["action"]["ct"] = 153
                        bridge_config["groups"][url_pices[4]]["state"]["ct"] = bridge_config["groups"][url_pices[4]]["action"]["ct"]
                        del put_dictionary["ct_inc"]
                        put_dictionary.update({"ct": bridge_config["groups"][url_pices[4]]["action"]["ct"]})
                        for light in bridge_config["groups"][url_pices[4]]["lights"]:
                            bridge_config["lights"][light]["state"].update(put_dictionary)
                            sendLightRequest(self.server.context['conf_obj'], light, put_dictionary)
                    elif "scene_inc" in put_dictionary:
                        switchScene(url_pices[4], put_dictionary["scene_inc"])
                    elif url_pices[4] == "0": #if group is 0 the scene applied to all lights
                        for light in bridge_config["lights"].keys():
                            if "virtual_light" not in bridge_config["alarm_config"] or light != bridge_config["alarm_config"]["virtual_light"]:
                                bridge_config["lights"][light]["state"].update(put_dictionary)
                                sendLightRequest(self.server.context['conf_obj'], light, put_dictionary)
                        for group in bridge_config["groups"].keys():
                            bridge_config["groups"][group][url_pices[5]].update(put_dictionary)
                            if "on" in put_dictionary:
                                bridge_config["groups"][group]["state"]["any_on"] = put_dictionary["on"]
                                bridge_config["groups"][group]["state"]["all_on"] = put_dictionary["on"]
                    else: # the state is applied to particular group (url_pices[4])
                        if "on" in put_dictionary:
                            bridge_config["groups"][url_pices[4]]["state"]["any_on"] = put_dictionary["on"]
                            bridge_config["groups"][url_pices[4]]["state"]["all_on"] = put_dictionary["on"]
                        bridge_config["groups"][url_pices[4]]["action"].update(put_dictionary)
                        #send all unique ip's in thread mode for speed
                        lightsIps = []
                        processedLights = []
                        for light in bridge_config["groups"][url_pices[4]]["lights"]:
                            bridge_config["lights"][light]["state"].update(put_dictionary)
                            if bridge_config["lights_address"][light]["ip"] not in lightsIps:
                                lightsIps.append(bridge_config["lights_address"][light]["ip"])
                                processedLights.append(light)
                                current_light = self.server.context['conf_obj'].get_light(light)
                                if current_light.manufacturername == "yeelight":
                                    Thread(target=current_light.send_request, args=[put_dictionary]).start()
                                else:
                                    Thread(target=sendLightRequest, args=[self.server.context['conf_obj'], light, put_dictionary]).start()
                        sleep(0.2) #give some time for the device to process the threaded request
                        #now send the rest of the requests in non threaded mode
                        for light in bridge_config["groups"][url_pices[4]]["lights"]:
                            if light not in processedLights:
                                sendLightRequest(self.server.context['conf_obj'], light, put_dictionary)
                elif url_pices[3] == "lights": #state is applied to a light
                    for key in put_dictionary.keys():
                        if key in ["ct", "xy"]: #colormode must be set by bridge
                            bridge_config["lights"][url_pices[4]]["state"]["colormode"] = key
                        elif key in ["hue", "sat"]:
                            bridge_config["lights"][url_pices[4]]["state"]["colormode"] = "hs"
                    updateGroupStats(self.server.context['conf_obj'], url_pices[4])
                    current_light = self.server.context['conf_obj'].get_light(url_pices[4]) 
                    if current_light.manufacturername == "yeelight":
                        current_light.send_request(put_dictionary)
                    else:
                        sendLightRequest(self.server.context['conf_obj'], url_pices[4], put_dictionary)
                if not url_pices[4] == "0": #group 0 is virtual, must not be saved in bridge configuration
                    try:
                        bridge_config[url_pices[3]][url_pices[4]][url_pices[5]].update(put_dictionary)
                    except KeyError:
                        bridge_config[url_pices[3]][url_pices[4]][url_pices[5]] = put_dictionary
                if url_pices[3] == "sensors" and url_pices[5] == "state":
                    current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                    for key in put_dictionary.keys():
                        sensors_state[url_pices[4]]["state"].update({key: current_time})
                    rulesProcessor(url_pices[4], current_time)
                response_location = "/" + url_pices[3] + "/" + url_pices[4] + "/" + url_pices[5] + "/"
            if len(url_pices) == 7:
                try:
                    bridge_config[url_pices[3]][url_pices[4]][url_pices[5]][url_pices[6]].update(put_dictionary)
                except KeyError:
                    bridge_config[url_pices[3]][url_pices[4]][url_pices[5]][url_pices[6]] = put_dictionary
                bridge_config[url_pices[3]][url_pices[4]][url_pices[5]][url_pices[6]] = put_dictionary
                response_location = "/" + url_pices[3] + "/" + url_pices[4] + "/" + url_pices[5] + "/" + url_pices[6] + "/"
            response_dictionary = []
            for key, value in put_dictionary.items():
                response_dictionary.append({"success":{response_location + key: value}})
            self.wfile.write(bytes(json.dumps(response_dictionary,sort_keys=True, indent=4, separators=(',', ': ')), "utf8"))
            print(json.dumps(response_dictionary, sort_keys=True, indent=4, separators=(',', ': ')))
        else:
            self.wfile.write(bytes(json.dumps([{"error": {"type": 1, "address": self.path, "description": "unauthorized user" }}],sort_keys=True, indent=4, separators=(',', ': ')), "utf8"))

    def do_DELETE(self):
        bridge_config = self.server.context['conf_obj'].bridge
        self._set_headers()
        url_pices = self.path.split('/')
        if url_pices[2] in bridge_config["config"]["whitelist"]:
            if len(url_pices) == 6:
                del bridge_config[url_pices[3]][url_pices[4]][url_pices[5]]
            else:
                del bridge_config[url_pices[3]][url_pices[4]]
            if url_pices[3] == "lights":
                del bridge_config["lights_address"][url_pices[4]]
                for light in list(bridge_config["deconz"]["lights"]):
                    if bridge_config["deconz"]["lights"][light]["bridgeid"] == url_pices[4]:
                        del bridge_config["deconz"]["lights"][light]
            if url_pices[3] == "sensors":
                for sensor in list(bridge_config["deconz"]["sensors"]):
                    if bridge_config["deconz"]["sensors"][sensor]["bridgeid"] == url_pices[4]:
                        del bridge_config["deconz"]["sensors"][sensor]
            self.wfile.write(bytes(json.dumps([{"success": "/" + url_pices[3] + "/" + url_pices[4] + " deleted."}]), "utf8"))

class ThreadingSimpleServer(ThreadingMixIn, HTTPServer):

    def __init__(self, server_address, handler_class, context):
        HTTPServer.__init__(self, server_address, handler_class)
        self.context = context 
        #self.context = { .... }
#    pass

def run(https, conf_obj, sensors_state, server_class=ThreadingSimpleServer, handler_class=S):
    context = {'conf_obj': conf_obj,
               'mac': '%012x' % get_mac(),
               'new_lights': {},
               'sensors_state': sensors_state,
               }
    if https:
        server_address = ('', 443)
        httpd = server_class(server_address, handler_class, context)
        httpd.socket = ssl.wrap_socket(httpd.socket, certfile='cert.pem', server_side=True, ssl_version=ssl.PROTOCOL_TLSv1_2)
        print ('Starting ssl httpd...')
    else:
        server_address = ('', 80)
        httpd = server_class(server_address, handler_class, context)
        print ('Starting httpd...')
    httpd.serve_forever()
    httpd.server_close()

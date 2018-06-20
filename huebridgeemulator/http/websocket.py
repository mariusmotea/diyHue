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

def websocketClient():
    from ws4py.client.threadedclient import WebSocketClient
    class EchoClient(WebSocketClient):
        def opened(self):
            self.send("hello")

        def closed(self, code, reason=None):
            print(("deconz websocket disconnected", code, reason))
            del bridge_config["deconz"]["websocketport"]

        def received_message(self, m):
            print(m)
            message = json.loads(str(m))
            try:
                if message["r"] == "sensors":
                    bridge_sensor_id = bridge_config["deconz"]["sensors"][message["id"]]["bridgeid"]
                    if "state" in message and bridge_config["sensors"][bridge_sensor_id]["config"]["on"]:

                        #change codes for emulated hue Switches
                        if "hueType" in bridge_config["deconz"]["sensors"][message["id"]]:
                            rewriteDict = {"ZGPSwitch": {1002: 34, 3002: 16, 4002: 17, 5002: 18}, "ZLLSwitch" : {1002 : 1000, 2002: 2000, 2001: 2001, 2003: 2002, 3001: 3001, 3002: 3000, 3003: 3002, 4002: 4000, 5002: 4000} }
                            message["state"]["buttonevent"] = rewriteDict[bridge_config["deconz"]["sensors"][message["id"]]["hueType"]][message["state"]["buttonevent"]]
                        #end change codes for emulated hue Switches

                        #convert tradfri motion sensor notification to look like Hue Motion Sensor
                        if message["state"] and bridge_config["deconz"]["sensors"][message["id"]]["modelid"] == "TRADFRI motion sensor":
                            #find the light sensor id
                            light_sensor = "0"
                            for sensor in bridge_config["sensors"].keys():
                                if bridge_config["sensors"][sensor]["type"] == "ZLLLightLevel" and bridge_config["sensors"][sensor]["uniqueid"] == bridge_config["sensors"][bridge_sensor_id]["uniqueid"][:-1] + "0":
                                    light_sensor = sensor
                                    break
                            if message["state"]["dark"]:
                                bridge_config["sensors"][light_sensor]["state"]["lightlevel"] = 6000
                            else:
                                bridge_config["sensors"][light_sensor]["state"]["lightlevel"] = 25000
                            if message["state"]["dark"] and not bridge_config["sensors"][light_sensor]["state"]["dark"]:
                                sensors_state[light_sensor]["state"]["dark"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                            bridge_config["sensors"][light_sensor]["state"]["dark"] = message["state"]["dark"]
                            bridge_config["sensors"][light_sensor]["state"]["daylight"] = not message["state"]["dark"]
                            bridge_config["sensors"][light_sensor]["state"]["lastupdated"] = message["state"]["lastupdated"]

                        #convert xiaomi motion sensor to hue sensor
                        if message["state"] and bridge_config["deconz"]["sensors"][message["id"]]["modelid"] == "lumi.sensor_motion.aq2" and message["state"] and bridge_config["deconz"]["sensors"][message["id"]]["type"] == "ZHALightLevel":
                            bridge_config["sensors"][bridge_sensor_id]["state"].update(message["state"])
                            return
                        ##############

                        bridge_config["sensors"][bridge_sensor_id]["state"].update(message["state"])
                        current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                        for key in message["state"].keys():
                            sensors_state[bridge_sensor_id]["state"][key] = current_time
                        rulesProcessor(bridge_sensor_id, current_time)
                        if "buttonevent" in message["state"] and bridge_config["sensors"][bridge_sensor_id]["modelid"] in ["TRADFRI remote control","RWL021"]:
                            if message["state"]["buttonevent"] in [2001, 3001, 4001, 5001]:
                                Thread(target=longPressButton, args=[bridge_sensor_id, message["state"]["buttonevent"]]).start()
                        if "presence" in message["state"] and message["state"]["presence"] and "virtual_light" in bridge_config["alarm_config"] and bridge_config["lights"][bridge_config["alarm_config"]["virtual_light"]]["state"]["on"]:
                            sendEmail(bridge_config["sensors"][bridge_sensor_id]["name"])
                            bridge_config["alarm_config"]["virtual_light"]
                    elif "config" in message and bridge_config["sensors"][bridge_sensor_id]["config"]["on"]:
                        bridge_config["sensors"][bridge_sensor_id]["config"].update(message["config"])
                elif message["r"] == "lights":
                    bridge_light_id = bridge_config["deconz"]["lights"][message["id"]]["bridgeid"]
                    if "state" in message:
                        bridge_config["lights"][bridge_light_id]["state"].update(message["state"])
                        updateGroupStats(bridge_light_id)
            except Exception as e:
                print("unable to process the request" + str(e))

    try:
        ws = EchoClient('ws://127.0.0.1:' + str(bridge_config["deconz"]["websocketport"]))
        ws.connect()
        ws.run_forever()
    except KeyboardInterrupt:
        ws.close()

def scanDeconz(conf_obj):
    bridge_config = conf_obj.bridge
    if not bridge_config["deconz"]["enabled"]:
        if "username" not in bridge_config["deconz"]:
            try:
                registration = json.loads(sendRequest("http://127.0.0.1:" + str(bridge_config["deconz"]["port"]) + "/api", "POST", "{\"username\": \"283145a4e198cc6535\", \"devicetype\":\"Hue Emulator\"}"))
            except:
                print("registration fail, is the link button pressed?")
                return
            if "success" in registration[0]:
                bridge_config["deconz"]["username"] = registration[0]["success"]["username"]
                bridge_config["deconz"]["enabled"] = True
    if "username" in bridge_config["deconz"]:
        deconz_config = json.loads(sendRequest("http://127.0.0.1:" + str(bridge_config["deconz"]["port"]) + "/api/" + bridge_config["deconz"]["username"] + "/config", "GET", "{}"))
        bridge_config["deconz"]["websocketport"] = deconz_config["websocketport"]

        #lights
        deconz_lights = json.loads(sendRequest("http://127.0.0.1:" + str(bridge_config["deconz"]["port"]) + "/api/" + bridge_config["deconz"]["username"] + "/lights", "GET", "{}"))
        for light in deconz_lights:
            if light not in bridge_config["deconz"]["lights"]:
                new_light_id = nextFreeId("lights")
                print("register new light " + new_light_id)
                bridge_config["lights"][new_light_id] = deconz_lights[light]
                bridge_config["lights_address"][new_light_id] = {"username": bridge_config["deconz"]["username"], "light_id": light, "ip": "127.0.0.1:" + str(bridge_config["deconz"]["port"]), "protocol": "deconz"}
                bridge_config["deconz"]["lights"][light] = {"bridgeid": new_light_id}
            else: #temporary patch for config compatibility with new release
                bridge_config["deconz"]["lights"][light]["modelid"] = deconz_lights[light]["modelid"]
                bridge_config["deconz"]["lights"][light]["type"] = deconz_lights[light]["type"]



        #sensors
        deconz_sensors = json.loads(sendRequest("http://127.0.0.1:" + str(bridge_config["deconz"]["port"]) + "/api/" + bridge_config["deconz"]["username"] + "/sensors", "GET", "{}"))
        for sensor in deconz_sensors:
            if sensor not in bridge_config["deconz"]["sensors"]:
                new_sensor_id = nextFreeId("sensors")
                if deconz_sensors[sensor]["modelid"] in ["TRADFRI remote control", "TRADFRI wireless dimmer"]:
                    print("register new " + deconz_sensors[sensor]["modelid"])
                    bridge_config["sensors"][new_sensor_id] = {"config": deconz_sensors[sensor]["config"], "manufacturername": deconz_sensors[sensor]["manufacturername"], "modelid": deconz_sensors[sensor]["modelid"], "name": deconz_sensors[sensor]["name"], "state": deconz_sensors[sensor]["state"], "swversion": deconz_sensors[sensor]["swversion"], "type": deconz_sensors[sensor]["type"], "uniqueid": deconz_sensors[sensor]["uniqueid"]}
                    bridge_config["deconz"]["sensors"][sensor] = {"bridgeid": new_sensor_id, "modelid": deconz_sensors[sensor]["modelid"]}
                elif deconz_sensors[sensor]["modelid"] == "TRADFRI motion sensor":
                    print("register TRADFRI motion sensor as Philips Motion Sensor")
                    newMotionSensorId = addHueMotionSensor("")
                    bridge_config["deconz"]["sensors"][sensor] = {"bridgeid": newMotionSensorId, "triggered": False, "modelid": deconz_sensors[sensor]["modelid"]}

                elif deconz_sensors[sensor]["modelid"] == "lumi.sensor_motion.aq2":
                    if deconz_sensors[sensor]["type"] == "ZHALightLevel":
                        print("register new Xiaomi light sensor")
                        bridge_config["sensors"][new_sensor_id] = {"name": "Hue ambient light sensor 1", "uniqueid": "00:17:88:01:02:" + deconz_sensors[sensor]["uniqueid"][12:], "type": "ZLLLightLevel", "swversion": "6.1.0.18912", "state": {"dark": True, "daylight": False, "lightlevel": 6000, "lastupdated": "none"}, "manufacturername": "Philips", "config": {"on": False,"battery": 100, "reachable": True, "alert": "none", "tholddark": 21597, "tholdoffset": 7000, "ledindication": False, "usertest": False, "pending": []}, "modelid": "SML001"}
                        bridge_config["sensors"][str(int(new_sensor_id) + 1)] = {"name": "Hue temperature sensor 1", "uniqueid": "00:17:88:01:02:" + deconz_sensors[sensor]["uniqueid"][12:-1] + "2", "type": "ZLLTemperature", "swversion": "6.1.0.18912", "state": {"temperature": None, "lastupdated": "none"}, "manufacturername": "Philips", "config": {"on": False, "battery": 100, "reachable": True, "alert":"none", "ledindication": False, "usertest": False, "pending": []}, "modelid": "SML001"}
                        bridge_config["deconz"]["sensors"][sensor] = {"bridgeid": new_sensor_id}
                    elif deconz_sensors[sensor]["type"] == "ZHAPresence":
                        print("register new Xiaomi motion sensor")
                        bridge_config["sensors"][new_sensor_id] = {"name": "Entrance Lights sensor", "uniqueid": "00:17:88:01:02:" + deconz_sensors[sensor]["uniqueid"][12:], "type": "ZLLPresence", "swversion": "6.1.0.18912", "state": {"lastupdated": "none", "presence": None}, "manufacturername": "Philips", "config": {"on": False,"battery": 100,"reachable": True, "alert": "lselect", "ledindication": False, "usertest": False, "sensitivity": 2, "sensitivitymax": 2,"pending": []}, "modelid": "SML001"}
                        bridge_config["deconz"]["sensors"][sensor] = {"bridgeid": new_sensor_id}
                else:
                    bridge_config["sensors"][new_sensor_id] = deconz_sensors[sensor]
                    bridge_config["deconz"]["sensors"][sensor] = {"bridgeid": new_sensor_id}
            else: #temporary patch for config compatibility with new release
                bridge_config["deconz"]["sensors"][sensor]["modelid"] = deconz_sensors[sensor]["modelid"]
                bridge_config["deconz"]["sensors"][sensor]["type"] = deconz_sensors[sensor]["type"]
        generateSensorsState()

        if "websocketport" in bridge_config["deconz"]:
            print("Starting deconz websocket")
            Thread(target=websocketClient).start()

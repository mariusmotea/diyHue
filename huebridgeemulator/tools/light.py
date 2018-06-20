from pprint import pprint
import requests
import json
from time import sleep
from threading import Thread
from datetime import datetime
import socket

from subprocess import check_output

from huebridgeemulator.http.websocket import scanDeconz
from huebridgeemulator.device.tradfri import scanTradfri
from huebridgeemulator.device.yeelight import discoverYeelight
from huebridgeemulator.tools.colors import convert_rgb_xy, convert_xy
from huebridgeemulator.http.client import sendRequest


def getIpAddress():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]

def syncWithLights(conf_obj): #update Hue Bridge lights states
    bridge_config = conf_obj.bridge
    while True:
        print("sync with lights")
        for light in bridge_config["lights_address"]:
            try:
                if bridge_config["lights_address"][light]["protocol"] == "native":
                    light_data = json.loads(sendRequest("http://" + bridge_config["lights_address"][light]["ip"] + "/get?light=" + str(bridge_config["lights_address"][light]["light_nr"]), "GET", "{}"))
                    bridge_config["lights"][light]["state"].update(light_data)
                elif bridge_config["lights_address"][light]["protocol"] == "hue":
                    light_data = json.loads(sendRequest("http://" + bridge_config["lights_address"][light]["ip"] + "/api/" + bridge_config["lights_address"][light]["username"] + "/lights/" + bridge_config["lights_address"][light]["light_id"], "GET", "{}"))
                    bridge_config["lights"][light]["state"].update(light_data["state"])
                elif bridge_config["lights_address"][light]["protocol"] == "ikea_tradfri":
                    light_data = json.loads(check_output("./coap-client-linux -m get -u \"" + bridge_config["lights_address"][light]["identity"] + "\" -k \"" + bridge_config["lights_address"][light]["preshared_key"] + "\" \"coaps://" + bridge_config["lights_address"][light]["ip"] + ":5684/15001/" + str(bridge_config["lights_address"][light]["device_id"]) +"\"", shell=True).decode('utf-8').split("\n")[3])
                    bridge_config["lights"][light]["state"]["on"] = bool(light_data["3311"][0]["5850"])
                    bridge_config["lights"][light]["state"]["bri"] = light_data["3311"][0]["5851"]
                    if "5706" in light_data["3311"][0]:
                        if light_data["3311"][0]["5706"] == "f5faf6":
                            bridge_config["lights"][light]["state"]["ct"] = 170
                        elif light_data["3311"][0]["5706"] == "f1e0b5":
                            bridge_config["lights"][light]["state"]["ct"] = 320
                        elif light_data["3311"][0]["5706"] == "efd275":
                            bridge_config["lights"][light]["state"]["ct"] = 470
                    else:
                        bridge_config["lights"][light]["state"]["ct"] = 470
                elif bridge_config["lights_address"][light]["protocol"] == "milight":
                    light_data = json.loads(sendRequest("http://" + bridge_config["lights_address"][light]["ip"] + "/gateways/" + bridge_config["lights_address"][light]["device_id"] + "/" + bridge_config["lights_address"][light]["mode"] + "/" + str(bridge_config["lights_address"][light]["group"]), "GET", "{}"))
                    if light_data["state"] == "ON":
                        bridge_config["lights"][light]["state"]["on"] = True
                    else:
                        bridge_config["lights"][light]["state"]["on"] = False
                    if "brightness" in light_data:
                        bridge_config["lights"][light]["state"]["bri"] = light_data["brightness"]
                    if "color_temp" in light_data:
                        bridge_config["lights"][light]["state"]["colormode"] = "ct"
                        bridge_config["lights"][light]["state"]["ct"] = light_data["color_temp"] * 1.6
                    elif "bulb_mode" in light_data and light_data["bulb_mode"] == "color":
                        bridge_config["lights"][light]["state"]["colormode"] = "xy"
                        bridge_config["lights"][light]["state"]["xy"] = convert_rgb_xy(light_data["color"]["r"], light_data["color"]["g"], light_data["color"]["b"])
                elif bridge_config["lights_address"][light]["protocol"] == "yeelight": #getting states from the yeelight
                    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    tcp_socket.settimeout(5)
                    tcp_socket.connect((bridge_config["lights_address"][light]["ip"], int(55443)))
                    msg=json.dumps({"id": 1, "method": "get_prop", "params":["power","bright"]}) + "\r\n"
                    tcp_socket.send(msg.encode())
                    data = tcp_socket.recv(16 * 1024)
                    light_data = json.loads(data[:-2].decode("utf8"))["result"]
                    if light_data[0] == "on": #powerstate
                        bridge_config["lights"][light]["state"]["on"] = True
                    else:
                        bridge_config["lights"][light]["state"]["on"] = False
                    bridge_config["lights"][light]["state"]["bri"] = int(int(light_data[1]) * 2.54)
                    msg_mode=json.dumps({"id": 1, "method": "get_prop", "params":["color_mode"]}) + "\r\n"
                    tcp_socket.send(msg_mode.encode())
                    data = tcp_socket.recv(16 * 1024)
                    if json.loads(data[:-2].decode("utf8"))["result"][0] == "1": #rgb mode
                        msg_rgb=json.dumps({"id": 1, "method": "get_prop", "params":["rgb"]}) + "\r\n"
                        tcp_socket.send(msg_rgb.encode())
                        data = tcp_socket.recv(16 * 1024)
                        hue_data = json.loads(data[:-2].decode("utf8"))["result"]
                        hex_rgb = "%6x" % int(json.loads(data[:-2].decode("utf8"))["result"][0])
                        r = hex_rgb[:2]
                        if r == "  ":
                            r = "00"
                        g = hex_rgb[3:4]
                        if g == "  ":
                            g = "00"
                        b = hex_rgb[-2:]
                        if b == "  ":
                            b = "00"
                        bridge_config["lights"][light]["state"]["xy"] = convert_rgb_xy(int(r,16), int(g,16), int(b,16))
                        bridge_config["lights"][light]["state"]["colormode"] = "xy"
                    elif json.loads(data[:-2].decode("utf8"))["result"][0] == "2": #ct mode
                        msg_ct=json.dumps({"id": 1, "method": "get_prop", "params":["ct"]}) + "\r\n"
                        tcp_socket.send(msg_ct.encode())
                        data = tcp_socket.recv(16 * 1024)
                        bridge_config["lights"][light]["state"]["ct"] =  int(1000000 / int(json.loads(data[:-2].decode("utf8"))["result"][0]))
                        bridge_config["lights"][light]["state"]["colormode"] = "ct"

                    elif json.loads(data[:-2].decode("utf8"))["result"][0] == "3": #ct mode
                        msg_hsv=json.dumps({"id": 1, "method": "get_prop", "params":["hue","sat"]}) + "\r\n"
                        tcp_socket.send(msg_hsv.encode())
                        data = tcp_socket.recv(16 * 1024)
                        hue_data = json.loads(data[:-2].decode("utf8"))["result"]
                        bridge_config["lights"][light]["state"]["hue"] = int(hue_data[0] * 182)
                        bridge_config["lights"][light]["state"]["sat"] = int(int(hue_data[1]) * 2.54)
                        bridge_config["lights"][light]["state"]["colormode"] = "hs"
                    tcp_socket.close()

                elif bridge_config["lights_address"][light]["protocol"] == "domoticz": #domoticz protocol
                    light_data = json.loads(sendRequest("http://" + bridge_config["lights_address"][light]["ip"] + "/json.htm?type=devices&rid=" + bridge_config["lights_address"][light]["light_id"], "GET", "{}"))
                    if light_data["result"][0]["Status"] == "Off":
                         bridge_config["lights"][light]["state"]["on"] = False
                    else:
                         bridge_config["lights"][light]["state"]["on"] = True
                    bridge_config["lights"][light]["state"]["bri"] = str(round(float(light_data["result"][0]["Level"])/100*255))

                bridge_config["lights"][light]["state"]["reachable"] = True
                updateGroupStats(conf_obj, light)
            except Exception as exp:
                bridge_config["lights"][light]["state"]["reachable"] = False
                bridge_config["lights"][light]["state"]["on"] = False
                print("light " + light + " is unreachable")
                raise exp
        sleep(10) #wait at last 10 seconds before next sync
        i = 0
        while i < 300: #sync with lights every 300 seconds or instant if one user is connected
            for user in bridge_config["config"]["whitelist"].keys():
                if bridge_config["config"]["whitelist"][user]["last use date"] == datetime.now().strftime("%Y-%m-%dT%H:%M:%S"):
                    i = 300
                    break
            sleep(1)


def scanForLights(conf_obj, new_lights): #scan for ESP8266 lights and strips
    Thread(target=discoverYeelight, args=[conf_obj, new_lights]).start()
    #return all host that listen on port 80
    device_ips = check_output("nmap  " + getIpAddress() + "/24 -p80 --open -n | grep report | cut -d ' ' -f5", shell=True).decode('utf-8').split("\n")
    pprint(device_ips)
    del device_ips[-1] #delete last empty element in list
    for ip in device_ips:
        try:
            if ip != getIpAddress():
                response = requests.get("http://" + ip + "/detect", timeout=3)
                if response.status_code == 200:
                    device_data = json.loads(response.text)
                    pprint(device_data)
                    if "hue" in device_data:
                        print(ip + " is a hue " + device_data['hue'])
                        device_exist = False
                        for light in conf_obj.bridge["lights"].keys():
                            if conf_obj.bridge["lights"][light]["uniqueid"].startswith( device_data["mac"] ):
                                device_exist = True
                                conf_obj.bridge["lights_address"][light]["ip"] = ip
                        if not device_exist:
                            light_name = "Hue " + device_data["hue"] + " " + device_data["modelid"]
                            if "name" in device_data:
                                light_name = device_data["name"]
                            print("Add new light: " + light_name)
                            for x in range(1, int(device_data["lights"]) + 1):
                                new_light_id = nextFreeId("lights")
                                conf_obj.bridge["lights"][new_light_id] = {"state": light_types[device_data["modelid"]]["state"], "type": light_types[device_data["modelid"]]["type"], "name": light_name if x == 1 else light_name + " " + str(x), "uniqueid": device_data["mac"] + "-" + str(x), "modelid": device_data["modelid"], "manufacturername": "Philips", "swversion": light_types[device_data["modelid"]]["swversion"]}
                                new_lights.update({new_light_id: {"name": light_name if x == 1 else light_name + " " + str(x)}})
                                conf_obj.bridge["lights_address"][new_light_id] = {"ip": ip, "light_nr": x, "protocol": "native"}
        except Exception as exp:
            raise exp
            print("ip " + ip + " is unknow device")
    scanDeconz(conf_obj)
    # TODO activatethis
    #scanTradfri()
    conf_obj.save()


def updateGroupStats(conf_obj, light): #set group stats based on lights status in that group
    bridge_config = conf_obj.bridge
    for group in bridge_config["groups"]:
        if "lights" in bridge_config["groups"][group] and light in bridge_config["groups"][group]["lights"]:
            for key, value in bridge_config["lights"][light]["state"].items():
                if key in ["bri", "xy", "ct", "hue", "sat"]:
                    bridge_config["groups"][group]["action"][key] = value
            any_on = False
            all_on = True
            for group_light in bridge_config["groups"][group]["lights"]:
                if bridge_config["lights"][light]["state"]["on"] == True:
                    any_on = True
                else:
                    all_on = False
            bridge_config["groups"][group]["state"] = {"any_on": any_on, "all_on": all_on,}
            bridge_config["groups"][group]["action"]["on"] = any_on


def sendLightRequest(conf_obj, light, data):
    bridge_config = conf_obj.bridge
    payload = {}
    if light in bridge_config["lights_address"]:
        if bridge_config["lights_address"][light]["protocol"] == "native": #ESP8266 light or strip
            url = "http://" + bridge_config["lights_address"][light]["ip"] + "/set?light=" + str(bridge_config["lights_address"][light]["light_nr"]);
            method = 'GET'
            for key, value in data.items():
                if key == "xy":
                    url += "&x=" + str(value[0]) + "&y=" + str(value[1])
                else:
                    url += "&" + key + "=" + str(value)
        elif bridge_config["lights_address"][light]["protocol"] in ["hue","deconz"]: #Original Hue light or Deconz light
            url = "http://" + bridge_config["lights_address"][light]["ip"] + "/api/" + bridge_config["lights_address"][light]["username"] + "/lights/" + bridge_config["lights_address"][light]["light_id"] + "/state"
            method = 'PUT'
            payload.update(data)

        elif bridge_config["lights_address"][light]["protocol"] == "domoticz": #Domoticz protocol
            url = "http://" + bridge_config["lights_address"][light]["ip"] + "/json.htm?type=command&param=switchlight&idx=" + bridge_config["lights_address"][light]["light_id"];
            method = 'GET'
            for key, value in data.items():
                if key == "on":
                    if value:
                        url += "&switchcmd=On"
                    else:
                        url += "&switchcmd=Off"
                elif key == "bri":
                    url += "&switchcmd=Set%20Level&level=" + str(round(float(value)/255*100)) # domoticz range from 0 to 100 (for zwave devices) instead of 0-255 of bridge

        elif bridge_config["lights_address"][light]["protocol"] == "milight": #MiLight bulb
            url = "http://" + bridge_config["lights_address"][light]["ip"] + "/gateways/" + bridge_config["lights_address"][light]["device_id"] + "/" + bridge_config["lights_address"][light]["mode"] + "/" + str(bridge_config["lights_address"][light]["group"]);
            method = 'PUT'
            for key, value in data.items():
                if key == "on":
                    payload["status"] = value
                elif key == "bri":
                    payload["brightness"] = value
                elif key == "ct":
                    payload["color_temp"] = int(value / 1.6 + 153)
                elif key == "hue":
                    payload["hue"] = value / 180
                elif key == "sat":
                    payload["saturation"] = value * 100 / 255
                elif key == "xy":
                    payload["color"] = {}
                    (payload["color"]["r"], payload["color"]["g"], payload["color"]["b"]) = convert_xy(value[0], value[1], bridge_config["lights"][light]["state"]["bri"])
            print(json.dumps(payload))
        elif bridge_config["lights_address"][light]["protocol"] == "yeelight": #YeeLight bulb
            url = "http://" + str(bridge_config["lights_address"][light]["ip"])
            method = 'TCP'
            transitiontime = 400
            if "transitiontime" in data:
                transitiontime = data["transitiontime"] * 100
            for key, value in data.items():
                if key == "on":
                    if value:
                        payload["set_power"] = ["on", "smooth", transitiontime]
                    else:
                        payload["set_power"] = ["off", "smooth", transitiontime]
                elif key == "bri":
                    payload["set_bright"] = [int(value / 2.55) + 1, "smooth", transitiontime]
                elif key == "ct":
                    payload["set_ct_abx"] = [int(1000000 / value), "smooth", transitiontime]
                elif key == "hue":
                    payload["set_hsv"] = [int(value / 182), int(bridge_config["lights"][light]["state"]["sat"] / 2.54), "smooth", transitiontime]
                elif key == "sat":
                    payload["set_hsv"] = [int(value / 2.54), int(bridge_config["lights"][light]["state"]["hue"] / 2.54), "smooth", transitiontime]
                elif key == "xy":
                    color = convert_xy(value[0], value[1], bridge_config["lights"][light]["state"]["bri"])
                    payload["set_rgb"] = [(color[0] * 65536) + (color[1] * 256) + color[2], "smooth", transitiontime] #according to docs, yeelight needs this to set rgb. its r * 65536 + g * 256 + b
                elif key == "alert" and value != "none":
                    payload["start_cf"] = [ 4, 0, "1000, 2, 5500, 100, 1000, 2, 5500, 1, 1000, 2, 5500, 100, 1000, 2, 5500, 1"]


        elif bridge_config["lights_address"][light]["protocol"] == "ikea_tradfri": #IKEA Tradfri bulb
            url = "coaps://" + bridge_config["lights_address"][light]["ip"] + ":5684/15001/" + str(bridge_config["lights_address"][light]["device_id"])
            for key, value in data.items():
                if key == "on":
                    payload["5850"] = int(value)
                elif key == "transitiontime":
                    payload["5712"] = value
                elif key == "bri":
                    payload["5851"] = value
                elif key == "ct":
                    if value < 270:
                        payload["5706"] = "f5faf6"
                    elif value < 385:
                        payload["5706"] = "f1e0b5"
                    else:
                        payload["5706"] = "efd275"
                elif key == "xy":
                    payload["5709"] = int(value[0] * 65535)
                    payload["5710"] = int(value[1] * 65535)
            if "hue" in data or "sat" in data:
                if("hue" in data):
                    hue = data["hue"]
                else:
                    hue = bridge_config["lights"][light]["state"]["hue"]
                if("sat" in data):
                    sat = data["sat"]
                else:
                    sat = bridge_config["lights"][light]["state"]["sat"]
                if("bri" in data):
                    bri = data["bri"]
                else:
                    bri = bridge_config["lights"][light]["state"]["bri"]
                rgbValue = hsv_to_rgb(hue, sat, bri)
                xyValue = convert_rgb_xy(rgbValue[0], rgbValue[1], rgbValue[2])
                payload["5709"] = int(xyValue[0] * 65535)
                payload["5710"] = int(xyValue[1] * 65535)
            if "5850" in payload and payload["5850"] == 0:
                payload.clear() #setting brightnes will turn on the ligh even if there was a request to power off
                payload["5850"] = 0
            elif "5850" in payload and "5851" in payload: #when setting brightness don't send also power on command
                del payload["5850"]

        try:
            if bridge_config["lights_address"][light]["protocol"] == "ikea_tradfri":
                if "5712" not in payload:
                    payload["5712"] = 4 #If no transition add one, might also add check to prevent large transitiontimes
                    check_output("./coap-client-linux -m put -u \"" + bridge_config["lights_address"][light]["identity"] + "\" -k \"" + bridge_config["lights_address"][light]["preshared_key"] + "\" -e '{ \"3311\": [" + json.dumps(payload) + "] }' \"" + url + "\"", shell=True)
            elif bridge_config["lights_address"][light]["protocol"] in ["hue", "deconz"]:
                if "xy" in payload:
                    sendRequest(url, method, json.dumps({"on": True, "xy": payload["xy"]}))
                    del(payload["xy"])
                    sleep(0.6)
                elif "ct" in payload:
                    sendRequest(url, method, json.dumps({"on": True, "ct": payload["ct"]}))
                    del(payload["ct"])
                    sleep(0.6)
                sendRequest(url, method, json.dumps(payload))
            else:
                sendRequest(url, method, json.dumps(payload))
        except Exception as exp:
            bridge_config["lights"][light]["state"]["reachable"] = False
            print("request error")
            raise(exp)
        else:
            bridge_config["lights"][light]["state"]["reachable"] = True
            print("LightRequest: " + url)



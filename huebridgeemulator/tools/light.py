from time import sleep
from datetime import datetime


def syncWithLights(bridge_config): #update Hue Bridge lights states
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
                updateGroupStats(light)
            except:
                bridge_config["lights"][light]["state"]["reachable"] = False
                bridge_config["lights"][light]["state"]["on"] = False
                print("light " + light + " is unreachable")
        sleep(10) #wait at last 10 seconds before next sync
        i = 0
        while i < 300: #sync with lights every 300 seconds or instant if one user is connected
            for user in bridge_config["config"]["whitelist"].keys():
                if bridge_config["config"]["whitelist"][user]["last use date"] == datetime.now().strftime("%Y-%m-%dT%H:%M:%S"):
                    i = 300
                    break
            sleep(1)

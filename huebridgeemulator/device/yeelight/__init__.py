import socket
import random
import json

from huebridgeemulator.const import LIGHT_TYPES
from huebridgeemulator.device.yeelight.light import YeelightLight, YeelightLightAddress
from huebridgeemulator.device.light import LightState



def _nextFreeId(bridge_config, element):
    i = 1
    while (str(i)) in bridge_config[element]:
        i += 1
    return str(i)


def sendToYeelight(url, api_method, param):
    try:
#        print({"id": 1, "method": api_method, "params": param})
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.settimeout(5)
        tcp_socket.connect((url, int(55443)))
        msg = json.dumps({"id": 1, "method": api_method, "params": param}) + "\r\n"
        tcp_socket.send(msg.encode())
        tcp_socket.close()
    except Exception as e:
        raise e
        print ("Unexpected error:", e)


def discoverYeelight(registry):
    group = ("239.255.255.250", 1982)
    message = "\r\n".join([
        'M-SEARCH * HTTP/1.1',
        'HOST: 239.255.255.250:1982',
        'MAN: "ssdp:discover"',
        'ST: wifi_bulb'])
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.settimeout(3)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    sock.sendto(message.encode(), group)
    # FIXME remove while true to do something smarter
    while True:
        try:
            response = sock.recv(1024).decode('utf-8').split("\r\n")
            properties = {"rgb": False, "ct": False}
            for line in response:
                if line[:2] == "id":
                    properties["id"] = line[4:]
                elif line[:3] == "rgb":
                    properties["rgb"] = True
                elif line[:2] == "ct":
                    properties["ct"] = True
                elif line[:8] == "Location":
                    properties["ip"] = line.split(":")[2][2:]
                elif line[:4] == "name":
                    properties["name"] = line[6:]
            device_exist = False
            # Check if the device exists
            for index, light in registry.lights.items():
                if light.address.protocol == "yeelight" and light.address.id == properties["id"]:
                    device_exist = True
                    light.address.ip = properties["ip"]
                    # TODO LOGGER
                    print("light id " + properties["id"] + " already exist, updating ip...")
                    break
            if (not device_exist):
                light_name = "YeeLight id " + properties["id"][-8:] if properties["name"] == "" else properties["name"]
                print("Add YeeLight: " + properties["id"])
                modelid = "LWB010"
                if properties["rgb"]:
                    modelid = "LCT015"
                elif properties["ct"]:
                    modelid = "LTW001"
                address = {"ip": properties["ip"], "id": properties["id"], "protocol": "yeelight"}
                raw_light = {"type": LIGHT_TYPES[modelid]["type"],
                             "name": light_name,
                             "uniqueid": "4a:e0:ad:7f:cf:" + str(random.randrange(0, 99)) + "-1",
                             "modelid": modelid,
                             "manufacturername": "yeelight",
                             "state": LightState(LIGHT_TYPES[modelid]["state"]),
                             "address": YeelightLightAddress(address),
                             "swversion": LIGHT_TYPES[modelid]["swversion"]}
                new_light = YeelightLight(raw_light)
                registry.lights[new_light.index] = new_light
                registry.add_new_light(new_light)

        except socket.timeout as exp:
            print('Yeelight search end')
            sock.close()
            break

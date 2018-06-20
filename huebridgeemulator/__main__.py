#!/usr/bin/python3
from collections import defaultdict
from threading import Thread
from uuid import getnode as get_mac
from time import sleep

from huebridgeemulator.http.websocket import scanDeconz
from huebridgeemulator.config import saveConfig, loadConfig
from huebridgeemulator.tools import getIpAddress, generateSensorsState
from huebridgeemulator.tools.ssdp import ssdpSearch, ssdpBroadcast
from huebridgeemulator.tools.scheduler import schedulerProcessor
from huebridgeemulator.tools.light import syncWithLights
from huebridgeemulator.http.web import run



def main():

    update_lights_on_startup = False # if set to true all lights will be updated with last know state on startup.

    mac = '%012x' % get_mac()

    run_service = True

    bridge_config = defaultdict(lambda:defaultdict(str))
    new_lights = {}
    sensors_state = {}

    light_types = {"LCT015": {"state": {"on": False, "bri": 200, "hue": 0, "sat": 0, "xy": [0.0, 0.0], "ct": 461, "alert": "none", "effect": "none", "colormode": "ct", "reachable": True}, "type": "Extended color light", "swversion": "1.29.0_r21169"}, "LST001": {"state": {"on": False, "bri": 200, "hue": 0, "sat": 0, "xy": [0.0, 0.0], "ct": 461, "alert": "none", "effect": "none", "colormode": "ct", "reachable": True}, "type": "Color light", "swversion": "66010400"}, "LWB010": {"state": {"on": False, "bri": 254,"alert": "none", "reachable": True}, "type": "Dimmable light", "swversion": "1.15.0_r18729"}, "LTW001": {"state": {"on": False, "colormode": "ct", "alert": "none", "reachable": True, "bri": 254, "ct": 230}, "type": "Color temperature light", "swversion": "5.50.1.19085"}, "Plug 01": {"state": {"on": False, "alert": "none", "reachable": True}, "type": "On/Off plug-in unit", "swversion": "V1.04.12"}}


    bridge_config = loadConfig('/home/tcohen/perso/gits/github.com/mariusmotea/diyHue/config.json')

    bridge_config, sensors_state = generateSensorsState(bridge_config, sensors_state)
    ip_pices = getIpAddress().split(".")
    bridge_config["config"]["ipaddress"] = getIpAddress()
    bridge_config["config"]["gateway"] = ip_pices[0] + "." +  ip_pices[1] + "." + ip_pices[2] + ".1"
    bridge_config["config"]["mac"] = mac[0] + mac[1] + ":" + mac[2] + mac[3] + ":" + mac[4] + mac[5] + ":" + mac[6] + mac[7] + ":" + mac[8] + mac[9] + ":" + mac[10] + mac[11]
    bridge_config["config"]["bridgeid"] = (mac[:6] + 'FFFE' + mac[6:]).upper()






    if bridge_config["deconz"]["enabled"]:
        scanDeconz()
    try:
        run_service = True
        mac = '%012x' % get_mac()
        if update_lights_on_startup:
            updateAllLights()
        Thread(target=ssdpSearch, args=[getIpAddress(), mac]).start()
        Thread(target=ssdpBroadcast, args=[getIpAddress(), mac]).start()
        Thread(target=schedulerProcessor, args=[bridge_config, run_service]).start()
        Thread(target=syncWithLights, args=[bridge_config]).start()
        Thread(target=run, args=[False, bridge_config]).start()
        Thread(target=run, args=[True, bridge_config]).start()
        while True:
            sleep(10)
    except Exception as e:
        print("server stopped " + str(e))
    finally:
        run_service = False
        saveConfig('/home/tcohen/perso/gits/github.com/mariusmotea/diyHue/config.json', bridge_config)
        print ('config saved')


if __name__ == "__main__":
    main()

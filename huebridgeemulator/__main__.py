#!/usr/bin/python3
from collections import defaultdict
from threading import Thread
from uuid import getnode as get_mac
from time import sleep
import argparse


from huebridgeemulator.http.websocket import scanDeconz
from huebridgeemulator.config import saveConfig, loadConfig, Config
from huebridgeemulator.tools import getIpAddress, generateSensorsState
from huebridgeemulator.tools.ssdp import ssdpSearch, ssdpBroadcast
from huebridgeemulator.tools.scheduler import schedulerProcessor
from huebridgeemulator.tools.light import syncWithLights
from huebridgeemulator.http.web import run
from huebridgeemulator.web.server import start



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config-file',
                        required=True, help='Config file')
    args = parser.parse_args()


    update_lights_on_startup = False # if set to true all lights will be updated with last know state on startup.

    mac = '%012x' % get_mac()

    run_service = True

    new_lights = {}
    sensors_state = {}

    light_types = {"LCT015": {"state": {"on": False, "bri": 200, "hue": 0, "sat": 0, "xy": [0.0, 0.0], "ct": 461, "alert": "none", "effect": "none", "colormode": "ct", "reachable": True}, "type": "Extended color light", "swversion": "1.29.0_r21169"}, "LST001": {"state": {"on": False, "bri": 200, "hue": 0, "sat": 0, "xy": [0.0, 0.0], "ct": 461, "alert": "none", "effect": "none", "colormode": "ct", "reachable": True}, "type": "Color light", "swversion": "66010400"}, "LWB010": {"state": {"on": False, "bri": 254,"alert": "none", "reachable": True}, "type": "Dimmable light", "swversion": "1.15.0_r18729"}, "LTW001": {"state": {"on": False, "colormode": "ct", "alert": "none", "reachable": True, "bri": 254, "ct": 230}, "type": "Color temperature light", "swversion": "5.50.1.19085"}, "Plug 01": {"state": {"on": False, "alert": "none", "reachable": True}, "type": "On/Off plug-in unit", "swversion": "V1.04.12"}}


    conf_obj = Config(args.config_file)
    bridge_config = conf_obj.bridge

    bridge_config, sensors_state = generateSensorsState(bridge_config, sensors_state)

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
        Thread(target=syncWithLights, args=[conf_obj]).start()
        Thread(target=run, args=[False, conf_obj, sensors_state]).start()
        Thread(target=run, args=[True, conf_obj, sensors_state]).start()
#        Thread(target=start, args=[conf_obj, sensors_state]).start()
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

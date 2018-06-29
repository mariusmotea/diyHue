#!/usr/bin/python3
from collections import defaultdict
from threading import Thread
from uuid import getnode as get_mac
from time import sleep
import argparse


from huebridgeemulator.http.websocket import scanDeconz
from huebridgeemulator.config import saveConfig, loadConfig, Config
from huebridgeemulator.tools import getIpAddress, generateSensorsState
from huebridgeemulator.tasks.ssdp import ssdp_search, ssdp_broadcast
from huebridgeemulator.tasks.scheduler import scheduler_processor
from huebridgeemulator.tasks.light import sync_with_lights
from huebridgeemulator.http.web import run
from huebridgeemulator.web.server import start
from huebridgeemulator.logger import main_logger, LOG_LEVELS


def main():
    """Main and entrypoitn function."""
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config-file',
                        required=True, help='Config file')
    parser.add_argument('-l', '--log-level', choices=LOG_LEVELS,
                        default="WARNING", help='Log Level')
    args = parser.parse_args()
    # Set log level
    main_logger.setLevel(args.log_level)

    # Setings some variables ??!!
    sensors_state = {}
    update_lights_on_startup = False # if set to true all lights will be updated with last know state on startup.

    # Load config
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
        Thread(target=ssdp_search).start()
        Thread(target=ssdp_broadcast).start()
        Thread(target=scheduler_processor, args=[conf_obj, sensors_state, run_service]).start()
        Thread(target=sync_with_lights, args=[conf_obj]).start()
#        Thread(target=run, args=[False, conf_obj, sensors_state]).start()
#        Thread(target=run, args=[True, conf_obj, sensors_state]).start()
        Thread(target=start, args=[conf_obj, sensors_state]).start()
        while True:
            sleep(10)
    except Exception as e:
        print("server stopped " + str(e))
    finally:
        run_service = False
        saveConfig('/home/tcohen/perso/gits/github.com/mariusmotea/diyHue/config.json', bridge_config)
        print('config saved')


if __name__ == "__main__":
    main()

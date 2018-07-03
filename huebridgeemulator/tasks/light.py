"""???

.. todo:: Add description and some comments
"""
from datetime import datetime
import json
from subprocess import check_output
from time import sleep

from huebridgeemulator.tools.colors import convert_rgb_xy
from huebridgeemulator.tools.light import updateGroupStats
from huebridgeemulator.http.client import sendRequest
from huebridgeemulator.logger import sync_with_lights_logger


# pylint: disable=R0912
def sync_with_lights(conf_obj):
    """Update Hue Bridge lights states.

    .. todo:: add some comments
    """
    bridge_config = conf_obj.bridge
    sync_with_lights_logger.info("Thread SyncWithLights starting")
    while True:
        sync_with_lights_logger.debug("Sync with lights")
        for light in bridge_config["lights_address"]:
            try:
                if bridge_config["lights_address"][light]["protocol"] == "native":
                    url = "http://{}/get?light={}".format(
                        bridge_config["lights_address"][light]["ip"],
                        str(bridge_config["lights_address"][light]["light_nr"]))
                    light_data = json.loads(sendRequest(url, "GET", "{}"))
                    bridge_config["lights"][light]["state"].update(light_data)
                elif bridge_config["lights_address"][light]["protocol"] == "hue":
                    url = "http://{}/api/{}/lights/{}".format(
                        bridge_config["lights_address"][light]["ip"],
                        bridge_config["lights_address"][light]["username"],
                        bridge_config["lights_address"][light]["light_id"])
                    light_data = json.loads(sendRequest(url, "GET", "{}"))
                    bridge_config["lights"][light]["state"].update(light_data["state"])
                elif bridge_config["lights_address"][light]["protocol"] == "ikea_tradfri":
                    command_line = ('./coap-client-linux -m get -u "{}" -k "{}" '
                                    '"coaps://{}:5684/15001/{}"'.format(
                                        bridge_config["lights_address"][light]["identity"],
                                        bridge_config["lights_address"][light]["preshared_key"],
                                        bridge_config["lights_address"][light]["ip"],
                                        str(bridge_config["lights_address"][light]["device_id"])))
                    light_data = json.loads(check_output(command_line, shell=True)
                                            .decode('utf-8').split("\n")[3])
                    bridge_config["lights"][light]["state"]["on"] = \
                        bool(light_data["3311"][0]["5850"])
                    bridge_config["lights"][light]["state"]["bri"] = \
                        light_data["3311"][0]["5851"]
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
                    url = "http://{}/gateways/{}/{}/{}".format(
                        bridge_config["lights_address"][light]["ip"],
                        bridge_config["lights_address"][light]["device_id"],
                        bridge_config["lights_address"][light]["mode"],
                        str(bridge_config["lights_address"][light]["group"]))
                    light_data = json.loads(sendRequest(url, "GET", "{}"))
                    # if light_data["state"] == "ON":
                    #     bridge_config["lights"][light]["state"]["on"] = True
                    # else:
                    #     bridge_config["lights"][light]["state"]["on"] = False
                    # Replaced by the next two lines
                    bridge_config["lights"][light]["state"]["on"] = \
                        bool(light_data["state"] == "ON")
                    if "brightness" in light_data:
                        bridge_config["lights"][light]["state"]["bri"] = light_data["brightness"]
                    if "color_temp" in light_data:
                        bridge_config["lights"][light]["state"]["colormode"] = "ct"
                        bridge_config["lights"][light]["state"]["ct"] = \
                            light_data["color_temp"] * 1.6
                    elif "bulb_mode" in light_data and light_data["bulb_mode"] == "color":
                        bridge_config["lights"][light]["state"]["colormode"] = "xy"
                        bridge_config["lights"][light]["state"]["xy"] = \
                            convert_rgb_xy(light_data["color"]["r"],
                                           light_data["color"]["g"],
                                           light_data["color"]["b"])
                elif bridge_config["lights_address"][light]["protocol"] == "yeelight":
                    # getting states from the yeelight
                    current_light = conf_obj.get_resource("lights", light)
                    current_light.update_status()
                    bridge_config["lights"][light] = current_light.serialize()
                elif bridge_config["lights_address"][light]["protocol"] == "domoticz":
                    # domoticz protocol
                    url = "http://{}/json.htm?type=devices&rid={}".format(
                        bridge_config["lights_address"][light]["ip"],
                        bridge_config["lights_address"][light]["light_id"])
                    light_data = json.loads(sendRequest(url, "GET", "{}"))
                    if light_data["result"][0]["Status"] == "Off":
                        bridge_config["lights"][light]["state"]["on"] = False
                    else:
                        bridge_config["lights"][light]["state"]["on"] = True
                    bridge_config["lights"][light]["state"]["bri"] = \
                        str(round(float(light_data["result"][0]["Level"]) / 100 * 255))

                bridge_config["lights"][light]["state"]["reachable"] = True
                updateGroupStats(conf_obj, light)
            except Exception as exp:
                bridge_config["lights"][light]["state"]["reachable"] = False
                bridge_config["lights"][light]["state"]["on"] = False
                sync_with_lights_logger.warning("light %s is unreachable", light)
                raise exp
        sleep(10)  # wait at last 10 seconds before next sync
        i = 0
        while i < 300:  # sync with lights every 300 seconds or instant if one user is connected
            for user in bridge_config["config"]["whitelist"].keys():
                # FIXME: Why this comparison ? We should compare datetime objects instead of str ?
                now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                if bridge_config["config"]["whitelist"][user]["last use date"] == now:
                    i = 300
                    break
            sleep(1)

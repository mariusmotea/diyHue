"""???

.. todo:: Add description and some comments
"""
from datetime import datetime
import json
from subprocess import check_output
import time

from huebridgeemulator.tools.colors import convert_rgb_xy
from huebridgeemulator.tools.group import update_group_status
from huebridgeemulator.http.client import sendRequest
from huebridgeemulator.logger import sync_with_lights_logger


# pylint: disable=R0912
def sync_with_lights(registry):
    """Update Hue Bridge lights states.

    .. todo:: add some comments
    """
    sync_with_lights_logger.info("Thread SyncWithLights starting")
    while True:
        sync_with_lights_logger.debug("Sync with lights")
        for light in registry.lights.values():
            try:
                if light.address.protocol in ("yeelight", "tplink", "hue"):
                    light.update_status()
                elif light.address.protocol == "native":
                    url = "http://{}/get?light={}".format(
                        light.address.ip,
                        str(light.address.light_nr))
                    # TODO convert
                    # light.update_status()
                    light_data = json.loads(sendRequest(url, "GET", "{}"))
                    bridge_config["lights"][light]["state"].update(light_data)
                elif light.address.protocol == "ikea_tradfri":
                    # TODO
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
                elif light.address.protocol == "milight":
                    # TODO
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
                elif light.address.protocol == "domoticz":
                    # TODO
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

                light.state.reachable = True
                # Update groups status
                update_group_status(registry, light)
            except Exception as exp:
                sync_with_lights_logger.warning(exp)
                light.set_unreachable()
                sync_with_lights_logger.warning("light %s is unreachable", light)
                raise exp
        i = 0
        while i < 300:  # sync with lights every 300 seconds or instant if one user is connected
            for user in registry.config["whitelist"].keys():
                last_use_date_str = registry.config["whitelist"][user]["last use date"]
                last_use_date = datetime.strptime(last_use_date_str, "%Y-%m-%dT%H:%M:%S")
                if last_use_date <= datetime.now():
                    if i < 5:
                        # Wait at least 5 seconds between 2 light sync
                        # TODO optimize this
                        time.sleep(5 - i)
                    i = 300
                    break
            time.sleep(1)

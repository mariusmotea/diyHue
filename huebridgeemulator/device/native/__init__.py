"""Base functions for Native lights."""
from subprocess import check_output

import requests

from huebridgeemulator.tools import get_ip_address
from huebridgeemulator.logger import scan_logger
from huebridgeemulator.device.native.light import NativeLight, NativeLightAddress
from huebridgeemulator.device.light import LightState
from huebridgeemulator.const import LIGHT_TYPES


def discover_native(registry):  # pylint: disable=W0613
    """Discover Native lights on your local network.

    .. todo:: need to be recoded
    """
    # TODO remove the checkout and find a better way to scan ll 80 TCP port opened
    # What happends if we are not in a /24 network ??
    current_ip = get_ip_address()
    command = "nmap {}/24 -p80 --open -n | grep report | cut -d ' ' -f5".format(current_ip)
    device_ips = check_output(command, shell=True).decode('utf-8').split("\n")
    scan_logger.debug(device_ips)
    # delete last empty element in list
    del device_ips[-1]
    # Delete our own ip
    if current_ip in device_ips:
        del current_ip
    # Parse result
    for light_ip in device_ips:
        try:
            url = "http://{}/detect".format(light_ip)
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                device_data = response.json()
                scan_logger.debug(device_data)
                if "hue" in device_data:
                    scan_logger.debug("{} is a hue {}".format(light_ip, device_data['hue']))
                    device_exist = False
                    for light in registry.lights.values():
                        if light.uniqueid.startswith(device_data["mac"]):
                            device_exist = True
                            light.address.ip = light_ip
                    if not device_exist:
                        light_name = "Hue {} {}".format(device_data["hue"],
                                                        device_data["modelid"])
                        if "name" in device_data:
                            light_name = device_data["name"]
                        scan_logger.debug("Add new light: {}", light_name)
                        for index in range(1, int(device_data["lights"]) + 1):
                            # State
                            state = LightState(LIGHT_TYPES[device_data["modelid"]]["state"])
                            # Address
                            address = NativeLightAddress({"ip": light_ip,
                                                          "light_nr": index,
                                                          "protocol": "native"})
                            # Name
                            if index == 1:
                                name = light_name
                            else:
                                name = "{} {}".format(light_name, str(index))
                            # SW version
                            swversion = LIGHT_TYPES[device_data["modelid"]]["swversion"]
                            # Finalize light data
                            data = {"state": state,
                                    "type": LIGHT_TYPES[device_data["modelid"]]["type"],
                                    "address": address,
                                    "name": name,
                                    "uniqueid": device_data["mac"] + "-" + str(index),
                                    "modelid": device_data["modelid"],
                                    "manufacturername": "Philips",
                                    "swversion": swversion}
                            # New light
                            new_light = NativeLight(data)
                            registry.lights[new_light.index] = new_light
                            registry.add_new_light(new_light)
        except Exception:  # pylint: disable=W0703
            scan_logger.debug("ip {} is unknow device".format(light_ip))

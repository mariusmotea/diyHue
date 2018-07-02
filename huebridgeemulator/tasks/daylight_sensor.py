"""???

.. todo:: Add description and some comments
"""
from datetime import datetime
import time
from astral import Astral, Location

from huebridgeemulator.tools import rulesProcessor
from huebridgeemulator.logger import daylight_logger


def daylight_sensor(conf_obj, sensors_state):
    """???

    .. todo:: Add description and some comments
    """
    bridge_config = conf_obj.bridge
    if bridge_config["sensors"]["1"]["modelid"] != "PHDL00" or \
    not bridge_config["sensors"]["1"]["config"]["configured"]:
        return

    astral = Astral()
    astral.solar_depression = 'civil'
    loc = Location(('Current',
                    bridge_config["config"]["timezone"].split("/")[1],
                    float(bridge_config["sensors"]["1"]["config"]["lat"][:-1]),
                    float(bridge_config["sensors"]["1"]["config"]["long"][:-1]),
                    bridge_config["config"]["timezone"], 0))
    sun = loc.sun(date=datetime.now(), local=True)
    delta_sunset = sun['sunset'].replace(tzinfo=None) - datetime.now()
    delta_sunrise = sun['sunrise'].replace(tzinfo=None) - datetime.now()
    delta_sunset_offset = delta_sunset.total_seconds() + \
                          bridge_config["sensors"]["1"]["config"]["sunsetoffset"] * 60
    delta_sunrise_offset = delta_sunrise.total_seconds() + \
                           bridge_config["sensors"]["1"]["config"]["sunriseoffset"] * 60
    daylight_logger.debug("delta_sunset_offset: " + str(delta_sunset_offset))
    daylight_logger.debug("delta_sunrise_offset: " + str(delta_sunrise_offset))
    if delta_sunset_offset > 0 and delta_sunset_offset < 3600:
        daylight_logger.debug("will start the sleep for sunset")
        time.sleep(delta_sunset_offset)
        current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        bridge_config["sensors"]["1"]["state"] = {"daylight":False, "lastupdated": current_time}
        sensors_state["1"]["state"]["daylight"] = current_time
        rulesProcessor("1", current_time)
    if delta_sunrise_offset > 0 and delta_sunrise_offset < 3600:
        daylight_logger.debug("will start the sleep for sunrise")
        time.sleep(delta_sunset_offset)
        current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        bridge_config["sensors"]["1"]["state"] = {"daylight":True, "lastupdated": current_time}
        sensors_state["1"]["state"]["daylight"] = current_time
        rulesProcessor("1", current_time)

import socket
import time
import json
import smtplib
from threading import Thread
from datetime import datetime

import requests

from huebridgeemulator.logger import rule_logger


def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]


def send_email(triggered_sensor):
    TEXT = "Sensor " + triggered_sensor + " was triggered while the alarm is active"
    # Prepare actual message
    message = """From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (bridge_config["alarm_config"]["mail_from"], ", ".join(bridge_config["alarm_config"]["mail_recipients"]), bridge_config["alarm_config"]["mail_subject"], TEXT)
    try:
        server_ssl = smtplib.SMTP_SSL(bridge_config["alarm_config"]["smtp_server"], bridge_config["alarm_config"]["smtp_port"])
        server_ssl.ehlo() # optional, called by login()
        server_ssl.login(bridge_config["alarm_config"]["mail_username"], bridge_config["alarm_config"]["mail_password"])
        server_ssl.sendmail(bridge_config["alarm_config"]["mail_from"], bridge_config["alarm_config"]["mail_recipients"], message)
        server_ssl.close()
        print("successfully sent the mail")
        return True
    except:
        print("failed to send mail")
        return False


def rules_processor(registry, sensor, current_time=datetime.now().strftime("%Y-%m-%dT%H:%M:%S")):
    registry.config["localtime"] = current_time #required for operator dx to address /config/localtime
    actionsToExecute = []
    for rule in registry.rules.keys():
        if registry.rules[rule]["status"] == "enabled":
            rule_result = _check_rule_conditions(rule, sensor, current_time)
            if rule_result[0]:
                if rule_result[1] == 0: #is not ddx rule
                    rule_logger.debug("rule %s is triggered", rule)
                    registry.rules[rule]["lasttriggered"] = current_time
                    registry.rules[rule]["timestriggered"] += 1
                    for action in registry.rules[rule]["actions"]:
                        actionsToExecute.append(action)
                else: #if ddx rule
                    rule_logger.debug("ddx rule {} will be re validated after {} seconds",
                                      rule, str(rule_result[1]))
                    Thread(target=_ddx_recheck, args=[registry, rule, sensor, current_time,
                                                      rule_result[1], rule_result[2]]).start()
    for action in actionsToExecute:
        url = "/api/{}".format(list(bridge_config["config"]["whitelist"])[0] + action["address"])
        method = action["method"].lower()
        if method in ("put", "post"):
            getattr(requests, method)(url, data=action["body"])
        elif method in ("get", "delete"):
            getattr(requests, method)(url, params=action["body"])
        else:
            raise Exception

def _check_rule_conditions(registry, rule, sensor, current_time, ignore_ddx=False):
    ddx = 0
    sensor_found = False
    ddx_sensor = []
    for condition in registry.rules[rule]["conditions"]:
        url_pices = condition["address"].split('/')
        if url_pices[1] == "sensors" and sensor == url_pices[2]:
            sensor_found = True
        # TODO refactoring
        if condition["operator"] == "eq":
            if condition["value"] == "true":
                if not bridge_config[url_pices[1]][url_pices[2]][url_pices[3]][url_pices[4]]:
                    return [False, 0]
            elif condition["value"] == "false":
                if bridge_config[url_pices[1]][url_pices[2]][url_pices[3]][url_pices[4]]:
                    return [False, 0]
            else:
                if not int(bridge_config[url_pices[1]][url_pices[2]][url_pices[3]][url_pices[4]]) == int(condition["value"]):
                    return [False, 0]
        elif condition["operator"] == "gt":
            if not int(bridge_config[url_pices[1]][url_pices[2]][url_pices[3]][url_pices[4]]) > int(condition["value"]):
                return [False, 0]
        elif condition["operator"] == "lt":
            if not int(bridge_config[url_pices[1]][url_pices[2]][url_pices[3]][url_pices[4]]) < int(condition["value"]):
                return [False, 0]
        elif condition["operator"] == "dx":
            if not sensors_state[url_pices[2]][url_pices[3]][url_pices[4]] == current_time:
                return [False, 0]
        elif condition["operator"] == "in":
            periods = condition["value"].split('/')
            if condition["value"][0] == "T":
                time_start = datetime.strptime(periods[0], "T%H:%M:%S").time()
                time_end = datetime.strptime(periods[1], "T%H:%M:%S").time()
                now_time = datetime.now().time()
                if time_start < time_end:
                    if not time_start <= now_time <= time_end:
                        return [False, 0]
                else:
                    if not (time_start <= now_time or now_time <= time_end):
                        return [False, 0]
        elif condition["operator"] == "ddx" and ignore_ddx is False:
            if not sensors_state[url_pices[2]][url_pices[3]][url_pices[4]] == current_time:
                    return [False, 0]
            else:
                ddx = int(condition["value"][2:4]) * 3600 + int(condition["value"][5:7]) * 60 + int(condition["value"][-2:])
                ddx_sensor = url_pices


    if sensor_found:
        return [True, ddx, ddx_sensor]
    return [False]


def _ddx_recheck(registry, rule, sensor, current_time, ddx_delay, ddx_sensor):
    """???

    .. todo:: need sensors_state dict
    """
    for delay in range(ddx_delay):
        if current_time != sensors_state[ddx_sensor[2]][ddx_sensor[3]][ddx_sensor[4]]:
            print("ddx rule " + rule + " canceled after " + str(delay) + " seconds")
            # rule not valid anymore because sensor state changed while waiting for ddx delay
            return
        time.sleep(1)
    current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    rule_state = _check_rule_conditions(registry, rule, sensor, current_time, True)
    if rule_state[0]: #if all conditions are meet again
        print("delayed rule " + rule + " is triggered")
        registry.rules[rule]["lasttriggered"] = current_time
        registry.rules[rule]["timestriggered"] += 1
        for action in registry.rules[rule]["actions"]:
            url = "/api/{}{}".format(registry.rules[rule]["owner"],
                                     action["address"])
            method = action["method"].lower()
            if method in ("put", "post"):
                getattr(requests, method)(url, data=action["body"])
            elif method in ("get", "delete"):
                getattr(requests, method)(url, params=action["body"])

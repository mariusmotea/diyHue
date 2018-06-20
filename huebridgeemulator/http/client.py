import requests
import json
import time

from huebridgeemulator.device.yeelight import sendToYeelight


def sendRequest(url, method, data, timeout=3, delay=0):
    if delay != 0:
        time.sleep(delay)
    if not url.startswith( 'http://' ):
        url = "http://127.0.0.1" + url
    head = {"Content-type": "application/json"}
    if method == "POST":
        response = requests.post(url, data=bytes(data, "utf8"), timeout=timeout, headers=head)
        return response.text
    elif method == "PUT":
        response = requests.put(url, data=bytes(data, "utf8"), timeout=timeout, headers=head)
        return response.text
    elif method == "GET":
        response = requests.get(url, timeout=timeout, headers=head)
        return response.text
    elif method == "TCP":
        if "//" in url: # cutting out the http://
            http, url = url.split("//",1)
        # yeelight uses different functions for each action, so it has to check for each function
        # see page 9 http://www.yeelight.com/download/Yeelight_Inter-Operation_Spec.pdf
        # check if hue wants to change brightness
        for key, value in json.loads(data).items():
            sendToYeelight(url, key, value)

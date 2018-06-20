import json
import socket

from huebridgeemulator.device.light import Light, LightState, LightAddress
from huebridgeemulator.tools.colors import convert_xy


class YeelightLight(Light):

    def __init__(self, index, type, name, uniqueid, modelid, manufacturername, swversion, state, address):
        Light.__init__(self, index, type, name, uniqueid, modelid, "yeelight", swversion, state, address)

    def send_request(self, data):
        payload = {}
        transitiontime = 400
        if "transitiontime" in data:
            transitiontime = data["transitiontime"] * 100
        for key, value in data.items():
            if key == "on":
                if value:
                    payload["set_power"] = ["on", "smooth", transitiontime]
                else:
                    payload["set_power"] = ["off", "smooth", transitiontime]
            elif key == "bri":
                payload["set_bright"] = [int(value / 2.55) + 1, "smooth", transitiontime]
            elif key == "ct":
                payload["set_ct_abx"] = [int(1000000 / value), "smooth", transitiontime]
            elif key == "hue":
                payload["set_hsv"] = [int(value / 182), int(self.state.sat / 2.54), "smooth", transitiontime]
            elif key == "sat":
                payload["set_hsv"] = [int(value / 2.54), int(self.state.hue / 2.54), "smooth", transitiontime]
            elif key == "xy":
                color = convert_xy(value[0], value[1], self.state.bri)
                payload["set_rgb"] = [(color[0] * 65536) + (color[1] * 256) + color[2], "smooth", transitiontime] #according to docs, yeelight needs this to set rgb. its r * 65536 + g * 256 + b
            elif key == "alert" and value != "none":
                payload["start_cf"] = [ 4, 0, "1000, 2, 5500, 100, 1000, 2, 5500, 1, 1000, 2, 5500, 100, 1000, 2, 5500, 1"]

        # yeelight uses different functions for each action, so it has to check for each function
        # see page 9 http://www.yeelight.com/download/Yeelight_Inter-Operation_Spec.pdf
        # check if hue wants to change brightness
        for api_method, param in payload.items():
            try:
                tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                tcp_socket.settimeout(5)
                tcp_socket.connect((self.address.ip, int(55443)))
                msg = json.dumps({"id": 1, "method": api_method, "params": param}) + "\r\n"
                tcp_socket.send(msg.encode())
                tcp_socket.close()
            except Exception as e:
                raise e
                print ("Unexpected error:", e)

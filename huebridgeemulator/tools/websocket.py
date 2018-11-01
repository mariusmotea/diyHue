from datetime import datetime
import json
from threading import Thread

from huebridgeemulator.tools import send_email, rules_processor


def websocketClient():
    from ws4py.client.threadedclient import WebSocketClient
    class EchoClient(WebSocketClient):
        def opened(self):
            self.send("hello")

        def closed(self, code, reason=None):
            print(("deconz websocket disconnected", code, reason))
            del bridge_config["deconz"]["websocketport"]

        def received_message(self, m):
            print(m)
            message = json.loads(str(m))
            try:
                if message["r"] == "sensors":
                    bridge_sensor_id = bridge_config["deconz"]["sensors"][message["id"]]["bridgeid"]
                    if "state" in message and bridge_config["sensors"][bridge_sensor_id]["config"]["on"]:

                        #change codes for emulated hue Switches
                        if "hueType" in bridge_config["deconz"]["sensors"][message["id"]]:
                            rewriteDict = {"ZGPSwitch": {1002: 34, 3002: 16, 4002: 17, 5002: 18}, "ZLLSwitch" : {1002 : 1000, 2002: 2000, 2001: 2001, 2003: 2002, 3001: 3001, 3002: 3000, 3003: 3002, 4002: 4000, 5002: 4000} }
                            message["state"]["buttonevent"] = rewriteDict[bridge_config["deconz"]["sensors"][message["id"]]["hueType"]][message["state"]["buttonevent"]]
                        #end change codes for emulated hue Switches

                        #convert tradfri motion sensor notification to look like Hue Motion Sensor
                        if message["state"] and bridge_config["deconz"]["sensors"][message["id"]]["modelid"] == "TRADFRI motion sensor":
                            #find the light sensor id
                            light_sensor = "0"
                            for sensor in bridge_config["sensors"].keys():
                                if bridge_config["sensors"][sensor]["type"] == "ZLLLightLevel" and bridge_config["sensors"][sensor]["uniqueid"] == bridge_config["sensors"][bridge_sensor_id]["uniqueid"][:-1] + "0":
                                    light_sensor = sensor
                                    break
                            if message["state"]["dark"]:
                                bridge_config["sensors"][light_sensor]["state"]["lightlevel"] = 6000
                            else:
                                bridge_config["sensors"][light_sensor]["state"]["lightlevel"] = 25000
                            if message["state"]["dark"] and not bridge_config["sensors"][light_sensor]["state"]["dark"]:
                                sensors_state[light_sensor]["state"]["dark"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                            bridge_config["sensors"][light_sensor]["state"]["dark"] = message["state"]["dark"]
                            bridge_config["sensors"][light_sensor]["state"]["daylight"] = not message["state"]["dark"]
                            bridge_config["sensors"][light_sensor]["state"]["lastupdated"] = message["state"]["lastupdated"]

                        #convert xiaomi motion sensor to hue sensor
                        if message["state"] and bridge_config["deconz"]["sensors"][message["id"]]["modelid"] == "lumi.sensor_motion.aq2" and message["state"] and bridge_config["deconz"]["sensors"][message["id"]]["type"] == "ZHALightLevel":
                            bridge_config["sensors"][bridge_sensor_id]["state"].update(message["state"])
                            return
                        ##############

                        bridge_config["sensors"][bridge_sensor_id]["state"].update(message["state"])
                        current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                        for key in message["state"].keys():
                            sensors_state[bridge_sensor_id]["state"][key] = current_time
                        rules_processor(bridge_sensor_id, current_time)
                        if "buttonevent" in message["state"] and bridge_config["sensors"][bridge_sensor_id]["modelid"] in ["TRADFRI remote control","RWL021"]:
                            if message["state"]["buttonevent"] in [2001, 3001, 4001, 5001]:
                                Thread(target=longPressButton, args=[bridge_sensor_id, message["state"]["buttonevent"]]).start()
                        if "presence" in message["state"] and message["state"]["presence"] and "virtual_light" in bridge_config["alarm_config"] and bridge_config["lights"][bridge_config["alarm_config"]["virtual_light"]]["state"]["on"]:
                            send_email(bridge_config["sensors"][bridge_sensor_id]["name"])
                            bridge_config["alarm_config"]["virtual_light"]
                    elif "config" in message and bridge_config["sensors"][bridge_sensor_id]["config"]["on"]:
                        bridge_config["sensors"][bridge_sensor_id]["config"].update(message["config"])
                elif message["r"] == "lights":
                    bridge_light_id = bridge_config["deconz"]["lights"][message["id"]]["bridgeid"]
                    if "state" in message:
                        bridge_config["lights"][bridge_light_id]["state"].update(message["state"])
                        updateGroupStats(bridge_light_id)
            except Exception as e:
                print("unable to process the request" + str(e))

    try:
        ws = EchoClient('ws://127.0.0.1:' + str(bridge_config["deconz"]["websocketport"]))
        ws.connect()
        ws.run_forever()
    except KeyboardInterrupt:
        ws.close()

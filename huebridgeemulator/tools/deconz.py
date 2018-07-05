from threading import Thread


def scanDeconz(registry):
    if not registry.deconz["enabled"]:
        if "username" not in registry.deconz:
            try:
                registration = json.loads(sendRequest("http://127.0.0.1:" + str(registry.deconz["port"]) + "/api", "POST", "{\"username\": \"283145a4e198cc6535\", \"devicetype\":\"Hue Emulator\"}"))
            except:
                print("registration fail, is the link button pressed?")
                return
            if "success" in registration[0]:
                registry.deconz["username"] = registration[0]["success"]["username"]
                registry.deconz["enabled"] = True
    if "username" in registry.deconz:
        deconz_config = json.loads(sendRequest("http://127.0.0.1:" + str(registry.deconz["port"]) + "/api/" + registry.deconz["username"] + "/config", "GET", "{}"))
        registry.deconz["websocketport"] = deconz_config["websocketport"]

        #lights
        deconz_lights = json.loads(sendRequest("http://127.0.0.1:" + str(registry.deconz["port"]) + "/api/" + registry.deconz["username"] + "/lights", "GET", "{}"))
        for light in deconz_lights:
            if light not in registry.deconz["lights"]:
                new_light_id = nextFreeId("lights")
                print("register new light " + new_light_id)
                bridge_config["lights"][new_light_id] = deconz_lights[light]
                bridge_config["lights_address"][new_light_id] = {"username": registry.deconz["username"], "light_id": light, "ip": "127.0.0.1:" + str(registry.deconz["port"]), "protocol": "deconz"}
                registry.deconz["lights"][light] = {"bridgeid": new_light_id}
            else: #temporary patch for config compatibility with new release
                registry.deconz["lights"][light]["modelid"] = deconz_lights[light]["modelid"]
                registry.deconz["lights"][light]["type"] = deconz_lights[light]["type"]



        #sensors
        deconz_sensors = json.loads(sendRequest("http://127.0.0.1:" + str(registry.deconz["port"]) + "/api/" + registry.deconz["username"] + "/sensors", "GET", "{}"))
        for sensor in deconz_sensors:
            if sensor not in registry.deconz["sensors"]:
                new_sensor_id = nextFreeId("sensors")
                if deconz_sensors[sensor]["modelid"] in ["TRADFRI remote control", "TRADFRI wireless dimmer"]:
                    print("register new " + deconz_sensors[sensor]["modelid"])
                    bridge_config["sensors"][new_sensor_id] = {"config": deconz_sensors[sensor]["config"], "manufacturername": deconz_sensors[sensor]["manufacturername"], "modelid": deconz_sensors[sensor]["modelid"], "name": deconz_sensors[sensor]["name"], "state": deconz_sensors[sensor]["state"], "swversion": deconz_sensors[sensor]["swversion"], "type": deconz_sensors[sensor]["type"], "uniqueid": deconz_sensors[sensor]["uniqueid"]}
                    registry.deconz["sensors"][sensor] = {"bridgeid": new_sensor_id, "modelid": deconz_sensors[sensor]["modelid"]}
                elif deconz_sensors[sensor]["modelid"] == "TRADFRI motion sensor":
                    print("register TRADFRI motion sensor as Philips Motion Sensor")
                    newMotionSensorId = addHueMotionSensor("")
                    registry.deconz["sensors"][sensor] = {"bridgeid": newMotionSensorId, "triggered": False, "modelid": deconz_sensors[sensor]["modelid"]}

                elif deconz_sensors[sensor]["modelid"] == "lumi.sensor_motion.aq2":
                    if deconz_sensors[sensor]["type"] == "ZHALightLevel":
                        print("register new Xiaomi light sensor")
                        bridge_config["sensors"][new_sensor_id] = {"name": "Hue ambient light sensor 1", "uniqueid": "00:17:88:01:02:" + deconz_sensors[sensor]["uniqueid"][12:], "type": "ZLLLightLevel", "swversion": "6.1.0.18912", "state": {"dark": True, "daylight": False, "lightlevel": 6000, "lastupdated": "none"}, "manufacturername": "Philips", "config": {"on": False,"battery": 100, "reachable": True, "alert": "none", "tholddark": 21597, "tholdoffset": 7000, "ledindication": False, "usertest": False, "pending": []}, "modelid": "SML001"}
                        bridge_config["sensors"][str(int(new_sensor_id) + 1)] = {"name": "Hue temperature sensor 1", "uniqueid": "00:17:88:01:02:" + deconz_sensors[sensor]["uniqueid"][12:-1] + "2", "type": "ZLLTemperature", "swversion": "6.1.0.18912", "state": {"temperature": None, "lastupdated": "none"}, "manufacturername": "Philips", "config": {"on": False, "battery": 100, "reachable": True, "alert":"none", "ledindication": False, "usertest": False, "pending": []}, "modelid": "SML001"}
                        registry.deconz["sensors"][sensor] = {"bridgeid": new_sensor_id}
                    elif deconz_sensors[sensor]["type"] == "ZHAPresence":
                        print("register new Xiaomi motion sensor")
                        bridge_config["sensors"][new_sensor_id] = {"name": "Entrance Lights sensor", "uniqueid": "00:17:88:01:02:" + deconz_sensors[sensor]["uniqueid"][12:], "type": "ZLLPresence", "swversion": "6.1.0.18912", "state": {"lastupdated": "none", "presence": None}, "manufacturername": "Philips", "config": {"on": False,"battery": 100,"reachable": True, "alert": "lselect", "ledindication": False, "usertest": False, "sensitivity": 2, "sensitivitymax": 2,"pending": []}, "modelid": "SML001"}
                        registry.deconz["sensors"][sensor] = {"bridgeid": new_sensor_id}
                else:
                    bridge_config["sensors"][new_sensor_id] = deconz_sensors[sensor]
                    registry.deconz["sensors"][sensor] = {"bridgeid": new_sensor_id}
            else: #temporary patch for config compatibility with new release
                registry.deconz["sensors"][sensor]["modelid"] = deconz_sensors[sensor]["modelid"]
                registry.deconz["sensors"][sensor]["type"] = deconz_sensors[sensor]["type"]
        generateSensorsState()

        if "websocketport" in registry.deconz:
            print("Starting deconz websocket")
            Thread(target=websocketClient).start()

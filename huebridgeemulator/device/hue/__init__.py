def addHueMotionSensor(uniqueid):
    new_sensor_id = nextFreeId("sensors")
    if uniqueid == "":
        if len(new_sensor_id) == 1:
            uniqueid = "0" + new_sensor_id + ":0f:12:23:34:45"
        else:
            uniqueid = new_sensor_id + ":0f:12:23:34:45"
    bridge_config["sensors"][new_sensor_id] = {"name": "Hue temperature sensor 1", "uniqueid": uniqueid + ":56:d0:5b-02-0402", "type": "ZLLTemperature", "swversion": "6.1.0.18912", "state": {"temperature": None, "lastupdated": "none"}, "manufacturername": "Philips", "config": {"on": False, "battery": 100, "reachable": True, "alert":"none", "ledindication": False, "usertest": False, "pending": []}, "modelid": "SML001"}
    bridge_config["sensors"][str(int(new_sensor_id) + 1)] = {"name": "Entrance Lights sensor", "uniqueid": uniqueid + ":56:d0:5b-02-0406", "type": "ZLLPresence", "swversion": "6.1.0.18912", "state": {"lastupdated": "none", "presence": None}, "manufacturername": "Philips", "config": {"on": False,"battery": 100,"reachable": True, "alert": "lselect", "ledindication": False, "usertest": False, "sensitivity": 2, "sensitivitymax": 2,"pending": []}, "modelid": "SML001"}
    bridge_config["sensors"][str(int(new_sensor_id) + 2)] = {"name": "Hue ambient light sensor 1", "uniqueid": uniqueid + ":56:d0:5b-02-0400", "type": "ZLLLightLevel", "swversion": "6.1.0.18912", "state": {"dark": True, "daylight": False, "lightlevel": 6000, "lastupdated": "none"}, "manufacturername": "Philips", "config": {"on": False,"battery": 100, "reachable": True, "alert": "none", "tholddark": 21597, "tholdoffset": 7000, "ledindication": False, "usertest": False, "pending": []}, "modelid": "SML001"}
    return(str(int(new_sensor_id) + 1))


def addHueSwitch(uniqueid, sensorsType):
    new_sensor_id = nextFreeId("sensors")
    if uniqueid == "":
        uniqueid = "00:00:00:00:00:40:" + new_sensor_id + ":83-f2"
    bridge_config["sensors"][new_sensor_id] = {"state": {"buttonevent": 0, "lastupdated": "none"}, "config": {"on": True, "battery": 100, "reachable": True}, "name": "Dimmer Switch" if sensorsType == "ZLLSwitch" else "Tap Switch", "type": sensorsType, "modelid": "RWL021" if sensorsType == "ZLLSwitch" else "ZGPSWITCH", "manufacturername": "Philips", "swversion": "5.45.1.17846" if sensorsType == "ZLLSwitch" else "", "uniqueid": uniqueid}
    return(new_sensor_id)


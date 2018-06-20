import sys
import json

def loadConfig(filename):  #load and configure alarm virtual light
    #load config files
    try:
        with open(filename, 'r') as fp:
            bridge_config = json.load(fp)
            print("Config loaded")
    except Exception as exp:
        print("CRITICAL! Config file was not loaded: %s" % exp)
        sys.exit(1)

    if bridge_config["alarm_config"]["mail_username"] != "":
        print("E-mail account configured")
        if "virtual_light" not in bridge_config["alarm_config"]:
            print("Send test email")
            if sendEmail("dummy test"):
                print("Mail succesfully sent\nCreate alarm virtual light")
                new_light_id = nextFreeId("lights")
                bridge_config["lights"][new_light_id] = {"state": {"on": False, "bri": 200, "hue": 0, "sat": 0, "xy": [0.690456, 0.295907], "ct": 461, "alert": "none", "effect": "none", "colormode": "xy", "reachable": True}, "type": "Extended color light", "name": "Alarm", "uniqueid": "1234567ffffff", "modelid": "LLC012", "swversion": "66009461"}
                bridge_config["alarm_config"]["virtual_light"] = new_light_id
            else:
                print("Mail test failed")
    return bridge_config

def saveConfig(filename, bridge_config):
    with open(filename, 'w') as fp:
        json.dump(bridge_config, fp, sort_keys=True, indent=4, separators=(',', ': '))



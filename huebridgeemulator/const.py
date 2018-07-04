import pytz
import time


RESOURCE_TYPES = [
  "alarm_config",
  "capabilities",
  "config",
  "deconz",
  "groups",
  "lights",
  "lights_address",
  "linkbutton",
  "resourcelinks",
  "rules",
  "scenes",
  "schedules",
  "sensors"
]


LIGHT_TYPES = {
    "LCT015": {
        "state": {
            "on": False,
            "bri": 200,
            "hue": 0,
            "sat": 0,
            "xy": [0.0, 0.0],
            "ct": 461,
            "alert": "none",
            "effect": "none",
            "colormode": "ct",
            "reachable": True
        },
        "type": "Extended color light",
        "swversion": "1.29.0_r21169"
    },
    "LST001": {
        "state": {
            "on": False,
            "bri": 200,
            "hue": 0,
            "sat": 0,
            "xy": [0.0, 0.0],
            "ct": 461,
            "alert": "none",
            "effect": "none",
            "colormode": "ct",
            "reachable": True
        },
        "type": "Color light",
        "swversion": "66010400"
    },
    "LWB010": {
        "state": {
            "on": False,
            "bri": 254,
            "alert": "none",
            "reachable": True
        },
        "type": "Dimmable light",
        "swversion": "1.15.0_r18729"
    },
    "LTW001": {
        "state": {
            "on": False,
            "colormode": "ct",
            "alert": "none",
            "reachable": True,
            "bri": 254,
            "ct": 230},
        "type": "Color temperature light",
        "swversion": "5.50.1.19085"
    },
    "Plug 01": {
        "state": {
            "on": False,
            "alert": "none",
            "reachable": True
        },
        "type": "On/Off plug-in unit",
        "swversion": "V1.04.12"
    }
}

# TODO should we transform this to a class ?
REGISTRY_ALARM_CONFIG = {
    "mail_from": "your_email@gmail.com",
    "mail_password": "",
    "mail_recipients": [
        "first_recipient@mail.com",
        "second_recipient@mail.com"
    ],
    "mail_subject": "HUE ALARM TRIGGERED!",
    "mail_username": "",
    "smtp_port": 465,
    "smtp_server": "smtp.gmail.com"
}

REGISTRY_CAPABILITIES = {
  "groups": {
    "available": 64
  },
  "lights": {
    "available": 63
  },
  "resourcelinks": {
    "available": 64
  },
  "rules": {
    "actions": {
      "available": 400
    },
    "available": 200,
    "conditions": {
      "available": 400
    }
  },
  "scenes": {
    "available": 200,
    "lightstates": {
      "available": 2048
    }
  },
  "schedules": {
    "available": 100
  },
  "sensors": {
    "available": 63,
    "clip": {
      "available": 63
    },
    "zgp": {
      "available": 63
    },
    "zll": {
      "available": 63
    }
  },
  "timezones": pytz.all_timezones,
}

REGISTRY_BASE_CONFIG = {
    "name": "Philips hue",
    "zigbeechannel": 25,
    # bridgeid":"001788FFFE29864E",
    # mac":"00:17:88:29:85:3e",
    "dhcp": True,
    # "ipaddress":"192.168.10.11",
    # "netmask":"255.255.255.0",
    # "gateway":"192.168.10.1",
    "proxyaddress": "none",
    "proxyport": 0,
    "UTC": "2018-06-09T18:03:20",
    "localtime": "2018-06-09T21:03:20",
    # "timezone":"Europe/Bucharest",
    "modelid": "BSB002",
    "datastoreversion": "70",
    "swversion": "1802201122",
    "apiversion": "1.24.0",
    "swupdate": {
        "updatestate": 0,
        "checkforupdate": False,
        "devicetypes": {
            "bridge": False,
            "lights": [],
            "sensors": []
        },
        "url": "",
        "text": "",
        "notify": True
    },
    "swupdate2": {
        "checkforupdate": False,
        "lastchange": "2018-06-09T10:11:08",
        "bridge": {
            "state": "noupdates",
            "lastinstall": "2018-06-08T19:09:45"
        },
        "state": "noupdates",
        "autoinstall": {
            "updatetime": "T14:00:00",
            "on": False
        }
    },
    "linkbutton": False,
    "portalservices": True,
    "portalconnection": "connected",
    "portalstate": {
        "signedon": True,
        "incoming": False,
        "outgoing": True,
        "communication": "disconnected"
    },
    "internetservices": {
        "internet": "connected",
        "remoteaccess": "connected",
        "time": "connected",
        "swupdate": "connected"
    },
    "factorynew": False,
    "replacesbridgeid": None,
    "backup": {
        "status": "idle",
        "errorcode": 0
    },
    "starterkitid": "",
    "whitelist": {}
}

REGISTRY_DECONZ = {
    "enabled": False,
    "lights": {},
    "port": 8080,
    "sensors": {}
}

REGISTRY_LINKBUTTON = {
    "lastlinkbuttonpushed": int(time.time()),
    # TODO what is this stuff ???
    "linkbutton_auth": "SHVlOkh1ZQ==",
}


import json



class Light(object):

    def __init__(self, index, type, name, uniqueid, modelid, manufacturername, swversion, state, address):
        self.index = index
        # ???
        self.type = type
        # name
        self.name = name
        # example: 4a:e0:ad:7f:cf:52-1
        self.uniqueid = uniqueid
        # model id
        self.modelid = modelid
        # Can we use something else ?
        self.manufacturername = manufacturername
        # ???
        self.swversion = swversion
        # address
        self.address = LightAddress(address["id"], address["ip"], "yeelight")
        # state
        self.state = LightState(state)

    def serialize(self):
        ret = {"type": self.type,
               "name": self.name,
               "uniqueid": self.uniqueid,
               "modelid": self.modelid,
               "manufacturername": self.manufacturername,
               "swversion": self.swversion,
               "state": self.state.serialize(),
               }
        return ret

    def toJSON(self):
        return json.dumps(self.serialize())

    def send_request(self, data):
        raise NotImplementedError


class LightState(object):

    def __init__(self, raw_state):
        # ?? (str)
        self.alert = raw_state['alert']
        # Brightness (int)
        self.bri = raw_state['bri']
        # color mode (str)
        self.colormode = raw_state['colormode']
        # ??? (int)
        self.ct = raw_state['ct']
        # effect (str)
        self.effect = raw_state['effect']
        # ??? (int)
        self.hue = raw_state['hue']
        # (bool)
        self.on = raw_state['on']
        # (bool)
        self.reachable = raw_state['reachable']
        # ???
        self.sat = raw_state['sat']
        # list(int, int)
        self.xy = raw_state['xy']

    def serialize(self):
        ret = {"alert": self.alert,
               "bri": self.bri,
               "colormode": self.colormode,
               "ct": self.ct,
               "self.effect": self.effect,
               "hue": self.hue,
               "on": self.on,
               "reachable": self.reachable,
               "sat": self.sat,
               "xy": self.xy,
               }
        return ret

class LightAddress(object):


    def __init__(self, id, ip, protocol):

        # Example: "0x00000000033447b4"
        self.id = id
        # Example: "192.168.2.161",
        self.ip = ip
        # Example: "yeelight"
        self.protocol = protocol

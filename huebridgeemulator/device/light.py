import json



class Light(object):

    def __init__(self, index, address, raw):
        self.index = index
        # address
        self.address = None
        self.set_address(address)
        # state
        self.state = LightState(raw['state'])
        # config
        self.read_config(raw)

        # ???
#        self.type = type
        # name
 #       self.name = name
        # example: 4a:e0:ad:7f:cf:52-1
  #      self.uniqueid = uniqueid
        # model id
   #     self.modelid = modelid
        # Can we use something else ?
    #    self.manufacturername = manufacturername
        # ???
     #   self.swversion = swversion

    def read_config(self, config):
        raise NotImplementedError

    def serialize(self):
        raise NotImplementedError

    def set_address(self, address):
        # address
        raise NotImplementedError

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
        self.effect = raw_state.get('effect')
        # ??? (int)
        self.hue = raw_state.get('hue')
        # (bool)
        self.on = raw_state['on']
        # (bool)
        self.reachable = raw_state['reachable']
        # ???
        self.sat = raw_state.get('sat')
        # list(int, int)
        self.xy = raw_state.get('xy')

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
               }
        if self.xy is not None:
            ret['xy'] = self.xy
        if self.effect is not None:
            ret['effect'] = self.effect
        if self.sat is not None:
            ret['sat'] = self.sat
        return ret

class LightAddress(object):

    def __init__(self, address):
        # Example: "yeelight"
        self.protocol = address["protocol"]

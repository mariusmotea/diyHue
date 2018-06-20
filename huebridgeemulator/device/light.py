


class Light(object):
    pass


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


class LightAddress(object):


    def __init__(self, id, ip, protocol):

        # Example: "0x00000000033447b4"
        self.id = id
        # Example: "192.168.2.161",
        self.ip = ip
        # Example: "yeelight"
        self.protocol = protocol

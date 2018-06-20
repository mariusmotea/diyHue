import json

from huebridgeemulator.device.light import Light, LightState, LightAddress

class YeelightLight(Light):

    def __init__(self, index, type_, name, uniqueid, modelid, manufacturername, swversion, raw_state):
        self.index = index
        # ???
        self.type = type_
        # name
        self.name = name
        # example: 4a:e0:ad:7f:cf:52-1
        self.uniqueid = uniqueid
        # model id
        self.modelid = modelid
        # Can we use something else ?
        self.manufacturername = "Philips"
        # ???
        self.swversion = swversion
        # address
        self.address = LightAddress(None, None, "yeelight")
        # state
        self.state = LightState(raw_state)

    def setState(self, ):
        self.state

    def send_request(self, api_method, param):
        try:
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_socket.settimeout(5)
            tcp_socket.connect((self, url, int(55443)))
            msg = json.dumps({"id": 1, "method": api_method, "params": param}) + "\r\n"
            tcp_socket.send(msg.encode())
            tcp_socket.close()
        except Exception as e:
            raise e
            print ("Unexpected error:", e)


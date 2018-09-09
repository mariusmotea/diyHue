"""Module to handle Yeelight lights."""
import json
from subprocess import check_output

from huebridgeemulator.device.light import Light, LightAddress
from huebridgeemulator.tools.colors import convert_rgb_xy, hsv_to_rgb
# Should we use yeelight python lib ??
# https://www.yeelight.com/download/Yeelight_Inter-Operation_Spec.pdf


class TradfriLight(Light):
    """Tradfri light class."""

    _RESOURCE_TYPE = "lights"
    # TODO
    _MANDATORY_ATTRS = ('address', 'state', 'type', 'name', 'uniqueid',
                        'modelid', 'manufacturername', 'swversion')
    # TODO
    _OPTIONAL_ATTRS = ()

    def set_name(self, name):
        self.name = name
        # TODO
        # self._con.set_name(name)

    def _connect(self):
        pass
        # TODO
        # self._con = ???

    def update_status(self):
        self.logger.debug(self.serialize())
        if self._con is None:
            self._connect()
        # TODO use ikea tradfri python lib
        command_line = ('./coap-client-linux -m get -u "{}" -k "{}" '
                        '"coaps://{}:5684/15001/{}"'.format(
                            self.address.identity,
                            self.address.preshared_key,
                            self.address.ip,
                            self.address.device_id))
        light_data = json.loads(check_output(command_line, shell=True)
                                .decode('utf-8').split("\n")[3])
        self.state.on = bool(light_data["3311"][0]["5850"])
        self.state.bri = light_data["3311"][0]["5851"]
        if "5706" in light_data["3311"][0]:
            if light_data["3311"][0]["5706"] == "f5faf6":
                self.state.ct = 170
            elif light_data["3311"][0]["5706"] == "f1e0b5":
                self.state.ct = 320
            elif light_data["3311"][0]["5706"] == "efd275":
                self.state.ct = 470
        else:
            self.state.ct = 470

    def send_request(self, data):
        if self._con is None:
            self._connect()
        url = "coaps://{}:5684/15001/{}".format(self.address.ip, self.address.device_id)
        payload = {}
        for key, value in data.items():
            if key == "on":
                payload["5850"] = int(value)
            elif key == "transitiontime":
                payload["5712"] = value
            elif key == "bri":
                payload["5851"] = value
            elif key == "ct":
                if value < 270:
                    payload["5706"] = "f5faf6"
                elif value < 385:
                    payload["5706"] = "f1e0b5"
                else:
                    payload["5706"] = "efd275"
            elif key == "xy":
                payload["5709"] = int(value[0] * 65535)
                payload["5710"] = int(value[1] * 65535)
        if "hue" in data or "sat" in data:
            if "hue" in data:
                hue = data["hue"]
            else:
                hue = self.state.hue
            if "sat" in data:
                sat = data["sat"]
            else:
                sat = self.state.sat
            if "bri" in data:
                bri = data["bri"]
            else:
                bri = self.state.bri
            rgb_value = hsv_to_rgb(hue, sat, bri)
            xy_value = convert_rgb_xy(rgb_value[0], rgb_value[1], rgb_value[2])
            payload["5709"] = int(xy_value[0] * 65535)
            payload["5710"] = int(xy_value[1] * 65535)
        if "5850" in payload and payload["5850"] == 0:
            # Setting brightnes will turn on the ligh even if there was a request to power off
            payload.clear()
            payload["5850"] = 0
        elif "5850" in payload and "5851" in payload:
            # When setting brightness don't send also power on command
            del payload["5850"]
        if "5712" not in payload:
            # If no transition add one, might also add check to prevent large transitiontimes
            payload["5712"] = 4
            data = {"3311": [payload]}
            command = ("""./coap-client-linux -m put -u "{}" -k "{}" """
                       """-e '{}' "{}" """.format(self.address.identity,
                                                  self.address.preshared_key,
                                                  json.dumps(data),
                                                  url))
            check_output(command, shell=True)
        # TODO what happening with the else ???


class TradfriLightAddress(LightAddress):
    """Tradfri light address class."""

    protocol = "ikea_tradfri"
    _MANDATORY_ATTRS = ('id', 'ip', 'identity', 'preshared_key')

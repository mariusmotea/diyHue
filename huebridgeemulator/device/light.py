import json

from huebridgeemulator.common import BaseResource, BaseObject, get_dict_key


class Light(BaseResource):

    _RESOURCE_TYPE = "lights"
    _MANDATORY_ATTRS = ('address', 'state')
    _OPTIONAL_ATTRS = ()

    def send_request(self, data):
        raise NotImplementedError

    def update_status(self):
        raise NotImplementedError

    def serialize(self):
        # FIXME should be not different from BaseResource
        ret = BaseResource.serialize(self)
        del(ret['address'])
        return ret

    def set_unreachable(self):
        self.state.reachable = False
        self.state.on = False


class LightState(BaseObject):

    _MANDATORY_ATTRS = ('alert', 'bri', 'colormode', 'ct', 'on', 'reachable')
    _OPTIONAL_ATTRS = ('effect', 'hue', 'sat', 'xy', 'mode')


class LightAddress(BaseObject):

    _MANDATORY_ATTRS = ('ip', )

    def serialize(self):
        ret = {}
        attrs = self._MANDATORY_ATTRS + self._OPTIONAL_ATTRS + ('protocol',)
        for attr in attrs:
            ret[get_dict_key(attr)] = getattr(self, attr)
        return ret

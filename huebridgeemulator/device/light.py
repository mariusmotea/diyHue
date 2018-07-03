import json

from huebridgeemulator.common import BaseResource, BaseObject

class Light(BaseResource):

    _RESOURCE_TYPE = "lights"
    _MANDATORY_ATTRS = ('address', 'state')
    _OPTIONAL_ATTRS = ()

    def __init__(self, raw_data):
        BaseResource.__init__(self, raw_data)

    def send_request(self, data):
        raise NotImplementedError

    def update_status(self):
        raise NotImplementedError

    def serialize(self):
        # FIXME should be not difderent
        ret = BaseResource.serialize(self)
        del(ret['address'])
        return ret

class LightState(BaseObject):

    _MANDATORY_ATTRS = ('alert', 'bri', 'colormode', 'ct', 'on', 'reachable')
    _OPTIONAL_ATTRS = ('effect', 'hue', 'sat', 'xy')


class LightAddress(BaseObject):

    _MANDATORY_ATTRS = ('ip', )

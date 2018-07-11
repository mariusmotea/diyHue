"""Base light module."""
from huebridgeemulator.common import BaseResource, BaseObject, get_dict_key


class Light(BaseResource):
    """Base light class."""

    _RESOURCE_TYPE = "lights"
    _MANDATORY_ATTRS = ('address', 'state')
    _OPTIONAL_ATTRS = ()
    _DEFAULT_DURATION = 400

    def __init__(self, raw_data, index=None):
        BaseResource.__init__(self, raw_data, index)
        self._con = None

    def send_request(self, data):
        """Send request to the device."""
        raise NotImplementedError

    def update_status(self):
        """Get light status."""
        raise NotImplementedError

    def serialize(self):
        # FIXME should be not different from BaseResource
        # Or at least use super
        ret = BaseResource.serialize(self)
        del ret['address']
        return ret

    def set_unreachable(self):
        """Set device unreachable."""
        self.state.reachable = False
        self.state.on = False

    def set_name(self, name):
        """Change light name."""
        raise NotImplementedError

    def _connect(self):
        """Connect to the light and store connection handler
        to `_con` attribute.
        """
        raise NotImplementedError


class LightState(BaseObject):
    """Class containing data about light's state."""

    _MANDATORY_ATTRS = ('on',)
    _OPTIONAL_ATTRS = ('bri', 'effect', 'hue', 'sat', 'xy', 'mode',
                       'alert', 'colormode', 'ct', 'reachable')


class LightAddress(BaseObject):
    """Class containing data to communicate with the light."""

    _MANDATORY_ATTRS = ('ip', )

    def serialize(self):
        ret = {}
        attrs = self._MANDATORY_ATTRS + self._OPTIONAL_ATTRS + ('protocol',)
        for attr in attrs:
            ret[get_dict_key(attr)] = getattr(self, attr)
        return ret

"""Module defining Hue Group/Room classes."""

from huebridgeemulator.common import BaseResource, BaseObject


class ActionGroup(BaseObject):
    """Hue group action class."""

    _MANDATORY_ATTRS = ('on', )
    _OPTIONAL_ATTRS = ('bri', 'ct', 'hue', 'sat', 'xy')


class StateGroup(BaseObject):
    """Hue group state class."""

    _MANDATORY_ATTRS = ('all_on', 'any_on')


class Group(BaseResource):
    """Hue group/room class."""

    _RESOURCE_TYPE = "groups"
    _MANDATORY_ATTRS = ('action', 'class', 'lights', 'name', 'state', 'type')

from huebridgeemulator.common import BaseResource, BaseObject


class ActionGroup(BaseObject):

    _MANDATORY_ATTRS = ('bri', 'ct', 'hue', 'on', 'sat', 'xy')


class ActionState(BaseObject):

    _MANDATORY_ATTRS = ('all_on', 'any_on')


class Group(BaseResource):

    _RESOURCE_TYPE = "groups"
    _MANDATORY_ATTRS = ('action', 'class', 'lights', 'name', 'state', 'type')

from huebridgeemulator.common import BaseResource, BaseObject


class ActionGroup(BaseObject):

    _MANDATORY_ATTRS = ('bri', 'ct', 'hue', 'on', 'sat', 'xy')


class Group(BaseResource):

    _RESOURCE_TYPE = "groups"
    _MANDATORY_ATTRS = ('action', 'class', 'lights', 'name', 'state', 'type')

    def __init__(self):

        self.action = None
        self.class_ = None
        self.lights = []
        self.name = None
        self.state = None
        self.type = None
    




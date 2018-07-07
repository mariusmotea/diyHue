import json
from huebridgeemulator.common import BaseResource, BaseObject


class Scene(BaseResource):

    _RESOURCE_TYPE = "scenes"
    _MANDATORY_ATTRS = ('appdata', 'lastupdated', 'lights', 'lightstates',
                        'locked', 'name', 'owner', 'picture', 'recycle', 'version')

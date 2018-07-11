"""Module defining Hue scene classes."""

from huebridgeemulator.common import BaseResource


class Scene(BaseResource):
    """Hue scene class."""

    _RESOURCE_TYPE = "scenes"
    _MANDATORY_ATTRS = ('appdata', 'lastupdated', 'lights', 'lightstates',
                        'locked', 'name', 'owner', 'picture', 'recycle', 'version')

"""Module defining Hue link button class."""

from huebridgeemulator.common import BaseObject


class LinkButton(BaseObject):
    """Hue Link Button class."""

    _RESOURCE_TYPE = "link_button"
    _MANDATORY_ATTRS = ("lastlinkbuttonpushed", "linkbutton_auth")

from huebridgeemulator.common import BaseObject

class LinkButton(BaseObject):

    _RESOURCE_TYPE = "link_button"
    _MANDATORY_ATTRS = ( "lastlinkbuttonpushed", "linkbutton_auth")

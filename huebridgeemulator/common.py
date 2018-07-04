import json

from huebridgeemulator.logger import main_logger


KEYWORD_OVERRIDE = [('class_', 'class'),
                    ('type_', 'type'),
                    ]
ATTR_TO_KEYWORD = dict([(k[0],k[1]) for k in KEYWORD_OVERRIDE])
KEYWORD_TO_ATTR = dict([(k[1],k[0]) for k in KEYWORD_OVERRIDE])

def get_class_attr(dict_key):
    """Return class attribute name from dict key name.

    This function is made to avoid python keyword utilization
    as attribute name in a hueBridgeEmulator Objects

    >>> get_class_attr('class')
    'class_'
    >>> get_class_attr('toto')
    'toto'
    """
    return KEYWORD_TO_ATTR.get(dict_key, dict_key)

def get_dict_key(class_attr):
    """Return correct dict key from a class attribute name.

    This function is made to avoid python keyword utilization
    as attribute name in a hueBridgeEmulator Objects

    >>> get_dict_key('class_')
    'class'
    >>> get_dict_key('toto')
    'toto'
    """
    return ATTR_TO_KEYWORD.get(class_attr, class_attr)


class BaseObject():

    _MANDATORY_ATTRS = ()
    _OPTIONAL_ATTRS = ()

    def __init__(self, raw_data):
        # Check keys
        for attr in self._MANDATORY_ATTRS:
            if attr not in raw_data:
                raise Exception("Key `{}` missing".format(attr))
            setattr(self, get_class_attr(attr), raw_data[attr])
        for attr in self._OPTIONAL_ATTRS:
            setattr(self, get_class_attr(attr), raw_data.get(attr))

    def serialize(self):
        ret = {}
        attrs = self._MANDATORY_ATTRS + self._OPTIONAL_ATTRS
        for attr in attrs:
            ret[get_dict_key(attr)] = getattr(self, attr)
        return ret

    def toJSON(self):
        return json.dumps(self.serialize)


class BaseResource(BaseObject):

    _RESOURCE_TYPE = None

    def __init__(self, raw_data):
        BaseObject.__init__(self, raw_data)
        if self._RESOURCE_TYPE is None:
            raise Exception("You must define _RESOURCE_TYPE class variable")
        from huebridgeemulator.registry import registry
        self._registry = registry
        self.index = self._registry.nextFreeId(self._RESOURCE_TYPE.lower())
        # logger
        self.logger = main_logger.getChild(self._RESOURCE_TYPE.lower()).getChild(self.index)
        # Add to the registry
        self._registry.add_new_resource(self)

    def serialize(self):
        ret = {}
        keys = self._MANDATORY_ATTRS + self._OPTIONAL_ATTRS
        for key in keys:
            attr = get_class_attr(key)
            if not hasattr(self, attr):
                ret[key] = None
            else:
                if hasattr(getattr(self, attr), 'serialize'):
                    ret[key] = getattr(self, attr).serialize()
                else:
                    ret[key] = getattr(self, attr)
        return ret

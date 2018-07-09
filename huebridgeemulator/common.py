"""HueBridgeEmulator common classes."""

import json

from huebridgeemulator.logger import main_logger


KEYWORD_OVERRIDE = [('class_', 'class'),
                    ('type_', 'type'),
                    ]
ATTR_TO_KEYWORD = dict([(k[0], k[1]) for k in KEYWORD_OVERRIDE])
KEYWORD_TO_ATTR = dict([(k[1], k[0]) for k in KEYWORD_OVERRIDE])


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
    """HueBridgeEmulator base class."""

    _MANDATORY_ATTRS = ()
    _OPTIONAL_ATTRS = ()

    def __init__(self, raw_data):
        # Check mandatory keys
        for attr in self._MANDATORY_ATTRS:
            if attr not in raw_data:
                raise Exception("Key `{}` missing".format(attr))
            setattr(self, get_class_attr(attr), raw_data[attr])
        # Add only existing optional attributes
        for attr in self._OPTIONAL_ATTRS:
            if attr in raw_data:
                setattr(self, get_class_attr(attr), raw_data.get(attr))

    def serialize(self):
        """Serialize the current object.

        :return: current object as dict
        :rtype: dict
        """
        ret = {}
        # Add all mandatory attributes
        for key in self._MANDATORY_ATTRS:
            attr = get_class_attr(key)
            ret[key] = getattr(self, attr)
        # Add only existing optional attributes
        for key in self._OPTIONAL_ATTRS:
            attr = get_class_attr(key)
            if hasattr(self, attr):
                ret[key] = getattr(self, attr)
        return ret

    def to_json(self):
        """Like serialize but return string.

        :return: current object as str
        :rtype: str
        """
        return json.dumps(self.serialize)


class BaseResource(BaseObject):
    """HueBridgeEmulator base class for indexed resources."""

    _RESOURCE_TYPE = None

    def __init__(self, raw_data, index=None):
        BaseObject.__init__(self, raw_data)
        if self._RESOURCE_TYPE is None:
            raise Exception("You must define _RESOURCE_TYPE class variable")
        from huebridgeemulator.registry import registry
        self._registry = registry
        # Set index
        self.index = index
        if self.index is None:
            self.index = self._registry.next_free_id(self._RESOURCE_TYPE.lower())
        # logger
        self.logger = main_logger.getChild(self._RESOURCE_TYPE.lower()).getChild(self.index)

    def serialize(self):
        """Serialize the current object.

        :return: current object as dict
        :rtype: dict
        """
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

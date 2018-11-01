"""Config Hue API module."""
import hug


@hug.get('/api/{uid}/config')
def api_get_config(uid, request, response):  # pylint: disable=W0613
    """Return Hue Configuration."""
    return request.context['registry'].config


@hug.get('/api/node')
@hug.get('/api/config')
@hug.get('/api/nouser')
@hug.get('/api/nouser/config')
def api_get_discover(request, response, output=hug.output_format.html):  # pylint: disable=W0613
    """Used by applications to discover the bridge."""
    print("api_get_discoverapi_get_discoverapi_get_discoverapi_get_discoverapi_get_discover")
    registry = request.context['registry']
    ret= {"name": registry.config["name"],
            "datastoreversion": 73,
            "swversion": registry.config["swversion"],
            "apiversion": registry.config["apiversion"],
            "mac": registry.config["mac"],
            "bridgeid": registry.config["bridgeid"],
            "factorynew": False,
            "replacesbridgeid": None,
            "modelid": registry.config["modelid"],
            "starterkitid":"",
            }
    print(ret)
    return ret
    return '''{"name":"Philips hue","datastoreversion":73,"swversion":"1809121051","apiversion":"1.24.0","mac":"48:5b:39:70:34:aa","bridgeid":"485B39FFFE7034AA","factorynew":false,"replacesbridgeid":null,"modelid":"BSB002","starterkitid":""}'''

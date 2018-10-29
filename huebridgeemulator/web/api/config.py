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
def api_get_discover(request, response):  # pylint: disable=W0613
    """Used by applications to discover the bridge."""
    print("api_get_discoverapi_get_discoverapi_get_discoverapi_get_discoverapi_get_discover")
    registry = request.context['registry']
    print({"name": registry.config["name"],
            "datastoreversion": 59,
            "swversion": registry.config["swversion"],
            "apiversion": registry.config["apiversion"],
            "mac": registry.config["mac"],
            "bridgeid": registry.config["bridgeid"],
            "factorynew": False,
            "modelid": registry.config["modelid"]})
    return {"name": registry.config["name"],
            "datastoreversion": 59,
            "swversion": registry.config["swversion"],
            "apiversion": registry.config["apiversion"],
            "mac": registry.config["mac"],
            "bridgeid": registry.config["bridgeid"],
            "factorynew": False,
            "modelid": registry.config["modelid"]}

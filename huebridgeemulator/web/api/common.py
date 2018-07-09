"""Common Hue API module."""
from datetime import datetime
import hashlib
import hug

from huebridgeemulator.web.templates import get_template
from huebridgeemulator.web.tools import authorized


@hug.get('/description.xml', output=hug.output_format.html)
def hue_description(request, response):
    """Return bridge description."""
    registry = request.context['registry']
    response.set_header('Content-type', 'application/xml')
#    description(bridge_config["config"]["ipaddress"], mac)
    template = get_template('description.xml.j2')
    return template.render({'ip': registry.config["ipaddress"],
                            'mac': registry.config['mac']})


@hug.get('/api/{uid}', requires=authorized)
@hug.get('/api/{uid}/', requires=authorized)
def api_get(uid, request, response):  # pylint: disable=W0613
    """Print entire config."""
    registry = request.context['registry']
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    registry.config["UTC"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    registry.config["localtime"] = now
    registry.config["whitelist"][uid]["last use date"] = now
    return registry.serialize()


@hug.get('/api/{uid}/info/{info}', requires=authorized)
def api_get_info(uid, info, request, response):  # pylint: disable=W0613
    """Registry bridge information."""
    registry = request.context['registry']
    return registry.capabilities[info]


@hug.post('/updater')
def updater(request, response):  # pylint: disable=W0613
    """?????

    ... todo:: code this function
    """
    return {}


@hug.post('/api')
@hug.post('/api/')
def api_post(body, request, response):
    """Register a new client (phone application or other)."""
    registry = request.context['registry']
    response = []
    # new registration by linkbutton
    post_dictionary = body
    if "devicetype" in post_dictionary:
        device_type = post_dictionary["devicetype"][0].encode('utf-8')
        if registry.config["linkbutton"]:  # this must be a new device registration
            #  create new user hash
            username = hashlib.new('ripemd160', device_type).hexdigest()[:32]
            registry.config["whitelist"][username] = {
                "last use date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
                "create date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
                "name": post_dictionary["devicetype"]}
            response = [{"success": {"username": username}}]
            if "generateclientkey" in post_dictionary and post_dictionary["generateclientkey"]:
                response[0]["success"]["clientkey"] = "E3B550C65F78022EFD9E52E28378583"
        elif not registry.config["linkbutton"]:
            now = datetime.now().strftime("%s")
            if int(registry.linkbutton.lastlinkbuttonpushed) + 30 >= int(now):
                username = hashlib.new('ripemd160', device_type).hexdigest()[:32]
                registry.config["whitelist"][username] = {
                    "last use date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
                    "create date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
                    "name": post_dictionary["devicetype"]}
                response = [{"success": {"username": username}}]
                if "generateclientkey" in post_dictionary and post_dictionary["generateclientkey"]:
                    response[0]["success"]["clientkey"] = "E3B550C65F78022EFD9E52E28378583"
            else:
                response = [{"error": {"type": 101,
                                       "address": request.path,
                                       "description": "link button not pressed"}}]

    request.context['conf_obj'].save()
    return response

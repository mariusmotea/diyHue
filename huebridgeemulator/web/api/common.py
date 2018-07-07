from datetime import datetime
from uuid import getnode as get_mac
import hashlib
import random
import json

import requests
import hug
from jinja2 import FileSystemLoader, Environment

from huebridgeemulator.tools import generateSensorsState
from huebridgeemulator.web.templates import get_template
from huebridgeemulator.http.websocket import scanDeconz
from huebridgeemulator.tools.light import scanForLights
from threading import Thread
import time
import huebridgeemulator.web.ui
from huebridgeemulator.web.tools import authorized 


@hug.get('/description.xml',  output=hug.output_format.html)
def hue_description(request, response):
    print("/description.xml/description.xml/description.xml/description.xml/description.xml/description.xml")
    registry = request.context['registry']
    response.set_header('Content-type', 'application/xml')
#    description(bridge_config["config"]["ipaddress"], mac)
    template = get_template('description.xml.j2')
    return template.render({'ip': registry.config["ipaddress"],
                            'mac': registry.config['mac']})


@hug.get('/api/{uid}', requires=authorized)
@hug.get('/api/{uid}/', requires=authorized)
def api_get(uid, request, response):
    """Print entire config."""
    registry = request.context['registry']
    registry.config["UTC"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    registry.config["localtime"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    registry.config["whitelist"][uid]["last use date"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    return registry.serialize()


@hug.get('/api/{uid}/info/{info}', requires=authorized)
def api_get_info(uid, info, request, response):
    print("api_get_groupsapi_get_groupsapi_get_groupsapi_get_groupsapi_get_groupsapi_get_groups")
    registry = request.context['registry']
    return ridge_config["capabilities"][info]


@hug.post('/updater')
def updater(request, response):
    # TODO
    return {}


@hug.post('/api')
@hug.post('/api/')
def api_post(body, request, response):
    print("api_registrationapi_registrationapi_registrationapi_registrationapi_registrationapi_registration")
    registry = request.context['registry']
    response = []
    # new registration by linkbutton
    post_dictionary = body
    print("QQQ1")
    if "devicetype" in post_dictionary:
        if registry.config["linkbutton"]: #  this must be a new device registration
            #  create new user hash
            username = hashlib.new('ripemd160', post_dictionary["devicetype"][0].encode('utf-8')).hexdigest()[:32]
            registry.config["whitelist"][username] = {"last use date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),"create date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),"name": post_dictionary["devicetype"]}
            response = [{"success": {"username": username}}]
            if "generateclientkey" in post_dictionary and post_dictionary["generateclientkey"]:
                response[0]["success"]["clientkey"] = "E3B550C65F78022EFD9E52E28378583"
            print(json.dumps(response, sort_keys=True, indent=4, separators=(',', ': ')))
        elif not registry.config["linkbutton"]:
            print("QQQ2")
            if int(registry.linkbutton.lastlinkbuttonpushed) + 30 >= int(datetime.now().strftime("%s")):
                print("QQQ3")
                username = hashlib.new('ripemd160', post_dictionary["devicetype"][0].encode('utf-8')).hexdigest()[:32]
                registry.config["whitelist"][username] = {"last use date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
                                                          "create date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
                                                           "name": post_dictionary["devicetype"]}
                response = [{"success": {"username": username}}]
                print("generateclientkey" in post_dictionary)
                print(post_dictionary["generateclientkey"])
                if "generateclientkey" in post_dictionary and post_dictionary["generateclientkey"]:
                    response[0]["success"]["clientkey"] = "E3B550C65F78022EFD9E52E28378583"
                print(json.dumps(response, sort_keys=True, indent=4, separators=(',', ': ')))
            else:
                print("QQQ4")
                response = [{"error": {"type": 101, "address": request.path, "description": "link button not pressed" }}]

    request.context['conf_obj'].save()
    return response

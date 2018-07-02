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
    bridge_config = request.context['conf_obj'].bridge
    response.set_header('Content-type', 'application/xml')
#    description(bridge_config["config"]["ipaddress"], mac)
    template = get_template('description.xml.j2')
    return template.render({'ip': bridge_config["config"]["ipaddress"],
                            'mac': request.context['mac']})


@hug.get('/api/{uid}', requires=authorized)
@hug.get('/api/{uid}/', requires=authorized)
def api_get(uid, request, response):
    """Print entire config."""
    bridge_config = request.context['conf_obj'].bridge
    bridge_config["config"]["UTC"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    bridge_config["config"]["localtime"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    bridge_config["config"]["whitelist"][uid]["last use date"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    return {"lights": bridge_config["lights"],
            "groups": bridge_config["groups"],
            "config": bridge_config["config"],
            "scenes": bridge_config["scenes"],
            "schedules": bridge_config["schedules"],
            "rules": bridge_config["rules"],
            "sensors": bridge_config["sensors"],
            "resourcelinks": bridge_config["resourcelinks"]}


@hug.get('/api/{uid}/info/{info}', requires=authorized)
def api_get_info(uid, info, request, response):
    print("api_get_groupsapi_get_groupsapi_get_groupsapi_get_groupsapi_get_groupsapi_get_groups")
    bridge_config = request.context['conf_obj'].bridge
    return ridge_config["capabilities"][info]


@hug.post('/updater')
def updater(request, response):
    # TODO
    return {}


@hug.post('/api')
@hug.post('/api/')
def api_post(body, request, response):
    print("api_registrationapi_registrationapi_registrationapi_registrationapi_registrationapi_registration")
    bridge_config = request.context['conf_obj'].bridge
    response = []
    # new registration by linkbutton
    post_dictionary = body
    print("QQQ1")
    if "devicetype" in post_dictionary:
        if bridge_config["config"]["linkbutton"]: #  this must be a new device registration
            #  create new user hash
            username = hashlib.new('ripemd160', post_dictionary["devicetype"][0].encode('utf-8')).hexdigest()[:32]
            bridge_config["config"]["whitelist"][username] = {"last use date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),"create date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),"name": post_dictionary["devicetype"]}
            response = [{"success": {"username": username}}]
            if "generateclientkey" in post_dictionary and post_dictionary["generateclientkey"]:
                response[0]["success"]["clientkey"] = "E3B550C65F78022EFD9E52E28378583"
            print(json.dumps(response, sort_keys=True, indent=4, separators=(',', ': ')))
        elif not bridge_config["config"]["linkbutton"]:
            print("QQQ2")
            if int(bridge_config["linkbutton"]["lastlinkbuttonpushed"]) + 30 >= int(datetime.now().strftime("%s")):
                print("QQQ3")
                username = hashlib.new('ripemd160', post_dictionary["devicetype"][0].encode('utf-8')).hexdigest()[:32]
                bridge_config["config"]["whitelist"][username] = {"last use date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
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

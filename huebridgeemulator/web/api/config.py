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


@hug.get('/api/{uid}/config')
def api_get_config(uid, request, response):
    return request.context['registry'].config

@hug.get('/api/node')
@hug.get('/api/config')
@hug.get('/api/nouser')
@hug.get('/api/nouser/config')
def api_get_discover(request, response):
    """used by applications to discover the bridge."""
    print("api_get_discoverapi_get_discoverapi_get_discoverapi_get_discoverapi_get_discover")
    registry = request.context['registry']
    return {"name": registry.config["name"],
            "datastoreversion": 59,
            "swversion": registry.config["swversion"],
            "apiversion": registry.config["apiversion"],
            "mac": registry.config["mac"],
            "bridgeid": registry.config["bridgeid"],
            "factorynew": False,
            "modelid": registry.config["modelid"]}

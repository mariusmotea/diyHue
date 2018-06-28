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
from huebridgeemulator.web import ui
from huebridgeemulator.web.api import scenes
from huebridgeemulator.web.api import common
from huebridgeemulator.web.api import config
from huebridgeemulator.web.api import groups
from huebridgeemulator.web.api import lights
from huebridgeemulator.web.api import sensors





@hug.extend_api()
def with_other_apis():
    return [ui, scenes, common, config, groups, lights, sensors]


def start(conf_obj, sensors_state):

    @hug.request_middleware()
    def create_context(request, response):
        request.context['conf_obj'] = conf_obj
        request.context['mac'] = '%012x' % get_mac()
        request.context['sensors_state'] = sensors_state
        request.context['new_lights'] = {}


    # TODO add port
    api = hug.API(__name__)
    host = ''
    port = 80
    api.http.serve(host=host, port=port)

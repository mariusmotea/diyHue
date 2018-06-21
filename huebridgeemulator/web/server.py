from datetime import datetime
from uuid import getnode as get_mac
import random
import json

import requests
import hug
from jinja2 import FileSystemLoader, Environment

from huebridgeemulator.web.templates import get_template

@hug.static('/')
def root():
    return ("web-ui/", )


@hug.get('/config.js',  output=hug.output_format.html)
def configjs(request, response):
#    import ipdb;ipdb.set_trace()
    bridge_config = request.context['conf_obj'].bridge

    if len(bridge_config["config"]["whitelist"]) == 0:
        bridge_config["config"]["whitelist"]["web-ui-" + str(random.randrange(0, 99999))] = {"create date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),"last use date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),"name": "WegGui User"}
    print('window.config = { API_KEY: "' + list(bridge_config["config"]["whitelist"])[0] + '",};')
    response.set_header('Content-type', 'text/javascript')
    return 'window.config = { API_KEY: "' + list(bridge_config["config"]["whitelist"])[0] + '",};'


@hug.get('/description.xml',  output=hug.output_format.html)
def hue_description(request, response):
    bridge_config = request.context['conf_obj'].bridge
    response.set_header('Content-type', 'application/xml')
#    description(bridge_config["config"]["ipaddress"], mac)
    template = get_template('description.xml.j2')
    return template.render({'ip': bridge_config["config"]["ipaddress"],
                            'mac': request.context['mac']})

@hug.get('/save')
def save(request, response):
    request.context['conf_obj'].save()
    return "config saved"


authentication = hug.authentication.basic(hug.authentication.verify('Hue', 'Hue'))
@hug.get('/hue/linkbutton', requires=authentication, output=hug.output_format.html)
def linkbutton(request, response):
    bridge_config = request.context['conf_obj'].bridge
    template = get_template('webform_linkbutton.html.j2')
    if request.params.get('action') == "Activate":
        bridge_config["config"]["linkbutton"] = False
        bridge_config["linkbutton"]["lastlinkbuttonpushed"] = datetime.now().strftime("%s")
        request.context['conf_obj'].save()
        return template.render({"message": "You have 30 sec to connect your device"})
    elif request.params.get('action') == "Exit":
        return 'You are succesfully disconnected'
    elif request.params.get('action') == "ChangePassword":
        tmp_password = str(base64.b64encode(bytes(get_parameters["username"][0] + ":" + get_parameters["password"][0], "utf8"))).split('\'')
        bridge_config["linkbutton"]["linkbutton_auth"] = tmp_password[1]
        request.context['conf_obj'].save()
        return template.render({"message": "Your credentials are succesfully change. Please logout then login again"})
    else:
        return template.render({})

@hug.get('/hue', output=hug.output_format.html)
def linkbutton(request, response):
    bridge_config = request.context['conf_obj'].bridge
    template = get_template('webform_hue.html.j2')
    if request.params.get('ip'):
        url = "http://" + request.params.get('ip') + "/api/"
        data = json.dumps({"devicetype": "Hue Emulator"})
        query = requests.post(url, data=data)
        response = query.json()
        if "success" in response[0]:
            url = "http://" +request.params.get('ip') + "/api/" + response[0]["success"]["username"] + "/lights"
            query = requests.get(url)
            hue_lights =  query.json()
#            hue_lights = json.loads(sendRequest("http://" + get_parameters["ip"][0] + "/api/" + response[0]["success"]["username"] + "/lights", "GET", "{}"))
            lights_found = 0
            for hue_light in hue_lights:
                new_light_id = request.context['conf_obj'].nextFreeId("lights")
                bridge_config["lights"][new_light_id] = hue_lights[hue_light]
                bridge_config["lights_address"][new_light_id] = {"username": response[0]["success"]["username"], "light_id": hue_light, "ip": request.params.get('ip'), "protocol": "hue"}
                lights_found += 1
            if lights_found == 0:
                return template.render({"message": "No lights where found"})
            else:
                return template.render({"message": "{} lights where found".format(lights_found)})
        else:
            return template.render({"message": "unable to connect to hue bridge"})
    else:
        return template.render({})

#@hug.get('/api/{uid}/sensors')
@hug.post('/api/{uid}/{type}')
def api_lights(uid, type, body, request, response):
    bridge_config = request.context['conf_obj'].bridge
    if uid in bridge_config["config"]["whitelist"]:
        if type == "lights" or type == "sensor" and not bool(body):
            Thread(target=scanForLights,
                   args=[request.context['conf_obj'],
                         request.context['new_lights']]).start()
            # TODO wait this thread but add a timeout
            time.sleep(7)
            return [{"success": {"/" + uid: "Searching for new devices"}}]
        elif type == "":
            # WHY ???
            return [{"success": {"clientkey": "E3B550C65F78022EFD9E52E28378583"}}]
        else: #create object
            # find the first unused id for new object
            # TODO
            pass

    print("/api/{uid}/lights")
    return {}

#@hug.get('/api/{uid}/groups')
#def api_lights(request, response):
#    print("/api/{uid}/groups")
#    return {}


@hug.post('/updater')
def updater(request, response):
    # TODO
    return {}









def start(conf_obj, sensors_state):

    @hug.request_middleware()
    def create_context(request, response):
        request.context['conf_obj'] = conf_obj
        request.context['mac'] = '%012x' % get_mac()
        request.context['sensors_state'] = sensors_state

    api = hug.API(__name__)
    api.http.serve()

"""Module starting http server."""
from uuid import getnode as get_mac

import hug

from huebridgeemulator.web import ui
from huebridgeemulator.web.api import scenes
from huebridgeemulator.web.api import common
from huebridgeemulator.web.api import config
from huebridgeemulator.web.api import groups
from huebridgeemulator.web.api import lights
from huebridgeemulator.web.api import sensors
from huebridgeemulator.logger import http_logger

# We need this line for the error serializer hack...
import huebridgeemulator.web.hack  # pylint: disable=W0611


@hug.extend_api()
def with_other_apis():
    """Load all API views."""
    return [ui, scenes, common, config, groups, lights, sensors]


def start(registry, sensors_state):
    """Start http server.

    .. todo:: check if some request.context elements are useless

    .. todo:: remove sensors_state dict and put it in the registry
    """
    @hug.request_middleware()
    def create_context(request, response):  # pylint: disable=W0613,W0612
        """Add context element to the request object."""
        request.context['conf_obj'] = registry
        request.context['registry'] = registry
        request.context['mac'] = '%012x' % get_mac()
        request.context['sensors_state'] = sensors_state
        request.context['new_lights'] = {}

    # TODO add port
    api = hug.API(__name__)

    host = ''
    port = 80
    http_logger.info("Start HTTP server")

    api.http.serve(host=host, port=port)

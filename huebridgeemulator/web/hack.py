"""The following lines set a custom error serializer to return only the description
of the error instead of the standard HUG behavior.

We have to do this way while https://github.com/timothycrosley/hug/issues/669 is done,
"""
import hug.api
import json
from hug import HTTP_200


hug.api._HTTPInterfaceAPI = hug.api.HTTPInterfaceAPI


class Custom_HTTPInterfaceAPI(hug.api._HTTPInterfaceAPI):

    def server(self, default_not_found=True, base_url=None):
        falcon_api = hug.api._HTTPInterfaceAPI.server(self, default_not_found=True, base_url=None)

        def error_serializer(request, response, error):
            response.status = error.title
            response.body = json.dumps(error.description)

        falcon_api.set_error_serializer(error_serializer)

        return falcon_api


hug.api.HTTPInterfaceAPI = Custom_HTTPInterfaceAPI

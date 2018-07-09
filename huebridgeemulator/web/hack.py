"""The following lines set a custom error serializer to return only the description
of the error instead of the standard HUG behavior.

We have to do this way while https://github.com/timothycrosley/hug/issues/669 is done,
"""
import json
import hug.api


hug.api._HTTPInterfaceAPI = hug.api.HTTPInterfaceAPI


class CustomHTTPInterfaceAPI(hug.api._HTTPInterfaceAPI):
    """Custom HTTPInterfaceAPI class to change error_serializer function."""

    def server(self, default_not_found=True, base_url=None):
        """Custom http server method to change error_serializer function."""
        falcon_api = hug.api._HTTPInterfaceAPI.server(self, default_not_found=True, base_url=None)

        def error_serializer(request, response, error):  # pylint: disable=W0613
            """Custom error serializer."""
            response.status = error.title
            response.body = json.dumps(error.description)

        falcon_api.set_error_serializer(error_serializer)

        return falcon_api


hug.api.HTTPInterfaceAPI = CustomHTTPInterfaceAPI

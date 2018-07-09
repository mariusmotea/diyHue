"""Module defining http tools functions."""

from falcon import HTTPUnauthorized
import hug
from hug.authentication import authenticator

from huebridgeemulator.logger import http_logger


@authenticator
# pylint: disable=W0613
def uid_authorized(request, response, verify_user, context=None, **kwargs):
    """Wrapper function for authentication."""
    # pylint: enable=W0613
    url_pices = request.path.split("/")
    if len(url_pices) < 3:
        raise Exception("Unknown")  # pylint: disable=E0704
    uid = url_pices[2]
    registry = request.context['registry']
    if not verify_user(registry.config["whitelist"], uid):
        http_logger.warning("User key %s unauthorized", uid)
        # pylint: disable=E0704
        raise HTTPUnauthorized(hug.HTTP_200,
                               description=[{"error": {"type": 1,
                                                       "address": request.path,
                                                       "description": "unauthorized user"}}])
        # pylint: enable=E0704
    return uid


def check_uid(whitelist, uid):
    """Function checking if the user is in the whitelist."""
    if uid not in whitelist:
        return False
    return True


authorized = uid_authorized(check_uid)  # pylint: disable=E1120,C0103

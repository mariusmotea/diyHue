from hug.authentication import authenticator
from huebridgeemulator.logger import http_logger


@authenticator
def uid_authorized(request, response, verify_user, context=None, **kwargs):
    url_pices = request.path.split("/")
    if len(url_pices) < 3:
        raise
    uid = url_pices[2]
    registry = request.context['registry']
    if not verify_user(registry.config["whitelist"], uid):
        response.data = [{"error": {"type": 1, "address": request.path, "description": "unauthorized user" }}]
        http_logger.warning("User key %s unauthorized", uid)
        return False
    return uid

def check_uid(whitelist, uid):
    if uid not in whitelist:
        return False
    return True

authorized = uid_authorized(check_uid)

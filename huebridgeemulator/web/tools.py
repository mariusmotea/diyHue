def authorized(request, response, module):
    url_pices = request.path.split("/")
    if len(url_pices) < 3:
        raise
    uid = url_pices[2]
    bridge_config = request.context['conf_obj'].bridge
    if uid not in bridge_config["config"]["whitelist"]:
        response.data = [{"error": {"type": 1, "address": request.path, "description": "unauthorized user" }}]
        return False
    return True

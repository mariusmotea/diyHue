"""Module related to static/templated file rendering for http server."""
import os

from jinja2 import FileSystemLoader, Environment


_DIR_PATH = os.path.dirname(os.path.realpath(__file__))
TEMPLATE_ENGINE = Environment(loader=FileSystemLoader(os.path.join(_DIR_PATH, "templates")))


def get_template(name):
    """Return template object based on the filename."""
    return TEMPLATE_ENGINE.get_template(name)


def get_static(name):
    """Return a static file."""
    filepath = os.path.join(_DIR_PATH, "web-ui", name.strip("/"))
    try:
        with open(filepath, "r") as sfh:
            return sfh.read()
    except UnicodeDecodeError:
        with open(filepath, "rb") as sfh:
            return sfh.read()

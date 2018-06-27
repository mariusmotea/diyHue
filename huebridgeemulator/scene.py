import json


class Scene():

    def __init__(self, raw):
        self.appdata = raw['appdata']
        self.lastupdated = raw['lastupdated']
        self.lights = raw['lights']
        self.lightstate = raw['lightstates']
        self.locked = raw['locked']
        self.name = raw['name']
        self.owner = raw['owner']
        self.picture = raw['picture']
        self.recyle = raw['recycle']
        self.version = raw['version']

    def serialize(self):
        ret = {"appdata": self.appdata,
               "lastupdated": self.lastupdated,
               "lights": self.lights,
               "lightstates": self.lightstate,
               "locked": self.locked,
               "name": self.name,
               "owner": self.owner,
               "pictyre": self.picture,
               "recyle": self.recyle,
               "version": self.version,
               }
        return ret

    def toJSON(self):
        return json.dumps(self.serialize())


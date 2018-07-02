# TODO not used for now
class Group():

    def __init__(self, index, name, type, action, state, class_, lights=None):

        self.index = index
        self.name = name
        # TODO list all possible type
        self.type = type
        self.action = GroupAction(action)
        self.class_ = class_
        self.state = GroupState(state)
        self.lights = []
        if lights is not None:
            self.lights = lights


class GroupState():

    def __init__(self, all_on, any_on):
        self.all_on = all_on
        self.any_on = any_on


class GroupAction():

    def __init__(self, bri, ct, hue, on, sat, xy):
        self.bri = bri
        self.ct = ct
        self.hue = hue
        self.on = on
        self.sat = sat
        self.xy = xy


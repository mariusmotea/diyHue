def update_group_status(registry, light_id):
    """Update Group(Room) status.

    registry
    light: Light Object
    """
    for group in registry.groups.values():
        if hasattr(group, "lights") and isinstance(group.lights, list) and light_id in group.lights:
            light = registry.lights[light_id]
            if hasattr(light.state, 'bri'):
                group.action.bri = light.state.bri
            if hasattr(light.state, 'xy'):
                group.action.xy = light.state.xy
            if hasattr(light.state, 'ct'):
                group.action.ct = light.state.ct
            if hasattr(light.state, 'hue'):
                group.action.hue = light.state.hue
            if hasattr(light.state, 'sat'):
                group.action.sat = light.state.sat
            any_on = False
            all_on = True
            for group_light_id in group.lights:
                if registry.lights[group_light_id].state.on == True:
                    any_on = True
                else:
                    all_on = False
            group.state.any_on = any_on
            group.state.all_on = all_on
            group.action.on = any_on

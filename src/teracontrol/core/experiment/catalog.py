from .sweep_axis import CountAxis, TemperatureAxis


AXIS_CATALOG = {
    "count": CountAxis,
    "temperature": TemperatureAxis,
}

AXIS_DEFAULTS = {
    "count": {
        "start": 0,
        "stop": 9,
        "step": 1,
        "dwell": 1.0,
    },
    "temperature": {
        "start": 0,
        "stop": 20,
        "step": 10,
        "dwell": 180.0,
    },
}
from .sweep_axis import CountAxis, TemperatureAxis, FieldAxis


AXIS_CATALOG = {
    "count": CountAxis,
    "temperature": TemperatureAxis,
    "field": FieldAxis,
}

AXIS_DEFAULTS = {
    "count": {
        "start": 1,
        "stop": 10,
        "step": 1,
        "dwell": 1.0,
    },
    "temperature": {
        "start": 0,
        "stop": 20,
        "step": 10,
        "dwell": 180.0,
    },
    "field": {
        "start": 0.0,
        "stop": 1.0,
        "step": 0.1,
        "dwell": 0.0,
    }
}
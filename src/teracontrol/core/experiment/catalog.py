from .sweep_axis import CountAxis, TemperatureAxis, FieldAxis, AngleAxis


AXIS_CATALOG = {
    "count": CountAxis,
    "temperature": TemperatureAxis,
    "field": FieldAxis,
    "angle": AngleAxis,
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
        "dwell": 0.1,
    },
    "angle": {
        "start": 0.0,
        "stop": 360.0,
        "step": 5.0,
        "dwell": 0.1,
    }
}
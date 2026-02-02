from .sweep_axis import CountAxis


AXIS_CATALOG = {
    "count": CountAxis,
}

AXIS_DEFAULTS = {
    "count": {
        "start": 0,
        "stop": 9,
        "step": 1,
        "dwell": 1.0,
    },
}
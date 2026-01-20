import numpy as np
from dataclasses import asdict
from teracontrol.core.experiment import Experiment


def serialize(obj):
    if isinstance(obj, np.ndarray):
        return {
            "__type__": "ndarray",
            "dtype": str(obj.dtype),
            "shape": obj.shape,
            "data": obj.tolist(),
        }
    
    elif isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}

    elif isinstance(obj, (list, tuple)):
        return [serialize(v) for v in obj]

    else:
        return obj

def experiment_to_dict(exp: Experiment) -> dict:
    return serialize(asdict(exp))
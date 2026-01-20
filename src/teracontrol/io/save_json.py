import json
from teracontrol.core.experiment import Experiment
from teracontrol.io.serialize import experiment_to_dict


def save_experiment_json(exp: Experiment, path: str) -> None:
    with open(path, "w") as f:
        json.dump(experiment_to_dict(exp), f, indent=2)
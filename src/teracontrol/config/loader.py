from pathlib import Path
import yaml


def load_config(path):
    """
    Load YAML configuration file and return it as a dict.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    
    with path.open("r") as f:
        return yaml.safe_load(f)
    
def save_config(config: dict, path):
    """
    Save configuration dict to a YAML file.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w") as f:
        yaml.safe_dump(config, f, sort_keys=False)
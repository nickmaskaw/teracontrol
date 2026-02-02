from pathlib import Path
import json


def load_config(path):
    """
    Load JSON configuration file and return it as a dict.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config: dict, path):
    """
    Save configuration dict to a JSON file.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(
            config,
            f,
            indent=4,        # pretty-printed, like YAML
            ensure_ascii=False
        )

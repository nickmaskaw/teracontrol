from __future__ import annotations

import re
from pathlib import Path
from datetime import datetime
from typing import Any

import h5py
import json

from teracontrol.core.data import DataAtom


# =============================================================================
# Helpers
# =============================================================================

def normalize_key(key: str) -> str:
    """
    Normalize a key to be a valid HDF5 attribute name.
    """
    key = key.strip()
    key = re.sub(r"\s+", "_", key)  # spaces -> underscores
    key = re.sub(r"[^\w\.]", "", key)  # drop weird chars
    return key

def flatten_dict(
    data: dict[str, Any],
    prefix: str = "",
    separator: str = ".",
) -> dict[str, Any]:
    """
    Recursively flatten a nested dict
    """
    out: dict[str, Any] = {}

    for key, value in data.items():
        norm_key = normalize_key(key)
        full_key = f"{prefix}{separator}{norm_key}" if prefix else norm_key

        if isinstance(value, dict):
            out.update(flatten_dict(value, full_key, separator))
        else:
            out[full_key] = value

    return out

def write_attr(attrs, key: str, value: Any) -> None:
    """
    Safely write an HDF5 attribute
    """
    if value is None:
        attrs[key] = ""
    elif isinstance(value, (int, float, bool, str)):
        attrs[key] = value
    else:
        attrs[key] = json.dumps(value)

# =============================================================================
# HDF5 writer
# =============================================================================

class HDF5RunWriter:
    """
    Live HDF5 writer for a single experiment run.

    One file == one run.
    One DataAtom == one dataset.
    """

    def __init__(self, path: Path):
        self._path = Path(path)
        self._file: h5py.File | None = None
        self._group: h5py.Group | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def open(
        self,
        sweep_meta: dict[str, Any],
        user_meta: dict[str, Any],
    ) -> None:
        self._file = h5py.File(self._path, "w")
        self._group = self._file.create_group("run")

        # --- Run attributes ---
        attrs = self._group.attrs
        write_attr(attrs, "created_at", datetime.now().astimezone().isoformat())
        write_attr(attrs, "status", "running")

        # --- Sweep metadata ---
        flat_sweep = flatten_dict(sweep_meta, prefix="sweep")
        for k, v in flat_sweep.items():
            write_attr(attrs, k, v)

        # --- User metadata ---
        flat_user = flatten_dict(user_meta, prefix="user", separator=".")
        for k, v in flat_user.items():
            write_attr(attrs, k, v)

    def write(self, index: int, atom: DataAtom) -> None:
        """
        Append DataAtom as its own group.
        """
        assert self._group is not None

        name = f"data_{index:05d}"

        if name in self._group:
            raise RuntimeError(
                f"Group '{name}' already exists (duplicate DataAtom)"
            )
        
        g = self._group.create_group(name)

        payload = atom.payload

        if not hasattr(payload, "to_dict"):
            raise TypeError(
                f"Payload type {type(payload).__name__} "
                 "does not support HDF5 serialization"
            )
        
        for key, array in payload.to_dict().items():
            g.create_dataset(key, data=array)

        write_attr(g.attrs, "index", index)
        write_attr(g.attrs, "timestamp", atom.timestamp)

        flat_status = flatten_dict(atom.status, prefix="status", separator=".")
        for k, v in flat_status.items():
            write_attr(g.attrs, k, v)

    def close(self, status: str = "completed") -> None:
        """
        Finalize and close the HDF5 file.
        """
        if self._group is not None:
            write_attr(self._group.attrs, "status", status)
            write_attr(
                self._group.attrs,
                "finished_at",
                datetime.now().astimezone().isoformat()
            )

        if self._file is not None:
            self._file.close()

        self._file = None
        self._group = None

    
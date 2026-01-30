from __future__ import annotations

from pathlib import Path
from datetime import datetime
from typing import Any

import h5py
import json

from teracontrol.core.data import DataAtom


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
        attrs["created_at"] = datetime.now().astimezone().isoformat()
        attrs["status"] = "running"

        # --- Sweep metadata ---
        for k, v in sweep_meta.items():
            attrs[f"sweep.{k}"] = v

        # --- User metadata ---
        for k, v in user_meta.items():
            attrs[f"user.{k}"] = v

        # --- Datasets (created lazily on first write) ---
        self._index = 0

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

        g.attrs["index"] = index
        g.attrs["timestamp"] = atom.timestamp

        for key, value in atom.status.items():
            g.attrs[f"status.{key}"] = json.dumps(value)

    def close(self, status: str = "completed") -> None:
        """
        Finalize and close the HDF5 file.
        """
        if self._group is not None:
            self._group.attrs["status"] = status
            self._group.attrs["finished_at"] = (
                datetime.now().astimezone().isoformat()
            )

        if self._file is not None:
            self._file.close()

        self._file = None
        self._group = None

    
from __future__ import annotations

import re
from pathlib import Path
from datetime import datetime
from typing import Any

import h5py
import json
import numpy as np

from teracontrol.core.data import DataAtom


# =============================================================================
# Helpers
# =============================================================================

def normalize_key(key: str) -> str:
    """
    Normalize a key to be HDF5-safe.
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
    Recursively flatten a nested dictionary.
    """
    out: dict[str, Any] = {}

    for key, value in data.items():
        norm = normalize_key(key)
        full = f"{prefix}{separator}{norm}" if prefix else norm

        if isinstance(value, dict):
            out.update(flatten_dict(value, full, separator))
        else:
            out[full] = value

    return out


def write_attr(attrs: h5py.AttributeManager, key: str, value: Any) -> None:
    """
    Write an HDF5-safe attribute.

    - None is skipped
    - Scalars are written directly
    - Complex objects are JSON-encoded
    """

    if value is None:
        return

    if isinstance(value, str):
        attrs.create(
            key,
            value,
            dtype=h5py.string_dtype(encoding="utf-8"),
        )
    elif isinstance(value, (int, float, bool)):
        attrs[key] = value
    else:
        attrs.create(
            key,
            json.dumps(value),
            dtype=h5py.string_dtype(encoding="utf-8"),
        )


# =============================================================================
# HDF5 writer
# =============================================================================

class HDF5RunWriter:
    """
    Live HDF5 writer for a single experiment run.

    Layout:

    /run
        attrs (experiment-level metadata)
        /data
            data_00000  (dataset: signal)
                attrs (data-level metadata)
            data_00001  (dataset: signal)
                attrs (data-level metadata)
            ...
    """

    def __init__(self, path: Path, flush_every: int = 1):
        self._path = Path(path)
        self._file: h5py.File | None = None
        self._run: h5py.Group | None = None
        self._data: h5py.Group | None = None

        self._flush_every = flush_every
        self._counter = 0

    # --------------------------------------------------------------------------
    # Context manager
    # --------------------------------------------------------------------------

    def __enter__(self) -> HDF5RunWriter:
        return self
    
    def __exit__(self, exc_type, exc, tb) -> None:
        status = "failed" if exc else "completed"
        self.close(status=status)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def open(
        self,
        sweep_meta: dict[str, Any],
        user_meta: dict[str, Any],
    ) -> None:
        """
        Create the HDF5 file and write run-level metadata.
        """
        self._file = h5py.File(self._path, "w", libver="latest")
        self._run = self._file.create_group("run")
        self._data = self._run.create_group("data")

        attrs = self._run.attrs
        write_attr(attrs, "run.created_at", datetime.now().astimezone().isoformat())
        write_attr(attrs, "run.status", "running")

        for k, v in flatten_dict(sweep_meta, prefix="sweep").items():
            write_attr(attrs, k, v)

        for k, v in flatten_dict(user_meta, prefix="user").items():
            write_attr(attrs, k, v)

    # --------------------------------------------------------------------------
    # Writing
    # --------------------------------------------------------------------------

    def write(self, index: int, atom: DataAtom) -> None:
        """
        Write a single DataAtom as one dataset.
        """
        if self._data is None:
            raise RuntimeError("Writer not opened")

        name = f"data_{index:05d}"
        if name in self._data:
            raise RuntimeError(f"Duplicate DataAtom index {index}")

        payload = atom.payload
        arrays = payload.to_dict()

        if "signal" not in arrays or "time" not in arrays:
            raise ValueError("Payload must provide 'signal'and 'time'")
        
        signal = np.asarray(arrays["signal"])
        time = np.asarray(arrays["time"])

        if signal.ndim != 1 or time.ndim != 1:
            raise ValueError("Signal and time must be 1D arrays")
        
        if len(signal) != len(time):
            raise ValueError("Signal and time must have the same length")
        
        # Deterministic time encoding (instrument contract)
        t0 = float(time[0])
        dt = float(time[1] - time[0]) if len(time) > 1 else 0.0
        nt = signal.shape[0]

        # Non-blocking uniformity check (record only)
        time_uniform = True
        if len(time) > 2:
            time_uniform = np.allclose(
                time,
                t0 + dt * np.arange(len(time)),
                rtol=1e-9,
                atol=0.0,
            )
        
        # Create the dataset
        dset = self._data.create_dataset(
            name,
            data=signal,
            chunks=True,
            compression="gzip",
            compression_opts=4,
            shuffle=True,
        )

        # Data metadata
        write_attr(dset.attrs, "data.index", index)
        write_attr(dset.attrs, "data.timestamp", atom.timestamp)
        write_attr(dset.attrs, "data.unit", "nA")
        
        # Time metadata
        write_attr(dset.attrs, "time.unit", "ps")
        write_attr(dset.attrs, "time.t0", t0)
        write_attr(dset.attrs, "time.dt", dt)
        write_attr(dset.attrs, "time.nt", signal.shape[0])
        write_attr(dset.attrs, "time.encoding", "uniform:t(n)=t0+dt*n")
        write_attr(dset.attrs, "time.uniform", time_uniform)

        # Status metadata
        for k, v in flatten_dict(atom.status, prefix="status").items():
            write_attr(dset.attrs, k, v)

        self._counter += 1
        if self._counter % self._flush_every == 0:
            self._file.flush()

    # --------------------------------------------------------------------------
    # Finalization
    # --------------------------------------------------------------------------

    def close(self, status: str = "completed") -> None:
        """
        Finalize and close the HDF5 file.
        """
        if self._run is not None:
            write_attr(self._run.attrs, "status", status)
            write_attr(
                self._run.attrs,
                "finished_at",
                datetime.now().astimezone().isoformat()
            )

        if self._file is not None:
            self._file.flush()
            self._file.close()

        self._file = None
        self._run = None
        self._data = None

    
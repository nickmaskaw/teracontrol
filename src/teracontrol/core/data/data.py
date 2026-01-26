from dataclasses import dataclass
import numpy as np
from datetime import datetime
from typing import Any, Callable
from scipy.fft import fft, fftfreq


# =============================================================================
# Payload
# =============================================================================

@dataclass(frozen=True)
class Waveform:
    time: np.ndarray
    signal: np.ndarray

@dataclass(frozen=True)
class WaveSpectrum:
    freq: np.ndarray
    amp: np.ndarray
    phase: np.ndarray

# --- FFT helper ---

def waveform_to_wavespectrum(
    waveform: Waveform,
    t_cut: float | None = None,
    length: int | None = None,
) -> WaveSpectrum:   
    if t_cut is not None:
        _signal = waveform.signal[waveform.time < t_cut]
    else:
        _signal = waveform.signal

    # zero padding
    if length is not None:
        _len = length
    else:
        _len = len(_signal)

    _dt = waveform.time[1] - waveform.time[0]
    _fft = fft(_signal, n=_len)[:_len//2]
    _freq = fftfreq(_len, _dt)[:_len//2]
    _amp = np.abs(_fft)
    _phase = np.unwrap(np.angle(_fft))
    
    return WaveSpectrum(
        freq=_freq,
        amp=_amp,
        phase=_phase,
    )

# =============================================================================
# Data Atom
# =============================================================================

@dataclass(frozen=True)
class DataAtom:
    timestamp: datetime
    status: dict[str, Any]
    payload: Any


# =============================================================================
# Data Cappture helper
# =============================================================================

def capture_data(
        read_status: Callable[[], dict[str, Any]],
        read_data: Callable[[], Any],
):  
    timestamp = datetime.now().astimezone().isoformat()
    status = read_status()
    payload = read_data()

    return DataAtom(
        timestamp=timestamp,
        status=status,
        payload=payload,
    )
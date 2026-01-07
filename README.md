# teracontrol

**teracontrol** is a research-grade Python framework for controlling
THz time-domain spectroscopy (THz-TDS) and magneto-THz experiments.

## Design goals

- Stability and reproducibility over UI polish
- Strict separation between hardware, acquisition logic, and experiments
- Support for long unattended measurement runs
- Full metadata and provenance tracking
- Hardware abstraction for future extensibility

## Target systems

- Toptica TeraFlash (Ethernet)
- Oxford Instruments Cryomag (Mercury IPS + ITC)
- Simulated backends for development and testing

## Status

🚧 Early development — architecture-first phase.

No hardware control implemented yet.
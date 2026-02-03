!!! AI generated README below !!!

# teracontrol

**teracontrol** is a modular Python framework for **laboratory experiment control and data acquisition**, designed around real-world constraints of multi-instrument THz experiments: asynchronous hardware, slow control loops, live monitoring, and safe data persistence.

It combines a **Qt-based GUI**, a **clean experiment abstraction**, and **pluggable hardware engines** to coordinate instruments such as THz systems, temperature controllers, and magnets in a reproducible and extensible way.

This project is under active development and reflects an evolving architecture rather than a frozen “end-user” application.

---

## Features

- 🧠 **Experiment-centric design**
  - Explicit experiment lifecycle (`IDLE → RUNNING → PAUSED → ERROR`)
  - Declarative sweep axes (time, temperature, field, etc.)
  - Engine-based execution model

- 🧩 **Hardware abstraction (HAL)**
  - Clear separation between *what* the experiment wants and *how* the hardware does it
  - Instrument-specific drivers isolated in `hal/`

- 🖥️ **Qt GUI**
  - Instrument connection & querying
  - Live signal monitoring and trends
  - Experiment control widgets

- 💾 **Robust data handling**
  - Incremental HDF5 writing during acquisition
  - No need to keep full experiments in memory

- 🧪 **Test utilities**
  - Fake data generators
  - Sweep runner tests
  - Status querying experiments

---

## Project Structure

```text
teracontrol
├─ docs/                  # Architecture notes and vendor manuals
├─ src/teracontrol/
│  ├─ app/                # Application entry point and global context
│  ├─ core/               # Experiment model, sweep logic, status handling
│  ├─ engines/            # Execution engines (capture, temperature, HDF5, etc.)
│  ├─ gui/                # Qt widgets and main window
│  ├─ hal/                # Hardware abstraction layer (instrument drivers)
│  ├─ utils/              # Logging and small utilities
├─ tests/                 # Development and regression tests
├─ environment.yml        # Conda environment (recommended)
├─ pyproject.toml         # Packaging and dependencies
```

A more detailed discussion of the architecture lives in `docs/architecture.md`.

---

## Installation

### Option 1: Conda (recommended)

This is the most reliable way to get a working Qt + scientific Python stack.

```bash
conda env create -f environment.yml
conda activate teracontrol
```

Then install the project in editable mode:

```bash
pip install -e .
```

---

### Option 2: pip / virtualenv

If you prefer pip-only environments:

```bash
python -m venv .venv
source .venv/bin/activate   # Linux / macOS
# .venv\Scripts\activate    # Windows

pip install -U pip
pip install -e .
```

⚠️ Note: Qt bindings and HDF5 backends can be more fragile without Conda.

---

## Running the Application

Once installed:

```bash
python -m teracontrol.app.main
```

This launches the main Qt GUI.

Configuration (IP addresses, ports, etc.) is currently expected to be handled at code level or via environment variables (see `.env.example`).

---

## Development Status & Philosophy

This project prioritizes:

- **Explicit control flow over magic**
- **Long-running experiment safety**
- **Debuggability over premature abstraction**

Some parts are intentionally verbose or conservative (e.g. engine boundaries, sweep handling). The goal is to make experimental logic *auditable* and *hard to misuse*, not minimal.

Expect breaking changes while the architecture stabilizes.

---

## License

See `LICENSE` for details.

---

## Notes for Contributors (or Future You)

- Engines should remain **stateless or minimally stateful**
- HAL methods should be **synchronous and deterministic**
- GUI widgets must never directly talk to hardware
- Experiments should be restartable after failure without restarting the app

If you’re unsure where something belongs, it probably goes in:
- **`core/`** if it’s conceptual
- **`engines/`** if it *does work*
- **`hal/`** if it touches hardware
- **`gui/`** if it reacts to humans 😄

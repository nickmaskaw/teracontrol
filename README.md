```
teracontrol
├─ configs
│  └─ instruments.yaml
├─ docs
│  ├─ architecture.md
│  ├─ TF_PRO-RC-Commands-UDP-v22p1.pdf
│  └─ TF_PRO_RemoteDataAcquisition-TCP_v22p1.pdf
├─ environment.yml
├─ LICENSE
├─ pyproject.toml
├─ README.md
├─ scripts
├─ src
│  └─ teracontrol
│     ├─ app
│     │  ├─ controller.py
│     │  ├─ main.py
│     │  └─ __init__.py
│     ├─ cli
│     │  └─ temp_logger.py
│     ├─ config
│     │  ├─ loader.py
│     │  └─ __init__.py
│     ├─ core
│     │  ├─ experiment
│     │  │  ├─ qt_experiment.py
│     │  │  ├─ runner.py
│     │  │  ├─ sweep_axis.py
│     │  │  ├─ sweep_config.py
│     │  │  └─ __init__.py
│     │  ├─ instruments
│     │  │  ├─ catalog.py
│     │  │  ├─ presets.py
│     │  │  ├─ registry.py
│     │  │  └─ __init__.py
│     │  └─ __init__.py
│     ├─ engines
│     │  ├─ capture_engine.py
│     │  ├─ connection_engine.py
│     │  ├─ query_engine.py
│     │  └─ __init__.py
│     ├─ gui
│     │  ├─ dock_widget.py
│     │  ├─ experiment
│     │  │  ├─ experiment_control_widget.py
│     │  │  └─ __init__.py
│     │  ├─ instrument
│     │  │  ├─ connection_widget.py
│     │  │  ├─ query_widget.py
│     │  │  └─ __init__.py
│     │  ├─ main_window.py
│     │  ├─ monitor
│     │  │  ├─ curve_list_widget.py
│     │  │  ├─ monitor_widget.py
│     │  │  ├─ signal_widget.py
│     │  │  ├─ trends_widget.py
│     │  │  └─ __init__.py
│     │  └─ __init__.py
│     ├─ hal
│     │  ├─ base.py
│     │  ├─ generic_mercury.py
│     │  ├─ mercury_ips.py
│     │  ├─ mercury_itc.py
│     │  ├─ teraflash.py
│     │  └─ __init__.py
│     ├─ utils
│     │  ├─ logging.py
│     │  └─ __init__.py
│     └─ __init__.py
└─ tests
   ├─ monitor_fake_data.py
   ├─ status_querying.py
   └─ sweep_runner.py

```
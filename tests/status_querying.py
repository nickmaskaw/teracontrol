import json
import logging
from teracontrol.hal.teraflash import TeraflashTHzSystem
from teracontrol.hal.mercury_itc import MercuryITCController
from teracontrol.hal.mercury_ips import MercuryIPSController
from teracontrol.core.data import capture_data
from teracontrol.core.experiment import Experiment
from teracontrol.io.save_json import save_experiment_json

from teracontrol.utils.logging import setup_logging
setup_logging(level=logging.DEBUG)

thz = TeraflashTHzSystem()
itc = MercuryITCController()
ips = MercuryIPSController()

def connect_all():
    thz.connect("127.0.0.1")
    itc.connect("192.168.1.2")
    ips.connect("192.168.1.3")

def disconnect_all():
    thz.disconnect()
    itc.disconnect()
    ips.disconnect()

def read_status():
    return {
        "THz System": thz.status(),
        "Temperature Controller": itc.status(),
        "Field Controller": ips.status(),
    }

def read_data():
    raw_data = thz.acquire_trace()
    return {
        "waveform": raw_data,
    }

connect_all()
print(json.dumps(read_status(), indent=4))
disconnect_all()
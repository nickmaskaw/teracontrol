from dataclasses import asdict
from teracontrol.core.experiment import SweepRunner, SweepConfig, CountAxis
from teracontrol.core.data import Experiment

count = CountAxis()
sweep = SweepConfig(count, 0, 10, 1, 1.0)

experiment = Experiment(metadata=sweep.describe())

runner = SweepRunner(sweep, experiment, capture)
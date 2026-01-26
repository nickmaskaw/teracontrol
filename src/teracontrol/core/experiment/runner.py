from __future__ import annotations

import time
from typing import Callable

from teracontrol.core.data import DataAtom
from teracontrol.core.data import Experiment
from .sweep_config import SweepConfig


class SweepRunner:
    """
    Executes a 1D sweep and fills an existing Experiment with DataAtom entries.
    """

    def __init__(
        self,
        sweep: SweepConfig,
        experiment: Experiment,
        capture: Callable[[dict], DataAtom],
    ):
        self.sweep = sweep
        self.experiment = experiment
        self.capture = capture
        self._abort = False

    def abort(self) -> None:
        """
        Request cooperative abortion of the sweep.
        """
        self._abort = True

    def run(self) -> Experiment:
        """
        Run the sweep synchronously.

        Returns the Experiment instance passed at construction time.
        """
        axis = self.sweep.axis

        self.experiment.metadata.update(self.sweep.describe())

        for value in self.sweep.points():
            if self._abort:
                break

            axis.goto(value)

            if self.sweep.dwell_s > 0:
                time.sleep(self.sweep.dwell_s)

            meta = axis.describe(value)
            atom = self.capture(meta)

            self.experiment.record.append(atom)

        return self.experiment
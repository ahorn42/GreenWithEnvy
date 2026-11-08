# This file is part of gwe.
#
# Copyright (c) 2018 Roberto Leinardi
#
# gwe is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# gwe is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with gwe.  If not, see <http://www.gnu.org/licenses/>.
import logging
from collections import deque
from enum import Enum
from typing import Any, Tuple, Dict, Deque, Mapping, Sequence

from gi.repository import Gtk, GLib
from injector import singleton, inject

from gwe.interactor.settings_interactor import SettingsInteractor
from gwe.model.gpu_status import GpuStatus
from gwe.model.status import Status
from gwe.util.view import hide_on_delete

_LOG = logging.getLogger(__name__)

MONITORING_INTERVAL = 300  # Seconds of history shown for every GPU
# The graph is shown delayed by one measurement interval (see GraphView): keep a bit more than what is shown
HISTORY_MARGIN = 20  # Seconds


class GraphType(Enum):
    GPU_CLOCK = 1
    MEMORY_CLOCK = 2
    GPU_TEMP = 3
    FAN_DUTY = 4
    FAN_RPM = 5
    GPU_LOAD = 6
    MEMORY_LOAD = 7
    MEMORY_USAGE = 8
    POWER_DRAW = 9


# (monotonic time in microseconds, value, unit, minimum of the axis, maximum of the axis)
GraphSample = Tuple[int, float, str, float, float]
GraphData = Dict[GraphType, GraphSample]


class HistoricalDataViewInterface:
    def show(self) -> None:
        raise NotImplementedError()

    def hide(self) -> None:
        raise NotImplementedError()

    def refresh_graphs(self, history: Mapping[GraphType, Sequence[GraphSample]]) -> None:
        raise NotImplementedError()


@singleton
class HistoricalDataPresenter:
    @inject
    def __init__(self,
                 settings_interactor: SettingsInteractor,
                 ) -> None:
        _LOG.debug("init HistoricalDataPresenter ")
        self._settings_interactor = settings_interactor
        self.view: HistoricalDataViewInterface = HistoricalDataViewInterface()
        self._gpu_index: int = 0
        # The measurements of every GPU of the last MONITORING_INTERVAL seconds are recorded all the time, also when the
        # window is closed and for the GPUs that are not selected, so the history is there when it is needed.
        self._history: Dict[int, Dict[GraphType, Deque[GraphSample]]] = {}

    def add_status(self, new_status: Status, gpu_index: int) -> None:
        time = GLib.get_monotonic_time()
        for gpu_status in new_status.gpu_status_list:
            self._record(gpu_status.index, self._get_graph_data(gpu_status, time), time)
        self.select_gpu(gpu_index)

    def select_gpu(self, gpu_index: int) -> None:
        """Shows the history of the given GPU."""
        self._gpu_index = gpu_index
        self.view.refresh_graphs(self._history.get(gpu_index, {}))

    def _record(self, gpu_index: int, data: GraphData, time: int) -> None:
        history = self._history.setdefault(gpu_index, {})
        oldest_time = time - (MONITORING_INTERVAL + HISTORY_MARGIN) * 1000 * 1000
        for graph_type, sample in data.items():
            samples = history.setdefault(graph_type, deque())
            samples.append(sample)
            while samples[0][0] < oldest_time:
                samples.popleft()

    @staticmethod
    def _get_graph_data(gpu_status: GpuStatus, time: int) -> GraphData:
        data: GraphData = {}
        gpu_clock = gpu_status.clocks.graphic_current
        if gpu_clock is not None:
            data[GraphType.GPU_CLOCK] = (time, float(gpu_clock), 'MHz', 0.0, 2000.0)
        mem_clock = gpu_status.clocks.memory_current
        if mem_clock is not None:
            data[GraphType.MEMORY_CLOCK] = (time, float(mem_clock), 'MHz', 0.0, 7000.0)
        gpu_temp = gpu_status.temp.gpu
        if gpu_temp is not None:
            data[GraphType.GPU_TEMP] = (time, float(gpu_temp), '°C', 0.0, 100.0)
        if gpu_status.fan.fan_list:
            fan_duty = gpu_status.fan.fan_list[0][0]
            data[GraphType.FAN_DUTY] = (time, float(fan_duty), '%', 0.0, 100.0)
            fan_rpm = gpu_status.fan.fan_list[0][1]
            data[GraphType.FAN_RPM] = (time, float(fan_rpm), 'rpm', 0.0, 2200.0)
        gpu_load = gpu_status.info.gpu_usage
        if gpu_load is not None:
            data[GraphType.GPU_LOAD] = (time, float(gpu_load), '%', 0.0, 100.0)
        mem_load = gpu_status.info.memory_usage
        if mem_load is not None:
            data[GraphType.MEMORY_LOAD] = (time, float(mem_load), '%', 0.0, 100.0)
        mem_usage = gpu_status.info.memory_used
        if mem_usage is not None and gpu_status.info.memory_total is not None:
            data[GraphType.MEMORY_USAGE] = (time, float(mem_usage), 'MiB', 0.0, float(gpu_status.info.memory_total))
        power_draw = gpu_status.power.draw
        maximum = gpu_status.power.maximum
        if power_draw is not None:
            data[GraphType.POWER_DRAW] = (time, power_draw, 'W', 0.0, 400 if maximum is None else maximum)
        return data

    def show(self) -> None:
        self.view.show()

    @staticmethod
    def on_dialog_delete_event(widget: Gtk.Widget, *_: Any) -> Any:
        return hide_on_delete(widget)

    def get_refresh_interval(self) -> int:
        return self._settings_interactor.get_int('settings_refresh_interval')

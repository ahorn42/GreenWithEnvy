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
from typing import Dict, Tuple, Mapping, Sequence

from gi.repository import Gtk
from injector import singleton, inject

from gwe.di import HistoricalDataBuilder
from gwe.presenter.historical_data_presenter import HistoricalDataViewInterface, HistoricalDataPresenter, \
    MONITORING_INTERVAL, GraphType, GraphSample
from gwe.util.view import apply_window_style
from gwe.view.graph_view import GraphView

_LOG = logging.getLogger(__name__)


@singleton
class HistoricalDataView(HistoricalDataViewInterface):
    @inject
    def __init__(self,
                 presenter: HistoricalDataPresenter,
                 builder: HistoricalDataBuilder,
                 ) -> None:
        _LOG.debug('init HistoricalDataView')
        self._presenter: HistoricalDataPresenter = presenter
        self._presenter.view = self
        self._builder: Gtk.Builder = builder
        self._builder.connect_signals(self._presenter)
        self._graphs: Dict[GraphType, GraphView] = {}
        self._labels: Dict[GraphType, Tuple[Gtk.Label, Gtk.Label, Gtk.Label]] = {}
        # The history of the selected GPU, owned by the presenter
        self._history: Mapping[GraphType, Sequence[GraphSample]] = {}
        self._init_widgets()

    def _init_widgets(self) -> None:
        self._dialog: Gtk.Dialog = self._builder.get_object('dialog')
        apply_window_style(self._dialog)
        self._init_graphs()

    def set_transient_for(self, window: Gtk.Window) -> None:
        self._dialog.set_transient_for(window)

    def _init_graphs(self) -> None:
        for graph_type in GraphType:
            self._labels[graph_type] = (self._builder.get_object(f'graph_min_value_{graph_type.value}'),
                                        self._builder.get_object(f'graph_max_value_{graph_type.value}'),
                                        self._builder.get_object(f'graph_max_axis_{graph_type.value}'))
            graph = GraphView(MONITORING_INTERVAL * 1000 * 1000)
            self._builder.get_object(f'graph_container_{graph_type.value}').add(graph)
            graph.show()
            self._graphs[graph_type] = graph

    def refresh_graphs(self, history: Mapping[GraphType, Sequence[GraphSample]]) -> None:
        self._history = history
        # Nothing is calculated or drawn while the window is closed, it is updated when it is opened
        if self._dialog.props.visible:
            self._update_graphs()

    def _update_graphs(self) -> None:
        for graph_type, graph in self._graphs.items():
            samples = self._history.get(graph_type)
            minimum_label, maximum_label, current_label = self._labels[graph_type]
            if samples:
                values = [sample[1] for sample in samples]
                minimum_label.set_text(f"{min(values):.0f}")
                maximum_label.set_text(f"{max(values):.0f}")
                current_label.set_text(f"{samples[-1][1]:.0f} {samples[-1][2]}")
            else:
                minimum_label.set_text('')
                maximum_label.set_text('')
                current_label.set_text('')
            graph.set_samples(samples or ())

    def show(self) -> None:
        self._dialog.show_all()
        self._update_graphs()

    def hide(self) -> None:
        self._dialog.hide()

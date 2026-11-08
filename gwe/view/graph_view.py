# This file is part of gwe.
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
from typing import Sequence

import cairo
from gi.repository import Gtk, Gdk

from gwe.conf import GRAPH_COLOR_HEX
from gwe.presenter.historical_data_presenter import GraphSample


class GraphView(Gtk.DrawingArea):
    """Area graph of the measurements of the last `timespan` microseconds, the newest one is at the right edge.

    It is redrawn only when set_samples() is called, i.e. when there is a new measurement. This is the difference with
    Dazzle.GraphView, which animates the graph continuously and redraws the whole window 60 times per second.
    """

    def __init__(self, timespan: int) -> None:
        super().__init__()
        self._timespan = timespan
        self._samples: Sequence[GraphSample] = ()
        self._color = Gdk.RGBA()
        self._color.parse(GRAPH_COLOR_HEX)
        self.set_hexpand(True)
        self.set_size_request(-1, 80)
        self.get_style_context().add_class('view')  # The theme draws the background (e.g. dark with a dark theme)
        self.connect('draw', self._on_draw)

    def set_samples(self, samples: Sequence[GraphSample]) -> None:
        self._samples = samples
        self.queue_draw()

    def _on_draw(self, widget: Gtk.Widget, cairo_context: cairo.Context) -> bool:
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()
        Gtk.render_background(widget.get_style_context(), cairo_context, 0, 0, width, height)
        samples = self._samples
        if len(samples) < 2:
            return False
        end = samples[-1][0]
        begin = end - self._timespan
        minimum = samples[-1][3]
        maximum = max(samples[-1][4], max(sample[1] for sample in samples))
        if maximum <= minimum:
            return False

        points = [((timestamp - begin) / self._timespan * width,
                   height - (value - minimum) / (maximum - minimum) * height)
                  for timestamp, value, _, _, _ in samples]

        cairo_context.set_line_width(1.5)
        cairo_context.move_to(*points[0])
        last_x, last_y = points[0]
        for x, y in points[1:]:
            half_step = (x - last_x) / 2.0
            cairo_context.curve_to(last_x + half_step, last_y, last_x + half_step, y, x, y)
            last_x, last_y = x, y

        # The line, then the area below it
        path = cairo_context.copy_path()
        cairo_context.set_source_rgba(self._color.red, self._color.green, self._color.blue, 0.5)
        cairo_context.stroke()
        cairo_context.append_path(path)
        cairo_context.line_to(last_x, height)
        cairo_context.line_to(points[0][0], height)
        cairo_context.close_path()
        cairo_context.fill()
        return False

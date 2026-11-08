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
from typing import Sequence, Optional, Tuple

import cairo
from gi.repository import Gtk, Gdk, GLib

from gwe.conf import GRAPH_COLOR_HEX
from gwe.presenter.historical_data_presenter import GraphSample


class GraphView(Gtk.DrawingArea):
    """Area graph of the measurements of the last `timespan` microseconds, scrolling smoothly to the left.

    Dazzle.GraphView redraws the whole graph 60 times per second to scroll it, but the graph moves just about one pixel
    per second (e.g. 300 s over 400 px). Here the graph is drawn only when there is a new measurement, in a cached
    surface, which is then shifted to the left by one pixel at a time (about every 0.7 s) while the widget is visible.
    """

    def __init__(self, timespan: int) -> None:
        super().__init__()
        self._timespan = timespan
        self._samples: Sequence[GraphSample] = ()
        self._color = Gdk.RGBA()
        self._color.parse(GRAPH_COLOR_HEX)
        self._surface: Optional[cairo.Surface] = None
        self._surface_size: Tuple[int, int] = (0, 0)
        self._reference_time = 0  # Time of the newest sample, the right edge of the cached surface
        self._timer_id = 0
        self.set_hexpand(True)
        self.set_size_request(-1, 80)
        self.get_style_context().add_class('view')  # The theme draws the background (e.g. dark with a dark theme)
        self.connect('draw', self._on_draw)
        self.connect('map', self._on_map)
        self.connect('unmap', self._on_unmap)
        self.connect('size-allocate', self._on_size_allocate)

    def set_samples(self, samples: Sequence[GraphSample]) -> None:
        self._samples = samples
        self._surface = None
        self.queue_draw()

    @staticmethod
    def _now() -> int:
        return int(GLib.get_monotonic_time())

    def _on_map(self, *_: object) -> None:
        self._start_timer()

    def _on_unmap(self, *_: object) -> None:
        self._stop_timer()

    def _on_size_allocate(self, *_: object) -> None:
        if self._timer_id:
            self._stop_timer()
            self._start_timer()

    def _start_timer(self) -> None:
        if not self._timer_id:
            # The time it takes to scroll the graph by one pixel
            interval = max(100, int(self._timespan / 1000 / max(self.get_allocated_width(), 1)))
            self._timer_id = GLib.timeout_add(interval, self._on_tick)

    def _stop_timer(self) -> None:
        if self._timer_id:
            GLib.source_remove(self._timer_id)
            self._timer_id = 0

    def _on_tick(self) -> bool:
        self.queue_draw()
        return True

    def _on_draw(self, widget: Gtk.Widget, cairo_context: cairo.Context) -> bool:
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()
        Gtk.render_background(widget.get_style_context(), cairo_context, 0, 0, width, height)
        if len(self._samples) < 2:
            return False
        if self._surface is None or self._surface_size != (width, height):
            self._render_surface(widget, width, height)
        if self._surface is not None:
            shift = round((self._now() - self._reference_time) / self._timespan * width)
            cairo_context.set_source_surface(self._surface, -max(shift, 0), 0)
            cairo_context.paint()
        return False

    def _render_surface(self, widget: Gtk.Widget, width: int, height: int) -> None:
        samples = self._samples
        end = samples[-1][0]
        begin = end - self._timespan
        minimum = samples[-1][3]
        maximum = max(samples[-1][4], max(sample[1] for sample in samples))
        self._surface = None
        if maximum <= minimum:
            return

        surface = widget.get_window().create_similar_surface(cairo.CONTENT_COLOR_ALPHA, width, height)
        cairo_context = cairo.Context(surface)
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
        self._surface = surface
        self._surface_size = (width, height)
        self._reference_time = end

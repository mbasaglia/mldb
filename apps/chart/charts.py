"""
\file

\author Mattia Basaglia

\copyright Copyright 2016 Mattia Basaglia

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import math
from django.utils.html import escape
from django.utils.safestring import mark_safe
from ..simple_page.templatetags.simple_page import make_attrs


class MetaData(object):
    def __init__(self, label="", id="", link=None, extra=None):
        self.label = label
        self.id = id
        self.link = link
        self.extra = extra

    def ctor_args(self):
        return (self.label, self.id, self.link, self.extra)

    def wrap_link(self, svg, xmlns="xlink"):
        if not self.link:
            return svg
        if xmlns and xmlns[-1] != ':':
            xmlns += ':'
        return mark_safe(
            "<a %shref='%s'>%s</a>" % (
                xmlns,
                escape(self.link),
                svg,
            )
        )


class DataPoint(MetaData):
    """
    A data point in the graph
    """
    def __init__(self, value, *args, **kwargs):
        """
        \param label Human-readable string to identify the value
        \param id    Unique XML-friendly identifier for the data point
        \param value Data value
        """
        MetaData.__init__(self, *args, **kwargs)
        self.value = value
        self.dataset = None

    @property
    def percent(self):
        """
        Percentage of the total
        """
        return float(self.value) / self.dataset.total if self.dataset.total else 0

    @property
    def normalized(self):
        """
        Percentage of the maximum
        """
        return float(self.value) / self.dataset.max if self.dataset.max else 1


class DataSet(MetaData):
    """
    A list of data points
    """
    def __init__(self, points, *args, **kwargs):
        MetaData.__init__(self, *args, **kwargs)
        self._data = list(points)
        self.total = 0
        self.max = 0
        for point in self._data:
            self._on_add(point)

    def _on_add(self, point):
        if point.value > self.max:
            self.max = point.value
        self.total += point.value
        point.dataset = self

    def append(self, point):
        self._data.append(point)
        self._on_add(point)

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __getitem__(self, key):
        return self._data[key]


class DataMatrix(object):
    """
    Collects a two-dimensional set of data
    """
    def __init__(self, rows, columns, values):
        """
        \param rows     List of MetaData
        \param columns  List of MetaData
        \param values   Matrix of values
        \pre len(rows) == len(values) and all(len(row) == len columns for row in values)
        """
        self.rows = rows
        self.columns = columns
        self.values = values

    def _adjust_maximum(self, data, global_maximum):
        if global_maximum:
            max_lines = max(ds.max for ds in data)
            for ds in data:
                ds.max = max_lines
        return data

    def data_by_row(self, global_maximum=False):
        """
        Returns a row-wise view of the data
        \param global_maximum Whether to alter dataset maximums to reflect the
                              maximum value in the whole data matrix

        Each DataSet represents a row,
        and each DataPoint a value associated with a column
        """
        data = [
            DataSet(
                [
                    DataPoint(value, *column.ctor_args())
                    for column, value in zip(self.columns, row_values)
                ],
                *row.ctor_args()
            )
            for row, row_values in zip(self.rows, self.values)
        ]

        return self._adjust_maximum(data, global_maximum)

    def data_by_column(self, global_maximum=False):
        """
        Returns a column-wise view of the data
        \param global_maximum Whether to alter dataset maximums to reflect the
                              maximum value in the whole data matrix

        Each DataSet represents a column,
        and each DataPoint a value associated with a row
        """
        data = [
            DataSet(
                [
                    DataPoint(row_values[x], *row.ctor_args())
                    for row, row_values in zip(self.rows, self.values)
                ],
                *column.ctor_args()
            )
            for x, column in enumerate(self.columns)
        ]

        return self._adjust_maximum(data, global_maximum)

    def data_by_row_global_max(self):
        """
        Helper for simpler use in templates
        """
        return self.data_by_row(True)

    def data_by_column_global_max(self):
        """
        Helper for simpler use in templates
        """
        return self.data_by_column(True)


class SvgPoint(object):
    """
    SVG coordinates in user units
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return "%s,%s " % (self.x, self.y)


class SvgRect(object):
    def __init__(self, x=0, y=0, width=0, height=0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    @property
    def top_left(self):
        return SvgPoint(self.x, self.y)

    @property
    def top_right(self):
        return SvgPoint(self.x + self.width, self.y)

    @property
    def bottom_right(self):
        return SvgPoint(self.x + self.width, self.y + self.height)

    @property
    def bottom_left(self):
        return SvgPoint(self.x, self.y + self.height)


class PieChart(object):
    """
    Pie chart
    """
    def __init__(self, radius, center=None, angle_start=0):
        """
        \param center        A SvgPoint
        \param radius        Radius of the chart (in svg user units)
        \param angle_start   Starting angle (in radians)
        """
        self.radius = radius
        self.center = center if center else SvgPoint(radius, radius)
        self.angle_start = angle_start

    def _circle_point(self, angle):
        """
        Returns a coordinate tuple of a point around the pie edge
        """
        return SvgPoint(
            self.center.x + self.radius * math.cos(angle),
            self.center.y + self.radius * math.sin(angle)
        )

    def render_slice(self, angle_start, angle_delta, attrs, title):
        """
        \brief Creates a SVG path element for a pie slice shape
        \param angle_start  Starting angle (in radians)
        \param angle_delta  Arc to cover (in radians)
        \param attrs        Extra attributes for the SVG element
        \returns A string with the SVG path element
        """
        return mark_safe(
            "<path d='M %s L %s A %s 0 %s 1 %s Z' %s>"
            "<title>%s</title>"
            "</path>" % (
            self.center,
            self._circle_point(angle_start),
            SvgPoint(self.radius, self.radius),
            1 if angle_delta > math.pi else 0,
            self._circle_point(angle_start + angle_delta),
            make_attrs(attrs),
            title
        ))

    def format_title(self, point):
        return "%s (%s, %.2g%%)" % (point.label, point.value, point.percent * 100)

    def render(self, data, id_prefix="pie_slice_", class_prefix="pie_slice_"):
        """
        Renders the given data as SVG paths
        \param data         A DataSet object
        \param id_prefix    Prefix to the path IDs
        \param class_prefix Prefix to the path css classes"
        """
        slices = ""
        angle = self.angle_start
        for point in data:
            angle_delta = math.pi * 2 * point.percent
            attrs = {
                "id": id_prefix + point.id,
                "class": class_prefix + point.id,
                "data-value": point.value,
                "data-name": point.label,
            }
            slices += point.wrap_link(
                self.render_slice(angle, angle_delta, attrs, self.format_title(point))
            ) + "\n"
            angle += angle_delta
        return mark_safe(slices)


class LineChart(object):
    default_prefix = "line_chart_"

    def __init__(self, rect):
        self.rect = rect

    def relpoint(self, percent_x, percent_y):
        return SvgPoint(
            self.rect.x + self.rect.width * percent_x,
            self.rect.y + self.rect.height * (1 - percent_y),
        )

    def points(self, data):
        return [
            self.relpoint(self._rel_x(index, len(data)), data_point.normalized)
            for index, data_point in enumerate(data)
        ]

    def _rel_x(self, index, size):
        return 0 if size < 2 else float(index) / (size - 1)

    def render_line(self, data, attrs, id_prefix=default_prefix,
                    class_prefix=default_prefix):
        points = self.points(data)
        if points:
            attrs["d"] = "M " + str(points[0]) \
                       + " L " + " ".join(map(str, points[1:]))
        if data.id:
            attrs["id"] = id_prefix + data.id
            attrs["class"] = class_prefix + data.id

        return data.wrap_link(mark_safe(
            "<path %s>"
            "<title>%s</title>"
            "</path>" % (
            make_attrs(attrs),
            data.label
        )))

    def format_title(self, point):
        return "%s (%s)" % (point.label, point.value)

    def _circlepoint(self, index, data, percent):

        point = self.relpoint(
            self._rel_x(index, len(data)),
            percent
        )
        return "cx='%s' cy='%s'" % (point.x, point.y)

    def render_points(self, data, attrs, class_prefix=default_prefix):
        if data.id:
            attrs["class"] = class_prefix + data.id
        attrstring = make_attrs(attrs)
        return mark_safe("\n".join(
            point.wrap_link(
                "<circle %s data-value='%s' data-name='%s' %s>"
                "<title>%s</title>"
                "</circle>" % (
                    self._circlepoint(index, data, point.normalized),
                    point.value,
                    point.label,
                    attrstring,
                    self.format_title(point),
                )
            )
            for index, point in enumerate(data)
        ))

    def render_hgrid(self, steps, attrs):
        attrs["d"] = " ".join(
            "M %s L %s" % (
                self.relpoint(self._rel_x(i, steps), 0),
                self.relpoint(self._rel_x(i, steps), 1),
            )
            for i in range(steps)
        )
        return mark_safe(
            "<path %s/>" % (
            make_attrs(attrs),
        ))

    def render_data_trace(
        self,
        data_set,
        point_radius=0,
        id_prefix=default_prefix,
        class_prefix=default_prefix,
        attrs={}
    ):
        return mark_safe("<g %s>%s%s</g>" % (
            make_attrs(attrs),
            self.render_line(data_set, {}, id_prefix, class_prefix),
            self.render_points(data_set, {"r": point_radius}, class_prefix),
        ))

    def render(
        self,
        data_set_list,
        point_radius=0,
        grid_class="grid",
        trace_class="line_data",
        id_prefix=default_prefix,
        class_prefix=default_prefix
    ):
        if isinstance(data_set_list, DataSet):
            data_set_list = [data_set_list]

        size = len(data_set_list[0]) if data_set_list else 1
        svg = self.render_hgrid(size, {"class": grid_class})
        for data_set in data_set_list:
            svg += self.render_data_trace(
                data_set,
                point_radius,
                id_prefix,
                class_prefix,
                {"class": trace_class}
            )
        return mark_safe(svg)


class StackedBarChart(object):
    default_prefix = "stacked_bar_chart_"

    def __init__(self, rect, separation=1):
        self.rect = rect
        self.separation = separation

    def format_title(self, point):
        return "%s (%s, %.2g%%)" % (point.label, point.value, point.percent * 100)

    def render_bar_item(self, rect, attrs, title):
        """
        \brief Creates a SVG rect element for a bar item
        \param rect         Rectangle to render in size percentages
        \param attrs        Extra attributes for the SVG element
        \param title        Value title
        \returns A string with the SVG path element
        """
        height = rect.height * self.rect.height
        return mark_safe(
            "<rect x='%s' y='%s' width='%s' height='%s' %s>"
            "<title>%s</title>"
            "</rect>" % (
            self.rect.x + rect.x * self.rect.width,
            self.rect.y + self.rect.height - rect.y * self.rect.height - height,
            rect.width * self.rect.width,
            height,
            make_attrs(attrs),
            title
        ))

    def render_bar(self, data_set, sub_rect=None, class_prefix=default_prefix):
        """
        Renders a stacked bar for the given data as SVG paths
        \param data         A DataSet object
        \param class_prefix Prefix to the path css classes"
        """
        items = ""
        y = sub_rect.y
        if not sub_rect:
            sub_rect = self.rect
        for point in data_set:
            rect = SvgRect(
                x=sub_rect.x,
                y=y,
                width=sub_rect.width,
                height=point.percent * sub_rect.height
            )
            attrs = {
                "class": class_prefix + point.id,
                "data-value": point.value,
                "data-name": point.label,
            }
            items += point.wrap_link(
                self.render_bar_item(rect, attrs, self.format_title(point))
            ) + "\n"
            y += rect.height
        return mark_safe("<g>%s</g>\n" % items)

    def _subrect(self, index, size):
        if size == 0:
            return self.rect
        width = float(1) / (size + size * self.separation)
        gap_with = width * self.separation
        return SvgRect(
            x=gap_with / 2 + (gap_with + width) * index,
            y=0,
            width=width,
            height=1
        )

    def render(self, data_set_list, class_prefix=default_prefix):
        if isinstance(data_set_list, DataSet):
            data_set_list = [data_set_list]
        bars = ""
        for index, data_set in enumerate(data_set_list):
            subrect = self._subrect(index, len(data_set_list))
            bars += self.render_bar(data_set, subrect, class_prefix)
        return mark_safe(bars)

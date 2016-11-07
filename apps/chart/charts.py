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

    def data_view(self):
        return MatrixView(self)

    def transposed_view(self):
        return TransposedMatrixView(self)


class MatrixView(object):
    def __init__(self, data_matrix):
        self.data_matrix = data_matrix

    @property
    def records(self):
        return self.data_matrix.rows

    @property
    def items(self):
        return self.data_matrix.columns

    def __call__(self, record_id, item_id):
        return self.data_matrix.values[record_id][item_id]

    @property
    def enumerated_items(self):
        return enumerate(self.items)

    @property
    def enumerated_records(self):
        return enumerate(self.records)
    @property
    def range_items(self):
        return xrange(len(self.items))

    @property
    def range_records(self):
        return xrange(len(self.records))

    def record_dataset(self, index):
        record = self.records[index]
        return DataSet(
            [
                DataPoint(
                    self(index, item_id),
                    *self.items[item_id].ctor_args()
                )
                for item_id in self.range_items
            ],
            *record.ctor_args()
        )

    def item_dataset(self, index):
        item = self.items[index]
        return DataSet(
            [
                DataPoint(
                    self(record_id, index),
                    *self.items[record_id].ctor_args()
                )
                for record_id in self.range_records
            ],
            *item.ctor_args()
        )

    def max_value(self):
        return max(max(self.data_matrix.values))

    @property
    def transposed(self):
        return TransposedMatrixView(self.data_matrix)


class TransposedMatrixView(MatrixView):
    @property
    def records(self):
        return self.data_matrix.columns

    @property
    def items(self):
        return self.data_matrix.rows

    def __call__(self, record_id, item_id):
        return self.data_matrix.values[item_id][record_id]

    @property
    def transposed(self):
        return MatrixView(self.data_matrix)


class MatrixViewSingleRecord(MatrixView):
    def __init__(self, data_set):
        self.data_set = data_set

    @property
    def records(self):
        return [self.data_set]

    @property
    def items(self):
        return self.data_set

    def __call__(self, record_id, item_id):
        return self.data_set[item_id].value

    def max_value(self):
        return self.data_set.max

    def record_dataset(self, index):
        return self.data_set

    @property
    def transposed(self):
        return MatrixViewSingleItem(self.data_set)


class MatrixViewSingleItem(MatrixView):
    def __init__(self, data_set):
        self.data_set = data_set

    @property
    def records(self):
        return self.data_set

    @property
    def items(self):
        return [self.data_set]

    def __call__(self, record_id, item_id):
        return self.data_set[record_id].value

    def max_value(self):
        return self.data_set.max

    def item_dataset(self, index):
        return self.data_set

    @property
    def transposed(self):
        return MatrixViewSingleRecord(self.data_set)


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


class LineChartBase(object):
    def __init__(self, rect):
        self.rect = rect

    def point_rel2abs(self, point):
        """
        Converts a relative/normalize point into an absolute point
        """
        return SvgPoint(
            self.rect.x + self.rect.width * point.x,
            self.rect.y + self.rect.height * (1 - point.y),
        )

    def _value_point(self, percent, index, size):
        """
        Returns an absolute point based on a data value
        """
        return self.point_rel2abs(SvgPoint(
            0 if size < 2 else float(index) / (size - 1),
            percent
        ))

    def render_hgrid(self, steps, attrs):
        attrs["d"] = " ".join(
            "M %s L %s" % (
                self._value_point(0, i, steps),
                self._value_point(1, i, steps),
            )
            for i in range(steps)
        )
        return mark_safe(
            "<path %s/>" % (
            make_attrs(attrs),
        ))


class LineChart(LineChartBase):
    default_prefix = "line_chart_"

    def __init__(self, rect):
        super(LineChart, self).__init__(rect)

    def points(self, data):
        return [
            self._value_point(data_point.normalized, index, len(data))
            for index, data_point in enumerate(data)
        ]

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
        point = self._value_point(percent, index, len(data))
        return "cx='%s' cy='%s'" % (point.x, point.y)

    def _svg_circle(self, data, index, point, attrstring):
        return point.wrap_link(
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

    def render_points(self, data, attrs, class_prefix=default_prefix):
        if data.id:
            attrs["class"] = class_prefix + data.id
        attrstring = make_attrs(attrs)
        return mark_safe("\n".join(
            self._svg_circle(data, index, point, attrstring)
            for index, point in enumerate(data)
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
        data,
        point_radius=0,
        grid_class="grid",
        trace_class="line_data",
        id_prefix=default_prefix,
        class_prefix=default_prefix
    ):
        if isinstance(data, DataSet):
            data = MatrixViewSingleItem(data)

        svg = self.render_hgrid(len(data.records), {"class": grid_class})
        global_max = data.max_value()
        for item_id in reversed(data.range_items):
            data_set = data.item_dataset(item_id)
            data_set.max = global_max
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

    def render(self, data, class_prefix=default_prefix):
        bars = ""
        for index in data.range_records:
            subrect = self._subrect(index, len(data.records))
            bars += self.render_bar(data.record_dataset(index), subrect, class_prefix)
        return mark_safe(bars)


class StackedLineChart(LineChartBase):
    default_prefix = "stacked_line_chart_"

    def __init__(self, rect):
        super(StackedLineChart, self).__init__(rect)

    def format_title(self, metadata, value):
        return "%s (%s)" % (metadata.label, value)

    def _render_circle(self, point, radius, metadata, value):
        return metadata.wrap_link(
            "<circle cx='%s' cy='%s' r='%s' data-value='%s' data-name='%s'>"
            "<title>%s</title>"
            "</circle>" % (
                point.x,
                point.y,
                radius,
                value,
                metadata.label,
                self.format_title(metadata, value),
            )
        )

    def render(self, data, circle_width=0, class_prefix=default_prefix):
        accumulate = [[0] * len(data.items) for i in data.range_records]
        global_max = 0
        for r_id in data.range_records:
            total = 0
            for it_id in data.range_items:
                accumulate[r_id][it_id] = total
                total +=  data(r_id, it_id)
            if total > global_max:
                global_max = total
        global_max = float(global_max)

        svg_paths = ""
        svg_points = ""

        for it_id, item in reversed(list(data.enumerated_items)):
            start = self._value_point(accumulate[0][it_id] / global_max, 0, len(data.records))
            path = "M %s L " % start
            circles = ""
            for r_id, record in data.enumerated_records:
                value =  data(r_id, it_id)
                point_y = (value + accumulate[r_id][it_id]) / global_max
                point = self._value_point(point_y, r_id, len(data.records))
                path += str(point) + " "
                if value:
                    circles += self._render_circle(point, circle_width, record, value)
            for r_id in reversed(data.range_records):
                point_y = accumulate[r_id][it_id] / global_max
                point = self._value_point(point_y, r_id, len(data.records))
                path += str(point) + " "

            if circles:
                svg_points += "<g class='%s'>%s</g>\n" % (
                    escape(class_prefix + item.id),
                    circles
                )

            svg_paths += item.wrap_link(
                "<path class='%s' d='%s'><title>%s</title></path>\n" % (
                    escape(class_prefix + item.id),
                    path,
                    item.label
                )
            )

        return mark_safe(
            svg_paths +
            self.render_hgrid(len(data.records), {"class": "grid"}) +
            svg_points
        )

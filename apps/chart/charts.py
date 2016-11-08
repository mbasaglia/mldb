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
    """
    Extra information associated with chart data
    """
    def __init__(self, label="", id="", link=None, extra=None):
        self.label = label
        self.id = id
        self.link = link
        self.extra = extra

    def ctor_args(self):
        """
        Returns a tuple of arguments that can be passed to the constructor
        """
        return (self.label, self.id, self.link, self.extra)

    def wrap_link(self, svg, xmlns="xlink"):
        """
        Wraps the given SVG snippet into a link
        """
        if not self.link:
            return svg
        if xmlns and xmlns[-1] != ':':
            xmlns += ':'
        return "<a %shref='%s'>%s</a>" % (
            xmlns,
            escape(self.link),
            svg,
        )


class DataPoint(MetaData):
    """
    A data point in the graph
    """
    def __init__(self, value, *args, **kwargs):
        """
        \param value Data value
        All other arguments are forwarded to MetaData
        """
        MetaData.__init__(self, *args, **kwargs)
        self.value = value

    def normalized(self, max):
        """
        Percentage of the maximum
        """
        return float(self.value) / max if max else 1


class DataSet(MetaData):
    """
    A list of data points
    """
    def __init__(self, points, *args, **kwargs):
        """
        \param points List of DataPoints
        All other arguments are forwarded to MetaData
        """
        MetaData.__init__(self, *args, **kwargs)
        self.data = list(points)

    def max_value(self):
        """
        Computes the maximum value across all data points
        """
        return max(point.value for point in self.data) if self.data else 0

    def total(self):
        """
        Computes the sum of all data points
        """
        return sum(point.value for point in self.data)

    def append(self, point):
        """
        Appends a data point
        """
        self.data.append(point)

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return iter(self.data)

    def __getitem__(self, key):
        return self.data[key]


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
        """
        Returns a standard matrix view of the data,
        where rows are records and columns are items
        """
        return MatrixView(self)

    def transposed_view(self):
        """
        Returns a transposed matrix view of the data,
        where rows are items and columns are records
        """
        return TransposedMatrixView(self)


class MatrixView(object):
    """
    View of matrix data that is usable by charts,
    This class maps records as rows of the underlying matrix
    and items as columns
    """

    def __init__(self, data_matrix):
        self.data_matrix = data_matrix

    @property
    def records(self):
        """
        List of record meta-data
        """
        return self.data_matrix.rows

    @property
    def items(self):
        """
        List of item meta-data
        """
        return self.data_matrix.columns

    def __call__(self, record_id, item_id):
        """
        Returns a raw value at the given record/item
        """
        return self.data_matrix.values[record_id][item_id]

    @property
    def range_items(self):
        """
        Returns a range of item indices
        """
        return xrange(len(self.items))

    @property
    def range_records(self):
        """
        Returns a range of record indices
        """
        return xrange(len(self.records))

    def record_datasets(self):
        """
        Generator yielding all record datasets
        """
        for id in self.range_records:
            yield self.record_dataset(id)

    def item_datasets(self):
        """
        Generator yielding all item datasets
        """
        for id in self.range_items:
            yield self.item_dataset(id)

    def record_dataset(self, index):
        """
        Returns the DataSet corresponding to the given record
        """
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
        """
        Returns the DataSet corresponding to the given item
        """
        item = self.items[index]
        return DataSet(
            [
                DataPoint(
                    self(record_id, index),
                    *self.records[record_id].ctor_args()
                )
                for record_id in self.range_records
            ],
            *item.ctor_args()
        )

    def max_value(self):
        """
        Returns the maximum among all values in the matrix
        """
        return float(max(map(max, self.data_matrix.values)))

    @property
    def transposed(self):
        """
        Returns a view to the same underlying data that swaps items and records
        """
        return TransposedMatrixView(self.data_matrix)


class TransposedMatrixView(MatrixView):
    """
    This class maps records as columns and items as rows
    """
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
    """
    This class maps a single DataSet as a record
    """

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
        return self.data_set.max_value()

    def record_dataset(self, index):
        return self.data_set

    @property
    def transposed(self):
        return MatrixViewSingleItem(self.data_set)


class MatrixViewSingleItem(MatrixView):
    """
    This class maps a single DataSet as an item
    """
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
        return self.data_set.max_value()

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
    """
    SVG axis-aligned rectangle in user units
    """
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

    @property
    def center(self):
        return SvgPoint(
            self.x + self.width / 2.0,
            self.y + self.height / 2.0
        )

    def __repr__(self):
        return "%.2gx%.2g+%.2g+%.2g" % (self.width, self.height, self.x, self.y)


class ChartBase(object):
    """
    Base class for graphs
    """
    def __init__(self, rect, padding, normalized):
        """
        \param rect         SvgRect for the bounding box of the rendered data
        \param normalized   Whether the total of a record is to be considered as 100%
        \param padding      Extra space to leave around \p rect
        """
        self.rect = rect
        self.normalized = normalized
        self.rect = SvgRect(
            self.rect.x + padding,
            self.rect.y + padding,
            self.rect.width - padding * 2,
            self.rect.height - padding * 2,
        )

    def format_title(self, point, total):
        """
        Returns a suitable title fot the given data point
        \param point A DataPoint for the value to display
        \param total Used to display a percentage (Only if self.normalized)
        """
        if not self.normalized:
            return "%s (%s)" % (point.label, point.value)
        return "%s (%s, %.2g%%)" % (point.label, point.value, point.normalized(total) * 100)

    def point_rel2abs(self, point):
        """
        Converts a relative/normalize point into an absolute point
        """
        return SvgPoint(
            self.rect.x + self.rect.width * point.x,
            self.rect.y + self.rect.height * (1 - point.y),
        )

    def rect_rel2abs(self, rect):
        """
        Converts a relative/normalize rect into an absolute point
        """
        height = rect.height * self.rect.height
        return SvgRect(
            self.rect.x + rect.x * self.rect.width,
            self.rect.y + self.rect.height - rect.y * self.rect.height - height,
            rect.width * self.rect.width,
            height
        )

    @classmethod
    def template_tag(cls):
        """
        Returns a function usable as a template tag
        """
        def func(data, width, height, *args, **kwargs):
            rect = SvgRect(0, 0, float(width), float(height))
            options = RenderOptions(**kwargs)
            return mark_safe(cls(rect, *args).render(data, options=options))
        return func


class RenderOptions(object):
    """
    Common rendering options for charts
    """
    def __init__(self, class_prefix=None, id_prefix=None, **kwargs):
        """
        \param class_prefix Used to generate CSS classes from metadata id
        \param id_prefix    Used to generate XML IDs from metadata id
        \param kwargs       Extra attributes
        """
        self.class_prefix = class_prefix
        self.attrs = kwargs
        self.id_prefix = id_prefix

    def attribute_string(self, metadata, **kwargs):
        """
        Returns a string representing attributes for the given metasata
        """
        return make_attrs(self.attributes(metadata, **kwargs))

    def attributes(self, metadata, **kwargs):
        """
        Returns a dict of attributes
        \param metadata Metadata used to extract some values
        \param kwargs   Used to override attributes, set to None to remove them
        """
        attrs = self.attrs.copy()

        if isinstance(metadata, DataPoint):
            attrs["data-value"] = metadata.value
            attrs["data-name"] = metadata.label

        if metadata.id:
            if self.class_prefix is not None:
                attrs["class"] = self.class_prefix + metadata.id
            if self.id_prefix is not None:
                attrs["id"] = self.id_prefix + metadata.id

        attrs.update(kwargs)

        return {k: v for k, v in attrs.iteritems() if v is not None}

    def render_element(self, element, metadata, title=None, **kwargs):
        """
        Renders a full SVG element.
        \param element  Element tag name
        \param metadata MetaData
        \param title    If None, metadata.label will be used
        \param kwargs   Attribute override

        It wraps the element into the metadata link, and adds title
        and attributes as needed.
        """
        if title is None and metadata.label:
            title = metadata.label

        if title:
            end = "><title>%s</%s>" % (escape(title), element)
        else:
            end = "/>"

        return metadata.wrap_link("<%s %s%s" % (
            element,
            self.attribute_string(metadata, **kwargs),
            end
        )) + "\n"


class PieChart(ChartBase):
    """
    Pie chart
    """
    def __init__(self, rect, padding=0, radius=None, angle_start=0):
        """
        \param radius        Radius of the chart (in svg user units)
        \param center        A SvgPoint
        \param angle_start   Starting angle (in radians)
        """
        super(PieChart, self).__init__(rect, padding, True)
        self.radius = radius if radius else min(self.rect.width, self.rect.height) / 2.0
        self.center = self.rect.center
        self.angle_start = angle_start

    def _circle_point(self, angle):
        """
        Returns a coordinate tuple of a point around the pie edge
        """
        return SvgPoint(
            self.center.x + self.radius * math.cos(angle),
            self.center.y + self.radius * math.sin(angle)
        )

    def render(self, data, options=RenderOptions()):
        """
        Renders the given data as SVG paths
        \param data     A DataSet object
        \param options  Options for the chart elements
        """
        slices = ""
        angle = self.angle_start
        total = data.total()
        for point in data:
            angle_delta = math.pi * 2 * point.normalized(total)
            title = self.format_title(point, total)
            slice_path = "M %s L %s A %s 0 %s 1 %s Z" % (
                self.center,
                self._circle_point(angle),
                SvgPoint(self.radius, self.radius),
                1 if angle_delta > math.pi else 0,
                self._circle_point(angle + angle_delta),
            )
            slices += options.render_element("path", point, title, d=slice_path)
            angle += angle_delta
        return slices


class LineChartBase(ChartBase):
    """
    Common functionality for line charts
    """
    def _value_point(self, percent, index, size):
        """
        Returns an absolute point based on a data value
        \param percent  Normalized height of the point
        \param index    Index of the record
        \param size     Number of records
        """
        return self.point_rel2abs(SvgPoint(
            0 if size < 2 else float(index) / (size - 1),
            percent
        ))

    def render_hgrid(self, steps, attrs):
        """
        Renders a horizontal grid
        \param steps    Number of lines to draw
        \param attrs    Attibutes to pass to the SVG path
        """
        attrs["d"] = " ".join(
            "M %s L %s" % (
                self._value_point(0, i, steps),
                self._value_point(1, i, steps),
            )
            for i in range(steps)
        )
        return "<path %s/>" % make_attrs(attrs)

    def _render_circle(self, data_point, index, size, max, options):
        """
        Renders a SVG circle for a data point
        \param data_point   Data point for value and metadata
        \param index        Index of \p data_point in the data set
        \param size         Number of elements in the data set
        \param max          Maximum value
        \param options      Options for the chart element
        """
        pos = self._value_point(data_point.normalized(max), index, size)
        return self._render_circle_offset(pos, data_point, index, size, max, options)

    def _render_circle_offset(self, pos, data_point, index, size, max, options):
        """
        Renders a SVG circle for a data point
        \param pos          Point position (center)
        \param data_point   Data point for value and metadata
        \param index        Index of \p data_point in the data set
        \param size         Number of elements in the data set
        \param max          Maximum value
        \param options      Options for the chart element
        """
        title = self.format_title(data_point, max)
        return options.render_element("circle", data_point, title, cx=pos.x, cy=pos.y)


class LineChart(LineChartBase):
    """
    Line chart

    Each item in the data becomes a line.
    All data points have a y position relative to the maximum element.
    Records become points on the lines.
    """
    default_prefix = "line_chart_"

    def __init__(self, rect, padding=0):
        super(LineChart, self).__init__(rect, padding, False)

    def points(self, data_set, max):
        """
        Evaluates positions for the DataSet
        \param data_set DataSet for the item to represent
        \param max      Value to be considered as maximum
        """
        return [
            self._value_point(data_point.normalized(max), index, len(data_set))
            for index, data_point in enumerate(data_set)
        ]

    def render_line(self, data_set, max, options=RenderOptions()):
        """
        Renders a path representing the data set
        \param data_set     DataSet for the item to represent
        \param max          Value to be considered as maximum
        \param options      Options for the path element
        """
        points = self.points(data_set, max)
        if points:
            path_d = "M " + str(points[0]) \
                       + " L " + " ".join(map(str, points[1:]))
        else:
            path_d = ""
        return options.render_element("path", data_set, d=path_d, r=None)

    def render_points(self, data_set, max, options=RenderOptions()):
        """
        Renders circle elements for the data set
        \param data_set     DataSet for the item to represent
        \param max          Value to be considered as maximum
        \param options      Options for the chart elements
        """
        return "\n".join(
            self._render_circle(point, index, len(data_set), max, options)
            for index, point in enumerate(data_set)
        )

    def render_data_trace(self, data_set, max, options=RenderOptions()):
        """
        Renders both line and points for a single item
        \param data_set     DataSet for the item to represent
        \param max          Value to be considered as maximum
        \param options      Options for the chart elements
        """
        return "<g %s>%s%s</g>" % (
            options.attribute_string(data_set, r=None),
            self.render_line(data_set, max, options),
            self.render_points(data_set, max, options),
        )

    def render(self, data, grid_class="grid", options=RenderOptions()):
        """
        Renders the whole graph
        \param data         A matrix view or a single DataSet
        \param grid_class   CSS class for the grid path
        \param options      Options for the chart elements
        """
        if isinstance(data, DataSet):
            data = MatrixViewSingleItem(data)

        svg = self.render_hgrid(len(data.records), {"class": grid_class})
        global_max = data.max_value()
        for data_set in reversed(list(data.item_datasets())):
            svg += self.render_data_trace(data_set, global_max, options)
        return svg


class StackedBarChart(ChartBase):
    default_prefix = "stacked_bar_chart_"

    def __init__(self, rect, padding=0, normalized=False, separation=1):
        super(StackedBarChart, self).__init__(rect, normalized)
        self.separation = separation

    def render_bar(self, data_set, max, sub_rect=None, options=RenderOptions()):
        """
        Renders a stacked bar for the given data as SVG paths
        \param data         A DataSet object
        \param options      Options for the chart elements
        """
        items = ""
        y = sub_rect.y
        if not sub_rect:
            sub_rect = self.rect
        for point in data_set:
            rel_rect = SvgRect(
                x=sub_rect.x,
                y=y,
                width=sub_rect.width,
                height=float(point.value) / max * sub_rect.height
            )
            title = self.format_title(point, max)

            abs_rect = self.rect_rel2abs(rel_rect)
            items += options.render_element(
                "rect", point, title,
                x=abs_rect.x, y=abs_rect.y,
                width=abs_rect.width, height=abs_rect.height
            )
            y += rel_rect.height
        return "<g>%s</g>\n" % items

    def _subrect(self, index, size):
        """
        Gets a relative rectangle for the record at the given index
        \param index Record index
        \param size  Number of records
        """
        if size == 0:
            return self.rect
        width = 1.0 / (size + size * self.separation)
        gap_with = width * self.separation
        x = gap_with / 2 + (gap_with + width) * index
        return SvgRect(x, 0.0, width, 1.0)

    def render(self, data, options=RenderOptions()):
        """
        Renders the data matrix with the given options
        """
        bars = ""
        global_max = max(ds.total() for ds in data.item_datasets())
        for index, data_set in enumerate(data.record_datasets()):
            subrect = self._subrect(index, len(data.records))
            local_max = data_set.total() if self.normalized else global_max
            bars += self.render_bar(data_set, local_max, subrect, options)
        return bars


class StackedLineChart(LineChartBase):
    default_prefix = "stacked_line_chart_"

    def __init__(self, rect, padding=0, normalized=False):
        super(StackedLineChart, self).__init__(rect, padding, normalized)

    # TODO Clean up this ugly function
    def render(self, data, options=RenderOptions()):
        accumulate = [[0] * len(data.items) for i in data.range_records]
        local_max = []
        for r_id in data.range_records:
            total = 0.0
            for it_id in data.range_items:
                accumulate[r_id][it_id] = total
                total += data(r_id, it_id)
            local_max.append(total)
        global_max = max(local_max) if local_max else 0.0

        def max_for(record_id):
            return local_max[record_id] if self.normalized else global_max

        def normalize(value, record_id):
            return value / max_for(record_id)

        svg_paths = ""
        svg_points = ""

        for it_id, item in reversed(list(enumerate(data.items))):
            start = self._value_point(normalize(accumulate[0][it_id], 0), 0, len(data.records))
            path = "M %s L " % start
            circles = ""
            for r_id in data.range_records:
                value = data(r_id, it_id)
                pos_y = normalize(value + accumulate[r_id][it_id], r_id)
                pos = self._value_point(pos_y, r_id, len(data.records))
                path += str(pos) + " "
                if value:
                    data_point = DataPoint(value, *item.ctor_args())
                    circles += self._render_circle_offset(
                        pos,
                        data_point,
                        r_id,
                        len(data.records),
                        max_for(r_id),
                        options
                    )
            for r_id in reversed(data.range_records):
                pos_y = normalize(accumulate[r_id][it_id], r_id)
                pos = self._value_point(pos_y, r_id, len(data.records))
                path += str(pos) + " "

            if circles:
                svg_points += "<g data-item='%s'>%s</g>\n" % (item.id, circles)

            svg_paths += options.render_element("path", item, d=path, r=None)

        return (
            svg_paths +
            self.render_hgrid(len(data.records), {"class": "grid"}) +
            svg_points
        )


abstract = [ChartBase, LineChartBase]

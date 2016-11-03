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

class DataPoint(object):
    """
    A data point in the graph
    """
    def __init__(self, label, id, value):
        """
        \param label Human-readable string to identify the value
        \param id    Unique XML-friendly identifier for the data point
        \param value Data value
        """
        self.label = label
        self.id = id
        self.value = value
        self.dataset = None

    @property
    def percent(self):
        return float(self.value) / self.dataset.total


class DataSet(object):
    """
    A list of data points
    """
    def __init__(self, points, label="", id=""):
        self._data = list(points)
        self.total = 0
        for point in self._data:
            self._on_add(point)
        self.label = label
        self.id = id

    def _on_add(self, point):
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


class SvgPoint(object):
    """
    SVG coordinates in user units
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return "%s,%s " % (self.x, self.y)


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
            slices += self.render_slice(angle, angle_delta, attrs,
                                        self.format_title(point)) + "\n"
            angle += angle_delta
        return mark_safe(slices)


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
            self.relpoint(self._rel_x(index, len(data)), data_point.percent)
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

        return mark_safe(
            "<path %s>"
            "<title>%s</title>"
            "</path>" % (
            make_attrs(attrs),
            data.label
        ))

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
            "<circle %s data-value='%s' data-name='%s' %s>"
            "<title>%s</title>"
            "</circle>" % (
                self._circlepoint(index, data, point.percent),
                point.value,
                point.label,
                attrstring,
                point.label,
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

    def render(self, data, point_radius=0, id_prefix=default_prefix,
               class_prefix=default_prefix):
        return mark_safe(
            self.render_line(data, {}, id_prefix, class_prefix) +
            self.render_points(data, {"r": point_radius}, class_prefix)
        )

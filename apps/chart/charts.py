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
    def __init__(self, points):
        self._data = list(points)
        self.total = 0
        for point in self._data:
            self._on_add(point)

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
    def __init__(self,  radius,  center=None, angle_start=0):
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
            title = "%s (%s, %.2g%%)" % (point.label, point.value, point.percent * 100)
            slices += self.render_slice(angle, angle_delta, attrs, title) + "\n"
            angle += angle_delta
        return mark_safe(slices)

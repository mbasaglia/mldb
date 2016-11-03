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
from django import template

from .. import charts


register = template.Library()

@register.simple_tag
def pie_chart(data, radius, *args, **kwargs):
    return charts.PieChart(float(radius)).render(data, *args, **kwargs)


@register.simple_tag
def line_chart(data, width, height, *args, **kwargs):
    rect = charts.SvgRect(0, 0, float(width), float(height))
    return charts.LineChart(rect).render(data, *args, **kwargs)


@register.simple_tag
def line_chart_grid(steps, width, height, **attrs):
    rect = charts.SvgRect(0, 0, float(width), float(height))
    return charts.LineChart(rect).render_hgrid(steps, attrs)

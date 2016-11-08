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
import re
import inspect

from django import template

from .. import charts


register = template.Library()


def is_chart_type(obj):
    return inspect.isclass(obj) and \
           issubclass(obj, charts.ChartBase) and \
           obj not in charts.abstract


for name, member in inspect.getmembers(charts):
    if is_chart_type(member):
        snake_name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
        register.simple_tag(member.template_tag(), name=snake_name)

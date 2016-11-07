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
import os
import sys

data_lines_root = os.path.join(os.path.dirname(__file__), "lines")
data_lines_data = os.path.join(data_lines_root, "data")
data_lines_scripts = os.path.join(data_lines_root, "scripts")
data_lines_raw = os.path.join(data_lines_data, "transcripts", "raw")

sys.path.append(data_lines_scripts)

from wikitranscript import lines as parse_lines

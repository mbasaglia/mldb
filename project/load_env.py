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

py_version = "python%i.%i" % sys.version_info[:2]
root = os.path.dirname(os.path.dirname(__file__))
virtualenv_dirname = "env"
virtualenv_path = os.path.join(root, virtualenv_dirname,
                               "lib", py_version, "site-packages")
if os.path.exists(virtualenv_path) and virtualenv_path not in sys.path:
    sys.path.insert(0, virtualenv_path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

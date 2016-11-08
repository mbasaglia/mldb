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
import sys
from django.core.management.base import BaseCommand, CommandError
from ... import models


class Command(BaseCommand):
    help = 'Creates aliases for the given character'

    def add_arguments(self, argparser):
        argparser.add_argument("name", nargs="*", help="Target name")

    def handle(self, *args, **options):
        try:
            name = " ".join(options["name"])
            target = models.Character.objects.get(name=name)
        except models.Character.NotFound:
            raise CommandError("Not found: %s" % name)

        aliases = [
            models.CharacterAlias(name=line.strip())
            for line in sys.stdin
            if line.strip()
        ]
        models.CharacterAlias.objects.bulk_create(aliases)

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
from django.core.management.base import BaseCommand
from ... import parser
from ... import models

class Command(BaseCommand):
    help = 'Reassigns lines associated with name aliases'

    def add_arguments(self, argparser):
        argparser.add_argument('--from', '-f', type=int, default=0,
                               help="Episode ID to start from.")
        argparser.add_argument('--to', '-t', type=int, default=10000,
                               help="Episode ID to end to.")
        argparser.add_argument('--keep', '-k', action="store_true",
            help="Keep aliased characters (deletes them by default).")

    def handle(self, *args, **options):
        aliases = models.CharacterAlias.objects.prefetch_related("character_set")
        alias_dict = {
            alias.name: alias.character_set.all()
            for alias in aliases
        }
        aliased_characters = models.Character.objects.filter(name__in=alias_dict)

        lines = models.Line.objects.prefetch_related("characters").filter(
            episode_id__gte=options["from"],
            episode_id__lte=options["to"],
            characters__in=aliased_characters
        ).distinct()

        print "Converting %s lines" % len(lines)

        for line in lines:
            for character in line.characters.all():
                ch_aliases = alias_dict.get(character.name, None)
                if ch_aliases:
                    line.characters.add(*ch_aliases)
                    line.characters.remove(character)

        print "Aliased characters:"
        print "\n".join(aliased_characters.values_list("name", flat=True))
        if not options["keep"]:
            print "Cleaning them up..."
            aliased_characters.delete()

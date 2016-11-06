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
from ... import models
from difflib import SequenceMatcher

class Command(BaseCommand):
    help = 'Lists characters with a similar name to the given string'

    def add_arguments(self, argparser):
        argparser.add_argument("name", help="Name to look up")
        argparser.add_argument("--threshold", "-t", type=float, default=0.4,
                               help="Similarity threshold")

    def handle(self, *args, **options):
        matcher = SequenceMatcher(lambda x: x == " ")
        matcher.set_seq2(options["name"].lower())
        results = []
        for name in models.Character.objects.values_list("name", flat=True):
            matcher.set_seq1(name.lower())
            results.append((
                matcher.ratio(),
                name
            ))

        threshold = options["threshold"]
        for result in sorted(results, key=lambda x: x[0], reverse=True):
            if result[0] < threshold:
                break
            print result[1]

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
from django.core.management.base import BaseCommand, CommandError
from ... import parser

class Command(BaseCommand):
    help = 'Loads episode data'

    def add_arguments(self, argparser):
        argparser.add_argument('--list', '-l', action="store_true", help="List avaliable files")
        argparser.add_argument('--file', '-f', help="File path")
        argparser.add_argument('--season', '-s', help="Season number", type=int)
        argparser.add_argument('--episode', '-e', help="Episode number", type=int)

    def handle(self, *args, **options):
        if options["list"]:
            print "\n".join(os.listdir(parser.pony_lines_raw))
            return
        elif options["file"]:
            if "season" not in options:
                raise CommandError("Missing season (-s)")
            if "episode" not in options:
                raise CommandError("Missing episode number (-e)")
            parser.load_episode(
                os.path.join(parser.pony_lines_raw, options["file"]),
                options["season"],
                options["episode"]
            )
        else:
            raise  CommandError("Nothing to do")



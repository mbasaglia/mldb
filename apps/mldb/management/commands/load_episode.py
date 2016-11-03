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
        argparser.add_argument('--grep', '-g', action="store_true", 
            help="Grep mode, when present --file is an approximatation")
        argparser.add_argument('--file', '-f', help="File path")
        argparser.add_argument('--season', '-s', help="Season number", type=int)
        argparser.add_argument('--episode', '-e', help="Episode number", type=int)

    def file_names(self):
        return os.listdir(parser.pony_lines_raw)

    def disambiguate(self, prompt):
        files = self.file_names()
        while True:
            files = filter(lambda name: prompt in name, files)
            print "\n".join(files)
            print ""
            if len(files) > 1:
                prompt = raw_input()
            elif len(files) == 1:
                print "Loading..."
                return files[0]
            else:
                raise CommandError("No match")

    def handle(self, *args, **options):
        if options["list"]:
            print "\n".join(self.file_names())
            return
        elif options["file"]:
            filename = options["file"]
            if options["grep"]:
                filename = self.disambiguate(filename)

            if "season" not in options:
                raise CommandError("Missing season (-s)")
            if "episode" not in options:
                raise CommandError("Missing episode number (-e)")

            parser.load_episode(
                os.path.join(parser.pony_lines_raw, filename),
                options["season"],
                options["episode"]
            )
        else:
            raise  CommandError("Nothing to do")

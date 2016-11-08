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
from ... import data, models


class Command(BaseCommand):
    help = 'Loads episode data'

    def add_arguments(self, argparser):
        argparser.add_argument('--list', '-l', action="store_true",
                               help="List avaliable files")
        argparser.add_argument('--grep', '-g', action="store_true",
            help="Grep mode, when present slug is an approximatation")
        argparser.add_argument('--season', '-s', help="Season number", type=int)
        argparser.add_argument('--episode', '-e', help="Episode number", type=int)
        argparser.add_argument('--id', '-i', help="Episode ID", type=int)
        argparser.add_argument('--reload', '-r', action="store_true",
            help="Reload lines if the episode has already been loaded")
        argparser.add_argument('slug', nargs='?', help="Episode slug")

    def file_names(self):
        return os.listdir(data.data_lines_raw)

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

    def get_episode(self, options):
        slug = options["slug"]

        if options["id"] is not None:
            if not slug:
                return models.Episode.objects.get(id=options["id"])
            season, number = models.Episode.split_id(options["id"])
        else:
            season = options["season"]
            number = options["episode"]

        if options["grep"]:
            slug = self.disambiguate(slug)

        if season is None:
            raise CommandError("Missing season (-s)")
        if number is None:
            raise CommandError("Missing episode number (-e)")

        return models.Episode.get_or_create(season, number, slug)

    def handle(self, *args, **options):
        if options["list"]:
            print "\n".join(self.file_names())
            return
        elif options["slug"] or options["id"]:
            episode = self.get_episode(options)
            if options["reload"]:
                episode.line_set.all().delete()
            elif episode.line_set.exists():
                raise CommandError("This episode has already been loaded")
            episode.load_lines()
        else:
            raise CommandError("Nothing to do")

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
import urllib
import models

pony_lines_root = os.path.join(os.path.dirname(__file__), "lines")
pony_lines_data = os.path.join(pony_lines_root, "data")
pony_lines_scripts = os.path.join(pony_lines_root, "scripts")
pony_lines_raw = os.path.join(pony_lines_data, "transcripts", "raw")

sys.path.append(pony_lines_scripts)

from wikitranscript import lines


def load_episode(filename, season, number):
    """
    Creates an episode and loads its lines
    """
    slug = os.path.basename(filename)
    episode = models.Episode.objects.get_or_create(
        id=models.Episode.make_id(season, number),
        defaults={
            "slug": slug,
            "title": models.Episode.slug_to_title(slug)
        }
    )
    load_lines(filename, episode[0])

    return episode[0]


def load_lines(filename, episode):
    """
    Loads all lines from a file relating to an episode
    """
    line_objects = []
    with open(filename) as file:
        order = 0
        for names, text in lines(file):
            line_objects.append((
                models.Line(episode=episode, order=order, text=text),
                models.Character.get_or_create_all(names)
            ))
            order += 1

    models.Line.objects.bulk_create([obj[0] for obj in line_objects])
    new_lines = models.Line.objects.filter(episode=episode).order_by("order")
    for obj in line_objects:
        new_lines[obj[0].order].characters.add(*obj[1])

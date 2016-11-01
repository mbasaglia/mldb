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
from django.shortcuts import get_object_or_404
from django.forms.models import model_to_dict
from api_base import ApiBase, view
import models


class Api(ApiBase):
    @view
    def version(self):
        return self.api_version

    @view
    def characters(self):
        return list(models.Character.objects.all().values())

    @view("characters/(?P<name>[^/]*)")
    def character(self, name):
        character = get_object_or_404(
            models.Character,
            name=name
        )
        data = model_to_dict(character)
        #data["lines"] = list(
            #models.Line.objects
            #.filter(characters__in=[character])
            #.values_list("text", flat=True)
        #)
        return data

    @view
    def episodes(self):
        return [
            {
                "title": episode.title,
                "season": "%02i" % episode.season,
                "epispde": "%02i" % episode.number,
                "slug": episode.slug,
            }
            for episode in models.Episode.objects.all()
        ]

    @view("episodes/(?P<season>[0-9]+)")
    def season(self, season):
        season = int(season)
        return {
            "season": "%02i" % season,
            "episodes": [
                {
                    "title": episode.title,
                    "epispde": "%02i" % episode.number,
                    "slug": episode.slug,
                }
                for episode in models.Episode.objects
                .filter(id__gt=season*100, id__lt=(season+1)*100).all()
            ]
        }

    @view("episodes/(?P<season>[0-9]+)/(?P<number>[0-9]+)")
    def episode(self, season, number):
        season = int(season)
        number = int(number)
        episode = get_object_or_404(
            models.Episode,
            id=models.Episode.make_id(season, number)
        )
        characters = models.Line.objects.filter(episode=episode) \
            .select_related("characters__name") \
            .values_list("characters__name", flat=True) \
            .distinct()
        return {
            "season": "%02i" % season,
            "title": episode.title,
            "epispde": "%02i" % number,
            "slug": episode.slug,
            "characters": list(characters)
        }

    @view("episodes/(?P<season>[0-9]+)/(?P<number>[0-9]+)/lines")
    def lines(self, season, number):
        season = int(season)
        number = int(number)
        episode = get_object_or_404(
            models.Episode,
            id=models.Episode.make_id(season, number)
        )
        lines = models.Line.objects.filter(episode=episode) \
            .order_by("order") \
            .prefetch_related("characters")

        return {
            "season": "%02i" % season,
            "title": episode.title,
            "epispde": "%02i" % number,
            "slug": episode.slug,
            "lines": [
                {
                    "text": line.text,
                    "characters": list(line.characters.values_list("name", flat=True))
                }
                for line in lines
            ]
        }


api = Api(1)

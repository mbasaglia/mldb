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
import re
import urllib
from django.db import models
from unidecode import unidecode_expect_ascii as unidecode


class Episode(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True)
    slug = models.CharField(max_length=128, unique=True, blank=False)
    title = models.CharField(max_length=128, unique=True, blank=False)

    @property
    def season(self):
        """
        Season number of this episode
        """
        return Episode.split_id(self.id)[0]

    @property
    def number(self):
        """
        Number of this episode within the season
        """
        return Episode.split_id(self.id)[1]

    @staticmethod
    def make_id(season, number):
        """
        Creates an episode ID from season/number pair
        """
        return season * 100 + number

    @staticmethod
    def slug_to_title(slug):
        return urllib.unquote(slug.replace("_", " ")).replace(" (episode)", "")

    @staticmethod
    def split_id(id):
        """
        Splits a numeric id into a (season, number) pair
        """
        return divmod(id, 100)

    @staticmethod
    def format_id(id):
        return "%02i/%02i" % Episode.split_id(id)

    @property
    def formatted_id(self):
        return Episode.format_id(self.id)

    def __unicode__(self):
        return "%s %s" % (self.formatted_id, self.title)


class Character(models.Model):
    name = models.CharField(max_length=128, db_index=True, blank=False)
    slug = models.CharField(max_length=128, unique=True, blank=False)

    @staticmethod
    def name_to_slug(name):
        return re.sub(
            "[^a-zA-Z0-9_]",
            "",
            unidecode(name.decode("utf8")).lower().replace(" ", "_")
        )

    def __unicode__(self):
        return self.name


class Line(models.Model):
    class Meta:
        unique_together = (('episode', 'order'),)

    episode = models.ForeignKey(Episode, on_delete=models.CASCADE)
    characters = models.ManyToManyField(Character)
    order = models.SmallIntegerField()
    text = models.TextField(blank=False)

    def __unicode__(self):
        return self.text

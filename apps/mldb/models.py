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
from django.db import models
from unidecode import unidecode_expect_ascii as unidecode


class Episode(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True)
    slug = models.CharField(max_length=128, unique=True)
    title = models.CharField(max_length=128, unique=True)

    @property
    def season(self):
        """
        Season number of this episode
        """
        return self.id // 100

    @property
    def number(self):
        """
        Number of this episode within the season
        """
        return self.id % 100

    @staticmethod
    def make_id(season, number):
        """
        Creates an episode ID from season/number pair
        """
        return season * 100 + number


class Character(models.Model):
    name = models.CharField(max_length=128)
    slug = models.CharField(max_length=128, unique=True)

    def save(self, *args, **kwargs):
        """
        Updates the slug before saving
        """
        self.slug = re.sub(
            "[^a-zA-Z0-0_]",
            "",
            unidecode(self.name).lower().replace(" ", "_")
        )
        super(Character, self).save(*args, **kwargs)


class Line(models.Model):
    class Meta:
        unique_together = (('episode', 'text'),)

    episode = models.ForeignKey(Episode, on_delete=models.CASCADE)
    characters = models.ManyToManyField(Character)
    order = models.SmallIntegerField()
    text = models.TextField()

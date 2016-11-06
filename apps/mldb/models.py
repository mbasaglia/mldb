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
import colorsys

from django.db import models
from django.core.validators import RegexValidator
from django.utils.functional import cached_property

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

    @cached_property
    def previous(self):
        return Episode.objects.filter(id__lt=self.id).order_by("-id").first()

    @cached_property
    def next(self):
        return Episode.objects.filter(id__gt=self.id).order_by("id").first()

    @cached_property
    def overall_number(self):
        return Episode.objects.filter(id__lt=self.id).count() + 1

    def __unicode__(self):
        return "%s %s" % (self.formatted_id, self.title)


def ColorField(*args, **kwargs):
    return models.CharField(
        max_length=7,
        validators=[RegexValidator("#[0-9a-fA-F]{6}")],
        *args, **kwargs
    )


class CharacterAlias(models.Model):
    """
    Aliases a name to a character (or a group of characters)
    """
    class Meta:
        verbose_name_plural = "Character aliases"

    name = models.CharField(max_length=128, db_index=True, blank=False, unique=True)

    def __unicode__(self):
        return "%s -> %s" % (
            self.name,
            ",".join(map(str, self.character_set.values_list("name", flat=True)))
        )


class Character(models.Model):
    name = models.CharField(max_length=128, db_index=True, blank=False)
    slug = models.CharField(max_length=128, unique=True, blank=False)
    color = ColorField(default='#ffffff')
    outline = ColorField(default='#cccccc')
    aliases = models.ManyToManyField(CharacterAlias)

    @staticmethod
    def name_to_slug(name):
        return re.sub(
            "[^a-zA-Z0-9_]",
            "",
            unidecode(name.decode("utf8")).lower().replace(" ", "_")
        )

    @classmethod
    def get_or_create_all(cls, names):
        objects = set()
        for name in names:
            try:
                objects.add(cls.objects.get(name=name))
            except cls.DoesNotExist:
                try:
                    objects.update(
                        CharacterAlias.objects.get(name=name)
                        .character_set.all()
                    )
                except cls.DoesNotExist:
                    obj = cls(name=name, slug=cls.name_to_slug(name))
                    obj.save()
                    objects.add(obj)
        return objects

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


def annotate_characters(character_queryset):
    """
    Annotates line and episode counts and sorts a Character model queryset
    """
    return (
        character_queryset
        .annotate(n_lines=models.Count("line"),
                  episodes=models.Count("line__episode", distinct=True))
        .order_by("-n_lines", "-episodes", "name")
    )

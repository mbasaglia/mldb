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
from __future__ import unicode_literals
from django import template
from django.utils.html import format_html
from django.urls import reverse

register = template.Library()


@register.simple_tag
def character_url(character):
    return reverse("character", kwargs={"name": character.name})


@register.simple_tag
def character_link(character):
    return format_html(
        "<a href='{}'>{}</a>",
        reverse("character", kwargs={"name": character.name}),
        character.name
    )


@register.simple_tag
def episode_url(episode):
    return reverse("episode", kwargs={
        "season": "%02d" % episode.season,
        "number": "%02d" % episode.number,
    })


@register.simple_tag
def episode_link(episode):
    return format_html(
        "<a href='{}'>{}</a>",
        episode_url(episode),
        episode.title
    )


@register.simple_tag
def season_url(season):
    return reverse("season", kwargs={
        "season": "%02d" % int(season),
    })

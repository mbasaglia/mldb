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
from django.urls import reverse_lazy
from django.db.models import Count, Sum

from ..simple_page.page import Page, LinkGroup, Link
from ..mldb import models
from ..chart import charts


class MldbPage(Page):
    """
    Page with site-specific defaults
    """
    site_name = "mldb"
    footer = [
        LinkGroup(site_name, [
            Link(reverse_lazy("home"), "Home"),
            Link(reverse_lazy("characters"), "Characters"),
        ]),
        LinkGroup("API", [
            Link(reverse_lazy("api:docs"), "Documentation"),
            Link(reverse_lazy("api:explore"), "Explore"),
        ]),
        LinkGroup("Sources", [
        ]),
    ]


def annotate_characters(character_queryset):
    """
    Annotates line and episode counts and sorts a Character model queryset
    """
    return (
        character_queryset
        .annotate(n_lines=Count("line"),
                  episodes=Count("line__episode", distinct=True))
        .order_by("-episodes", "-n_lines", "name")
    )


def season_episodes(season):
    """
    Returns a queryset with all episodes from the given season
    """
    return (
        models.Episode.objects
        .filter(id__gt=season*100, id__lt=(season+1)*100)
        .order_by("id")
    )


def home(request):
    """
    Homepage view
    """
    latest_episode = models.Episode.objects.latest("id")
    latest_season = latest_episode.season if latest_episode else 0
    ctx = {
        "n_characters": models.Character.objects.count(),
        "n_lines": models.Line.objects.count(),
        "n_episodes": models.Episode.objects.count(),
        "best":  annotate_characters(models.Character.objects).first(),
        "seasons": [
            {
                "number": season,
                "episodes": season_episodes(season),
            }
            for season in range(1, latest_season + 1)
        ],
    }
    page = MldbPage("Home", "mldb/home.html")
    return page.render(request, ctx)


def characters(request):
    """
    Full list of characters
    """
    ctx = {
        "characters": annotate_characters(models.Character.objects)
    }
    page = MldbPage("Characters", "mldb/character_list.html")
    return page.render(request, ctx)


def character(request, name):
    """
    Character details
    """
    character = get_object_or_404(models.Character, name=name)
    episodes = models.Episode.objects.order_by("id")
    episode_data = charts.DataSet(
        (
            charts.DataPoint(
                ep.title,
                ep.slug,
                ep.line_set.filter(characters__in=[character]).count()
            )
            for ep in episodes
        ),
        name,
        character.slug
    )
    episodes = episodes \
        .filter(line__characters__in=[character]) \
        .annotate(n_lines=Count('id')) \
        .distinct()

    ctx = {
        "character": character,
        "episodes": episodes,
        "line_count": sum(episodes.values_list("n_lines", flat=True)),
        "episode_data": episode_data,
    }
    page = MldbPage(character.name, "mldb/character.html")
    return page.render(request, ctx)


def season(request, season):
    """
    List of episodes in the given season
    """
    season = int(season)
    ctx = {
        "season": "%02i" % season,
        "episodes": season_episodes(season),
        "characters": annotate_characters(
            models.Character.objects
            .filter(line__episode__gt=100, line__episode__lt=202)
        ).distinct()
    }
    page = MldbPage("Season %s" % season, "mldb/season.html")
    return page.render(request, ctx)


def episode(request, season, number):
    """
    Episode details
    """
    season = int(season)
    number = int(number)
    episode = get_object_or_404(
        models.Episode,
        id=models.Episode.make_id(season, number)
    )

    characters =  annotate_characters(
        models.Character.objects.filter(line__episode=episode)
    ).distinct()

    character_data = charts.DataSet(
        charts.DataPoint(ch.name, ch.slug, ch.n_lines)
        for ch in characters[0:10]
    )
    character_data.append(charts.DataPoint(
        "Other", "other",
        characters[10:].aggregate(Sum("n_lines"))["n_lines__sum"]
    ))

    ctx = {
        "episode": episode,
        "characters": characters,
        "lines": models.Line.objects
            .filter(episode=episode)
            .order_by("order"),
        "character_data": character_data
    }
    page = MldbPage(episode.title, "mldb/episode.html")
    return page.render(request, ctx)


def search(request):
    # TODO
    pass



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
import math

from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy, reverse
from django.db.models import Count, Sum, Case, When, IntegerField, Value
from django.conf import settings

from ..simple_page.page import Page, LinkGroup, Link
from ..mldb import models
from ..chart import charts
from templatetags import mldb as links
import forms
from forms import annotate_characters

class MldbPage(Page):
    """
    Page with site-specific defaults
    """
    site_name = "mldb"
    menu = LinkGroup(site_name, [
        Link(reverse_lazy("home"), "Home"),
        Link(reverse_lazy("characters"), "Characters"),
        Link(reverse_lazy("episodes"), "Episodes"),
        Link(reverse_lazy("compare"), "Compare"),
        Link(reverse_lazy("search"), "Search"),
    ])
    footer = [
        LinkGroup(site_name, [
            Link(reverse_lazy("home"), "Home"),
            Link(reverse_lazy("characters"), "Characters"),
            Link(reverse_lazy("episodes"), "Episodes"),
        ]),
        LinkGroup("API", [
            Link(reverse_lazy("api:docs"), "Documentation"),
            Link(reverse_lazy("api:explore"), "Explore"),
        ]),
        LinkGroup("Sources", [
            Link("https://github.com/mbasaglia/mldb", "MLDB"),
            Link("https://github.com/mbasaglia/Pony-Lines", "Pony-Lines"),
            Link(settings.WIKI_BASE, "MLP Wiki"),
        ]),
    ]


def season_episodes(season):
    """
    Returns a queryset with all episodes from the given season
    """
    return (
        models.Episode.objects
        .filter(id__gt=season*100, id__lt=(season+1)*100)
        .order_by("id")
    )


def seasons_context():
    """
    Returns a list that can be used in a render context to display all episodes
    divided by season
    """
    latest_episode = models.Episode.objects.latest("id")
    latest_season = latest_episode.season if latest_episode else 0
    return {
        "seasons": [
            {
                "number": season,
                "episodes": season_episodes(season),
            }
            for season in range(1, latest_season + 1)
        ]
    }


def character_lines_data(queryset, cutoff=10):
    """
    Retrieves the chart dataset from the queryset
    """
    character_lines_data = charts.DataSet(
        charts.DataPoint(ch.n_lines, *character_metadata(ch).ctor_args())
        for ch in queryset[0:cutoff]
    )

    if queryset.count() > cutoff:
        character_lines_data.append(charts.DataPoint(
            queryset[cutoff:].aggregate(Sum("n_lines"))["n_lines__sum"],
            "Other", "other"
        ))

    return character_lines_data


def character_metadata(character):
    return charts.MetaData(
        character.name,
        character.slug,
        links.character_url(character),
        character
    )


def episode_metadata(episode):
    return charts.MetaData(
        episode.title,
        episode.slug,
        links.episode_url(episode),
        character
    )


def home(request):
    """
    Homepage view
    """
    ctx = {
        "n_characters": models.Character.objects.count(),
        "n_lines": models.Line.objects.count(),
        "n_episodes": models.Episode.objects.count(),
        "best":  annotate_characters(models.Character.objects).first(),
    }
    ctx.update(seasons_context())
    page = MldbPage("Home", "mldb/home.html")
    return page.render(request, ctx)


def episodes(request):
    """
    Episode list
    """
    ctx = seasons_context()
    page = MldbPage("Home", "mldb/episode_list.html")
    return page.render(request, ctx)


def characters(request):
    """
    Full list of characters
    """
    characters = annotate_characters(models.Character.objects)
    ctx = {
        "characters": characters,
        "character_lines_data": character_lines_data(characters),
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
                ep.line_set.filter(characters__in=[character]).count(),
                *episode_metadata(ep).ctor_args()
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
    page.breadcrumbs.links = [
        Link(reverse("characters"), "Characters"),
        Link(links.character_url(character), name),
    ]
    return page.render(request, ctx)


def get_trends_data(characters, episodes):
    """
    Returnds a data matrix mapping episodes * characters to number of lines
    """
    return charts.DataMatrix(
        [ character_metadata(character) for character in characters ],
        [
            episode_metadata(episode)
            for episode in episodes
        ],
        [
            episodes.annotate(n_lines=Sum(Case(
                When(line__characters__in=[character], then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            ))).values_list("n_lines", flat=True)
            # The query above is similar to
            # .filter(line__characters__in=[character])
            # .annotate(n_lines=Count("line__id"))
            # but it keeps all of the episodes, even without matchin lines
            for character in characters
        ]
    )


def season(request, season):
    """
    List of episodes in the given season
    """
    season = int(season)
    characters =  annotate_characters(
        models.Character.objects
        .filter(line__episode__gt=season*100, line__episode__lt=(season+1)*100)
    ).distinct()

    episodes = season_episodes(season)
    cutoff = 10

    trends_data = get_trends_data(characters[:cutoff], episodes)
    trends_data.rows.append(charts.MetaData("Other", "other"))
    trends_data.values.append(
        list(characters[cutoff:].values_list("n_lines", flat=True))
    )

    ctx = {
        "season": "%02i" % season,
        "episodes": episodes,
        "characters": characters,
        "character_lines_data": character_lines_data(characters),
        "trends_data": trends_data,
    }
    page = MldbPage("Season %s" % season, "mldb/season.html")
    page.breadcrumbs.links = [
        Link(reverse("episodes"), "Episodes"),
        Link(links.season_url(season), "Season %s" % season),
    ]
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

    ctx = {
        "episode": episode,
        "characters": characters,
        "lines": models.Line.objects
            .filter(episode=episode)
            .prefetch_related("characters")
            .order_by("order"),
        "character_lines_data": character_lines_data(characters),
        "wiki_url": settings.WIKI_BASE,
    }
    page = MldbPage(episode.title, "mldb/episode.html")
    page.breadcrumbs.links = [
        Link(reverse("episodes"), "Episodes"),
        Link(links.season_url(season), "Season %s" % season),
        Link(request.path, episode.title),
    ]
    return page.render(request, ctx)


def search(request):
    results = None
    pages = 0
    curpage = 0
    max_results = settings.SEARCH_MAX_RESULTS

    if "q" in request.GET:
        form = forms.SearchForm(request.GET)

        if form.is_valid():
            results = models.Line.objects

            characters = form.cleaned_data["characters"]
            if characters:
                results = results.filter(characters__in=characters)
            else:
                results = results.all()
            # TODO: Proper fulltext search
            results = results.filter(text__contains=form.cleaned_data["query"])
            pages = int(math.ceil(float(results.count()) / max_results))
            start = max_results * curpage
            results = results[start:start + max_results] \
                .prefetch_related("episode")
    else:
        form = forms.SearchForm()

    ctx = {
        "form": form,
        "results": results,
        "pages": pages,
        "curpage": curpage,
    }
    page = MldbPage("Search", "mldb/search.html")
    return page.render(request, ctx)


def compare(request):
    ctx = {
        "show_results": False
    }
    if request.GET:
        form = forms.CompareForm(request.GET)
        if form.is_valid():
            characters = form.cleaned_data["characters"]
            episodes = form.cleaned_data["episode_range"]
            ctx.update({
                "show_results": True,
                "characters": characters,
                "episodes": episodes,
                "character_lines_data": character_lines_data(characters),
                "trends_data": get_trends_data(characters, episodes),
            })
    else:
        form = forms.CompareForm()

    ctx["form"] = form

    page = MldbPage("Compare Characters", "mldb/compare.html")
    return page.render(request, ctx)

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

from ..simple_page.page import Page, LinkGroup, Link, Resource
from ..mldb import models
from ..chart import charts
from templatetags import mldb as links
import forms


class MldbPage(Page):
    """
    Page with site-specific defaults
    """
    site_name = "mldb"

    def __init__(self):
        super(MldbPage, self).__init__()

        if not self.block_contents:
            self.block_contents = "mldb/%s.html" % self.slug()

        self.menu = LinkGroup(self.site_name, [
            Home.link(),
            Characters.link(),
            Episodes.link(),
            Search.link(),
            Link(reverse_lazy("admin:index"), "Admin", lambda r: r.user.is_staff),
        ])

        self.footer = [
        LinkGroup(self.site_name, [
            Home.link(),
            Characters.link(),
            Episodes.link(),
            Compare.link(),
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


def character_lines_data(detailed, other=None):
    """
    Retrieves the chart dataset from the queryset
    """
    character_lines_data = charts.DataSet(
        charts.DataPoint(ch.n_lines, *character_metadata(ch).ctor_args())
        for ch in detailed
    )

    if other is not None:
        character_lines_data.append(charts.DataPoint(
            sum(ch.n_lines for ch in other),
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
        episode
    )


def count_lines_for(characters, episodes):
    # This query is similar to
    # .filter(line__characters__in=[character])
    # .annotate(n_lines=Count("line__id"))
    # but it keeps all of the episodes, even without matchin lines
    return list(
        episodes.annotate(n_lines=Sum(Case(
            When(line__characters__in=list(characters), then=Value(1)),
            default=Value(0),
            output_field=IntegerField()
        ))).values_list("n_lines", flat=True)
    )


def get_trends_data(characters, episodes):
    """
    Returns a data matrix mapping episodes * characters to number of lines
    """
    return charts.DataMatrix(
        [
            character_metadata(character)
            for character in characters
        ],
        [
            episode_metadata(episode)
            for episode in episodes
        ],
        [
            count_lines_for([character], episodes)
            for character in characters
        ]
    )


def cutoff(characters, threshold=10):
    return characters[:threshold], characters[threshold:]


class Home(MldbPage):
    """
    Homepage view
    """
    def get(self, request):
        ctx = {
            "n_characters": models.Character.objects.count(),
            "n_lines": models.Line.objects.count(),
            "n_episodes": models.Episode.objects.count(),
            "best":  models.annotate_characters(models.Character.objects).first(),
        }
        ctx.update(seasons_context())

        return self.render(request, ctx)


class Episodes(MldbPage):
    """
    Episode list
    """
    block_contents = "mldb/episode_list.html"

    def __init__(self):
        super(Episodes, self).__init__()

        self.breadcrumbs = LinkGroup([
            Episodes.link(),
            Link(reverse_lazy("admin:mldb_episode_changelist"), "Edit", "mldb.change_episode"),
        ])

    def get(self, request):
        return self.render(request, seasons_context())


svg_css_resource = Resource(Resource.Style|Resource.Template, "mldb/svg.css")


class Season(MldbPage):
    """
    List of episodes in the given season
    """
    def __init__(self, season):
        super(Season, self).__init__()
        self.season = int(season)
        self.breadcrumbs = LinkGroup([
            Episodes.link(),
            Link(links.season_url(self.season), "Season %s" % self.season)
        ])
        self.title = "Season %s" % self.season
        self.resources.append(svg_css_resource)

    def get(self, request):
        characters = models.annotate_characters(
            models.Character.objects
            .filter(line__episode__gt=self.season*100,
                    line__episode__lt=(self.season+1)*100)
        ).distinct()

        episodes = season_episodes(self.season)
        characters = list(characters)
        detailed, other = cutoff(characters)

        trends_data = get_trends_data(detailed, episodes)
        trends_data.rows.append(charts.MetaData("Other", "other"))
        trends_data.values.append(count_lines_for(other, episodes))

        ctx = {
            "season": "%02i" % self.season,
            "episodes": episodes,
            "characters": characters,
            "character_lines_data": character_lines_data(detailed, other),
            "trends_data": trends_data,
        }
        return self.render(request, ctx)


class Episode(MldbPage):
    """
    Episode details
    """
    def __init__(self, season, number):
        super(Episode, self).__init__()

        self.season = int(season)
        self.number = int(number)
        self.episode = get_object_or_404(
            models.Episode,
            id=models.Episode.make_id(self.season, self.number)
        )
        self.title = self.episode.title

        self.breadcrumbs = LinkGroup([
            Episodes.link(),
            Link(links.season_url(self.season), "Season %s" % self.season),
            Link(links.episode_url(self.episode), self.episode.title),
            Link(reverse("admin:mldb_episode_change", args=[self.episode.id]),
                 "Edit", "mldb.change_episode"),
        ])
        self.resources.append(svg_css_resource)

    def get(self, request):
        characters = list(models.annotate_characters(
            models.Character.objects.filter(line__episode=self.episode)
        ).distinct())

        detailed, other = cutoff(characters)

        ctx = {
            "episode": self.episode,
            "characters": characters,
            "lines": models.Line.objects
                .filter(episode=self.episode)
                .prefetch_related("characters")
                .order_by("order"),
            "character_lines_data": character_lines_data(detailed, other),
            "wiki_url": settings.WIKI_BASE,
        }
        return self.render(request, ctx)


class Characters(MldbPage):
    """
    Full list of characters
    """
    block_contents = "mldb/character_list.html"

    def __init__(self):
        super(Characters, self).__init__()

        self.breadcrumbs = LinkGroup([
            Characters.link(),
            Compare.link(),
            Link(reverse("admin:mldb_character_changelist"), "Edit", "mldb.change_character")
        ])
        self.resources.append(svg_css_resource)

    def get(self, request):
        characters = list(models.annotate_characters(models.Character.objects))
        detailed, other = cutoff(characters)

        ctx = {
            "characters": characters,
            "character_lines_data": character_lines_data(detailed, other),
        }
        return self.render(request, ctx)


class Character(MldbPage):
    """
    Character details
    """
    def __init__(self, name):
        super(Character, self).__init__()

        self.character = get_object_or_404(models.Character, name=name)
        self.title = self.character.name
        self.breadcrumbs = LinkGroup([
            Characters.link(),
            Link(links.character_url(self.character), name),
            Link(reverse("admin:mldb_character_change", args=[self.character.id]),
                 "Edit", "mldb.change_character"),
        ])
        self.resources.append(svg_css_resource)

    def get(self, request):
        episodes = models.Episode.objects.order_by("id")
        episode_data = charts.DataSet(
            (
                charts.DataPoint(
                    ep.line_set.filter(characters__in=[self.character]).count(),
                    *episode_metadata(ep).ctor_args()
                )
                for ep in episodes
            ),
            self.character.name,
            self.character.slug
        )
        episodes = episodes \
            .filter(line__characters__in=[self.character]) \
            .annotate(n_lines=Count('id')) \
            .distinct()

        ctx = {
            "character": self.character,
            "characters": [self.character],
            "episodes": episodes,
            "line_count": sum(episodes.values_list("n_lines", flat=True)),
            "episode_data": episode_data,
        }
        return self.render(request, ctx)


class Search(MldbPage):
    def get(self, request):
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
        return self.render(request, ctx)


class Compare(MldbPage):
    title = "Compare Characters"

    def __init__(self):
        super(Compare, self).__init__()
        self.breadcrumbs = LinkGroup([
            Characters.link(),
            Compare.link(),
        ])
        self.resources.append(svg_css_resource)

    def get(self, request):
        ctx = {
            "show_results": False
        }
        if request.GET:
            form = forms.CompareForm(request.GET)
            if form.is_valid():
                characters = list(form.cleaned_data["characters"])
                episodes = form.cleaned_data["episode_range"]
                trends_data = get_trends_data(characters, episodes)
                lines_data = character_lines_data(characters, None)
                if form.cleaned_data["include_other"]:
                    other_characters = models.annotate_characters(
                        models.Character.objects.exclude(id__in=[ch.id for ch in characters])
                    )
                    other_characters_lines = count_lines_for(other_characters, episodes)
                    trends_data.rows.append(charts.MetaData("Other", "other"))
                    trends_data.values.append(other_characters_lines)
                    lines_data.append(charts.DataPoint(
                        sum(other_characters_lines),
                        "Other", "other"
                    ))
                ctx.update({
                    "show_results": True,
                    "characters": characters,
                    "episodes": list(episodes),
                    "character_lines_data": lines_data,
                    "trends_data": trends_data,
                })
        else:
            form = forms.CompareForm()

        ctx["form"] = form

        return self.render(request, ctx)

    @classmethod
    def link(cls):
        return Link(reverse_lazy(cls.slug()), "Compare")

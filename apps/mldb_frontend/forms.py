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
from django import forms
from django.db.models import Count
from ..mldb import models


def annotate_characters(character_queryset):
    """
    Annotates line and episode counts and sorts a Character model queryset
    """
    return (
        character_queryset
        .annotate(n_lines=Count("line"),
                  episodes=Count("line__episode", distinct=True))
        .order_by("-n_lines", "-episodes", "name")
    )


class MultipleCharactersField(forms.ModelMultipleChoiceField):
    def __init__(self, queryset=None, min=0, max=6, *args, **kwargs):
        if queryset is None:
            queryset = annotate_characters(models.Character.objects.all())
        super(MultipleCharactersField, self).__init__(queryset, *args, **kwargs)
        self.min_characters = min
        self.max_characters = max

    def clean(self, value):
        if len(value) < self.min_characters:
            raise forms.ValidationError(
                "You need to select at least %s characters." %
                self.min_characters
            )
        if len(value) > self.max_characters:
            raise forms.ValidationError(
                "You can't select more than %s characters." %
                self.max_characters
            )
        return self.queryset.filter(id__in=value)


class EpisodeField(forms.ModelChoiceField):
    default_queryset = models.Episode.objects.all()

    def __init__(self, queryset=None, *args, **kwargs):
        if queryset is None:
            queryset = EpisodeField.default_queryset
        super(EpisodeField, self).__init__(queryset, *args, **kwargs)


class SearchForm(forms.Form):
    query = forms.CharField(label="Search")
    characters = MultipleCharactersField(required=False)

    def add_prefix(self, field_name):
        if field_name == "query":
            field_name = "q"
        return super(SearchForm, self).add_prefix(field_name)


class CompareForm(forms.Form):
    characters = MultipleCharactersField(min=2, required=False)
    episode_start = EpisodeField(required=False, label="From",
                                 initial=EpisodeField.default_queryset.first())
    episode_finish = EpisodeField(required=False, label="To",
                                 initial=EpisodeField.default_queryset.last())
    include_other = forms.BooleanField(required=False)

    def clean(self):
        data = super(CompareForm, self).clean()
        episode_start = data["episode_start"]
        episode_finish = data["episode_finish"]

        if episode_finish.id < episode_start.id:
            temp = episode_start.id
            episode_start = episode_finish
            episode_finish = temp

        data["episode_range"] = models.Episode.objects.filter(
            id__gte=episode_start.id,
            id__lte=episode_finish.id,
        )
        return data

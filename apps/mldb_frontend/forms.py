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

class SearchForm(forms.Form):
    query = forms.CharField(label="Search")
    characters = forms.ModelMultipleChoiceField(
        queryset=annotate_characters(models.Character.objects.all()),
        required=False
    )
    max_characters = 5

    def clean_characters(self):
        value = self.cleaned_data['characters']
        if len(value) > self.max_characters:
            raise forms.ValidationError(
                "You can't select more than %s characters." %
                self.max_characters
            )
        return value

    def add_prefix(self, field_name):
        if field_name == "query":
            field_name = "q"
        return super(SearchForm, self).add_prefix(field_name)

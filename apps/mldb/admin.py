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
from django.contrib import admin
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from . import models


class CharacterAdmin(admin.ModelAdmin):
    filter_horizontal = ('aliases',)

    def get_queryset(self, request):
        queryset = super(CharacterAdmin, self).get_queryset(request)
        return models.annotate_characters(queryset)


class CharacterAliasAdminForm(forms.ModelForm):
    characters = forms.ModelMultipleChoiceField(
        queryset=models.annotate_characters(models.Character.objects.all()),
        required=False,
        widget=FilteredSelectMultiple("Characters", False)
    )

    class Meta:
        model = models.CharacterAlias
        fields = ["name"]

    def __init__(self, *args, **kwargs):
        super(CharacterAliasAdminForm, self).__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields['characters'].initial = self.instance.character_set.all()

    def save(self, commit=True):
        character_alias = super(CharacterAliasAdminForm, self).save(commit=False)

        if commit:
            character_alias.save()

        if character_alias.pk:
            character_alias.character_set = self.cleaned_data['characters']
        self.save_m2m()

        return character_alias


class CharacterAliasAdmin(admin.ModelAdmin):
    form = CharacterAliasAdminForm


admin.site.register(models.Episode)
admin.site.register(models.Character, CharacterAdmin)
admin.site.register(models.Line)
admin.site.register(models.CharacterAlias, CharacterAliasAdmin)

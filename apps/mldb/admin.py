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
from django.db.models import Count
from . import models


class CharacterAdmin(admin.ModelAdmin):
    filter_horizontal = ("aliases",)
    search_fields = ("name", )
    list_display = ("name", "color_field",)

    def get_queryset(self, request):
        queryset = super(CharacterAdmin, self).get_queryset(request)
        return models.annotate_characters(queryset)

    def color_field(self, obj):
        return """<div style='
            background: %s;
            border: 3px solid %s;
            width: 16px;
            height: 16px;
        '></div>""".replace("\n", "") % (obj.color, obj.outline)
    color_field.allow_tags = True
    color_field.short_description = 'Color'


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


def has_reverse_key_filter(relation):

    class HasReverseKeyFilter(admin.SimpleListFilter):
        title = "Has related %s" % relation
        parameter_name = relation

        def lookups(self, request, model_admin):
            return (
                (1, "Yes"),
                (0, "No"),
            )

        def queryset(self, request, queryset):
            if self.value() is None:
                return queryset
            annotated = queryset.annotate(count=Count(relation))
            value = int(self.value())
            if value == 1:
                return annotated.filter(count__gt=0)
            elif value == 0:
                return annotated.filter(count=0)
            return annotated
    return HasReverseKeyFilter


class CharacterAliasAdmin(admin.ModelAdmin):
    form = CharacterAliasAdminForm
    list_filter = (has_reverse_key_filter("character"),)


class EpisodeAdmin(admin.ModelAdmin):
    ordering = ("id",)

admin.site.register(models.Episode, EpisodeAdmin)
admin.site.register(models.Character, CharacterAdmin)
admin.site.register(models.Line)
admin.site.register(models.CharacterAlias, CharacterAliasAdmin)

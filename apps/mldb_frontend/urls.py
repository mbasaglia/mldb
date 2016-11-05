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
from django.conf.urls import url

import views


urlpatterns = [
    url(r'^$', views.home, name="home"),
    url(r'^episodes/?$', views.episodes, name="episodes"),
    url(r'^episodes/(?P<season>[0-9]+)/?$', views.season, name="season"),
    url(r'^episodes/(?P<season>[0-9]+)/(?P<number>[0-9]+)/?$', views.episode, name="episode"),
    url(r'^search/?$', views.search, name="search"),
    url(r'^characters/?$', views.characters, name="characters"),
    url(r'^characters/compare/?$', views.compare, name="compare"),
    url(r'^(?P<name>.*?)/?$', views.character, name="character"),
]

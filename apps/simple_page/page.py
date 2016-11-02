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
from django.shortcuts import render


class Link(object):
    def __init__(self, url, text):
        self.url = url
        self.text = text


class LinkGroup(object):
    def __init__(self, title="", links=[]):
        self.title = title
        self.links = links

    def add_link(self, link):
        self.links.append(link)


class Page(object):
    site_name = ""
    template_root = "simple_page/"
    base_template = template_root + "base.html"

    def __init__(self, title, blocks={"head": None, "contents": None}):
        self.title = title
        self.menu = LinkGroup()
        self.current_page = None # Url in menu
        self.breadcrumbs = LinkGroup()
        self.footer = [] # List of link groups
        self.blocks = blocks # Dict block name -> template path

    def context(self, extra_context):
        ctx = self._obj_to_dict(Page)
        ctx.update(self._obj_to_dict(self))
        ctx.update(self.blocks)
        ctx.update(extra_context)
        return ctx

    def render(self, request, extra_context={}, status_code=None):
        return render(request, self.base_template, self.context(extra_context), status_code)

    def _obj_to_dict(self, object):
        return {
            name: val
            for name, val in vars(object).iteritems()
            if not name.startswith("_")
        }

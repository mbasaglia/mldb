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

    def __iter__(self):
        return iter(self.links)

    def __contains__(self, url):
        if isinstance(url, Link):
            url = url.url
        return any(link.url == url for link in self.links)

    def __nonzero__(self):
        return len(self.links)


class Page(object):
    site_name = ""
    template_root = "simple_page/"
    base_template = template_root + "base.html"
    footer = [] # List of link groups
    menu = LinkGroup()

    def __init__(self, title, blocks):
        self.title = title
        self.current_page = None # Url in menu
        self.breadcrumbs = LinkGroup()
        if type(blocks) is str:
            self.blocks = {
                "contents": blocks,
                "head": self.template_root + "inline_css.html",
            }
        else:
            self.blocks = blocks # Dict block name -> template path

    def context(self, extra_context):
        ctx = {
            "page": self
        }
        ctx.update(extra_context)
        return ctx

    def render(self, request, extra_context={}, status_code=None):
        return render(
            request,
            self.base_template,
            self.context(extra_context),
            status_code
        )

    def _obj_to_dict(self, object):
        return {
            name: val
            for name, val in vars(object).iteritems()
            if not name.startswith("_")
        }

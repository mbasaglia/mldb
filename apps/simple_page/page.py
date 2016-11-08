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
from __future__ import unicode_literals
from django.shortcuts import render
from django.conf.urls import url
from django.urls import reverse_lazy
from django.utils.html import format_html
from django.template.loader import render_to_string


class Link(object):
    def __init__(self, url, text, condition=None):
        self.url = url
        self.text = text
        if type(condition) is str:
            self.condition = lambda request: request.user.has_perm("mldb.change_episode")
        else:
            self.condition = condition

    def visible(self, request):
        return not self.condition or self.condition(request)


class LinkGroup(object):
    def __init__(self, title="", links=[]):
        if type(title) is list and not links:
            self.links = title
            self.title = ""
        else:
            self.title = title
            self.links = links

    def add_link(self, *links):
        for link in links:
            self.links.append(link)

    def __iter__(self):
        return iter(self.links)

    def __contains__(self, url):
        if isinstance(url, Link):
            url = url.url
        return any(link.url == url for link in self.links)

    def __nonzero__(self):
        return len(self.links)


class Resource(object):
    # Load flags:
    Url      = 0x01 # The resource links to this url when rendered
    Template = 0x02 # The resource includes the remplate when rendered
    Text     = 0x04 # The resource includes this hardcoded value when rendered
    # Type flags
    Script   = 0x10 # The resource is a script
    Style    = 0x20 # The resource is stylesheet
    Custom   = 0x40 # The resource is some custom HTML string

    def __init__(self, flags, target):
        self.flags = flags
        self.target = target

    def render(self, context):
        return format_html(self._template(), self._contents(context))

    def _contents(self, context):
        if self.flags & Resource.Url or self.flags & Resource.Text:
            return self.target
        elif self.flags & Resource.Template:
            return render_to_string(self.target, context)
        raise ValueError("Unknown flags")

    def _template(self):
        if self.flags & Resource.Script:
            if self.flags & Resource.Url:
                return "<script src='{}'></script>"
            else:
                return "<script>{}</script>"
        elif self.flags & Resource.Style:
            if self.flags & Resource.Url:
                return "<link rel='stylesheet' href='{}' />"
            else:
                return "<style>{}</style>"
        elif self.flags & Resource.Custom:
            return "{}"
        raise ValueError("Unknown flags")


class Page(object):
    site_name = ""
    template_root = "simple_page/"
    base_template = template_root + "base.html"
    footer = [] # List of link groups
    menu = LinkGroup()
    breadcrumbs = LinkGroup()
    title = None
    block_contents = ""
    resources = [Resource(
        Resource.Style|Resource.Template,
        template_root + "style.css"
    )]

    def __init__(self):
        if self.title is None:
            self.title = self.__class__.__name__

    def context(self, extra_context):
        ctx = {
            "page": self
        }
        ctx["context"] = ctx
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

    @classmethod
    def slug(cls):
        return cls.__name__.lower()

    @classmethod
    def link(cls):
        return Link(reverse_lazy(cls.slug()), cls.title or cls.__name__)

    @classmethod
    def url_pattern(cls, pattern, *args, **kwargs):
        return url(pattern, cls.view, name=cls.slug(), *args, **kwargs)

    @classmethod
    def view(cls, request, *args, **kwargs):
        return cls(*args, **kwargs).get(request)

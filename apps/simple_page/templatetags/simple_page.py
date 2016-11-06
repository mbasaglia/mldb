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
import urllib

from django import template
from django.utils.html import escape, strip_tags
from django.utils.text import slugify
from django.utils.safestring import mark_safe
from django.template.base import kwarg_re, TemplateSyntaxError

from ..page import Link


register = template.Library()


def make_attrs(dict):
    """
    Returns a string containing properly formatted HTML attributes from dict
    """
    return " ".join(
        "%s='%s'" % (name, escape(value))
        for name, value in dict.iteritems()
    )


@register.simple_tag
def section_header(text, elem, id=None, **extra_attrs):
    """
    Creates a section header linking to itself
    """

    if "class" not in extra_attrs:
        extra_attrs["class"] = "section"

    return mark_safe(
        "<{elem} id='{id}' {extra_attrs}><a href='#{id}'>{text}</a></{elem}>"
        .format(
            elem=elem,
            id=id if id is not None else slugify(strip_tags(text)),
            text=text,
            extra_attrs=make_attrs(extra_attrs)
        )
    )


def token_to_args(parser, token, detect_as=True):
    """
    Parses arguments passed to {% section %}
    """
    bits = token.split_contents()[1:]
    args = []
    kwargs = {}
    asvar = None

    if detect_as and len(bits) >= 2 and bits[-2] == 'as':
        asvar = bits[-1]
        bits = bits[:-2]

    if len(bits):
        for bit in bits:
            match = kwarg_re.match(bit)
            if not match:
                raise TemplateSyntaxError("Malformed arguments")
            name, value = match.groups()
            if name:
                kwargs[name] = parser.compile_filter(value)
            else:
                args.append(parser.compile_filter(value))

    return (args, kwargs, asvar) if detect_as else (args, kwargs)


@register.tag
def section(parser, token):
    """
    Simital to section_header() but it creates a long tag to wrap the title text
    """
    args = token_to_args(parser, token)
    nodelist = parser.parse(('endsection',))
    parser.delete_first_token()
    return SectionNode(nodelist, *args)


class SectionNode(template.Node):
    """
    Template node for {% section %}
    """
    def __init__(self, nodelist, args, kwargs, asvar):
        self.nodelist = nodelist
        self.elem = str(args[0])
        self.args = args[1:]
        self.kwargs = kwargs
        self.asvar = asvar

    def render(self, context):
        args = [arg.resolve(context) for arg in self.args]
        kwargs = {
            key: val.resolve(context)
            for key, val in self.kwargs.items()
        }
        text = self.nodelist.render(context)
        result = section_header(text, self.elem, *args, **kwargs)
        if self.asvar:
            context[self.asvar] = result
            return ''
        else:
            return result


@register.simple_tag(takes_context=True)
def link(context, target, text=None, **attrs):
    """
    Renders a link.
    If the target points to the current page, it renders a span instead.
    """
    request = context["request"]

    if isinstance(target, Link):
        if not target.visible(request):
            return ""
        text = target.text
        target = target.url

    target = str(urllib.unquote(target))
    if text is None:
        text = target

    match = False
    if request.path == target:
        if "class" in attrs:
            attrs["class"] += ' ' + 'current_link'
        else:
            attrs["class"] = 'current_link'
        tag = "span"
    else:
        attrs["href"] = target
        tag = "a"
    return mark_safe("<{tag} {attrs}>{text}</{tag}>".format(
        tag=tag,
        attrs=make_attrs(attrs),
        text=text
    ))


@register.simple_tag(takes_context=True)
def if_crumb(context, url, text):
    if str(urllib.unquote(url)) in context["page"].breadcrumbs:
        return mark_safe(text)
    return ""


@register.simple_tag
def flatten_list(list, join=" ", template="{}"):
    return join.join(template.format(item) for item in list)

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
from django import template
from django.utils.html import escape, strip_tags
from django.utils.text import slugify
from django.utils.safestring import mark_safe
from django.template.base import kwarg_re, TemplateSyntaxError


register = template.Library()

@register.simple_tag
def section_header(text, elem, id=None, **extra_attrs):

    if "class" not in extra_attrs:
        extra_attrs["class"] = "section"

    extra_attrs_string =  " ".join(
        "%s='%s'" % (name, escape(value))
        for name, value in extra_attrs.iteritems()
    )

    return mark_safe(
        "<{elem} id='{id}' {extra_attrs}><a href='#{id}'>{text}</a></{elem}>"
        .format(
            elem=elem,
            id=id if id is not None else slugify(strip_tags(text)),
            text=text,
            extra_attrs=extra_attrs_string
        )
    )

def token_to_args(parser, token, detect_as=True):
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
    args = token_to_args(parser, token)
    nodelist = parser.parse(('endsection',))
    parser.delete_first_token()
    return SectionNode(nodelist, *args)


class SectionNode(template.Node):
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

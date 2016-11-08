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
import json
from copy import deepcopy
from django import http
from django.utils.six.moves.http_client import responses as http_codes
from django.conf.urls import url
from django.conf import settings


class ApiResponse(http.HttpResponse):
    def __init__(self, content, status=200, pretty=False):
        http.HttpResponse.__init__(
            self,
            self.to_string(content, pretty),
            content_type=self.mime_type,
            status=status
        )

    @classmethod
    def error(cls, code, msg=None):
        return cls({"error": msg or http_codes[code]}, code)


class JsonResponse(ApiResponse):
    """
    Api response, dumps contents as JSON
    """
    mime_type = "application/json"

    def to_string(self, content, pretty):
        if pretty:
            return json.dumps(content, indent=4)
        return json.dumps(content)


class PonResponse(ApiResponse):
    """
    Api response, dumps contents as Python object notation
    """
    mime_type = "text/plain"

    def to_string(self, content, pretty):
        return repr(content)


class ViewWrapper(object):
    """
    Wrapper around a method that exposes a view
    """
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def bound(self, object):
        """
        Binds to an object
        """
        return BoundViewWrapper(object, *self.args, **self.kwargs)


class BoundViewWrapper(object):
    """
    Wrapper around a method that exposes a view, bound to an object
    """

    def __init__(self, object, callback, pattern=None, methods={"GET", "HEAD"}):
        """
        \param name Name for the URL
        \param args Arguments to prepend to each call of the wrapped callback
        \param callback Callable to be wrapped
        \param pattern  (Optional) regex pattern for the url
        \param methods  Request methods supported by the view
        """
        self.callback = callback
        self.pattern = pattern
        self.methods = methods
        self.this = object

    def view(self, request, type, *args, **kwargs):
        """
        Acts as a view.

        This wraps the result from self.callback into
        self.response_type and rejects invalid requests.
        """
        if type not in self.this.response_types:
            return self.this.default_response.error(404, "Unknown file type")

        response_type = self.this.response_types[type]
        try:
            if not self.methods or request.method in self.methods:
                pretty = "pretty" in request.GET
                return response_type(self(*args, **kwargs), pretty=pretty)
            return response_type.error(405)
        except http.Http404:
            return response_type.error(404)
        except Exception:
            if settings.DEBUG:
                raise
            return response_type.error(500)

    def __call__(self, *args, **kwargs):
        """
        Invokes the callback
        """
        return self.callback(*((self.this,) + args), **kwargs)

    def url_pattern(self, name):
        """
        Url regex pattern for the given name
        """
        return '^%s\.(?P<type>%s)$' % (
            self.pattern or name,
            "|".join(self.this.response_types)
        )

    def url(self, name):
        """
        Returns a url object, with a view bound to \p object
        and the given name
        """
        return url(self.url_pattern(name), self.view, name=name)


def view(*args, **kwargs):
    """
    Decorates a callable as a view, can take arguments that get forwarded
    to the ViewWrapper constructor
    """

    # This branch is taken when called without arguments
    # and wraps the callable directly
    if len(args) == 1 and not kwargs and callable(args[0]):
        return ViewWrapper(args[0])

    # This branch is taken when there are arguments to forward to ViewWrapper
    def wrapper(method):
        return ViewWrapper(method, *args, **kwargs)
    return wrapper


class ApiBase(object):
    """
    Base class for API classes
    """
    response_types = {
        "json": JsonResponse,
        "py": PonResponse,
    }

    default_response = JsonResponse

    def __init__(self, version):
        """
        The constructor finds all methods decorated with @view and binds them
        to self
        """
        self.api_version = version

        for name, func in vars(self.__class__).iteritems():
            if isinstance(func, ViewWrapper):
                setattr(self, name, func.bound(self))

    def url_patterns(self, urlns="api"):
        """
        Returns a url pattern tuple, with the given url namespace
        """
        return ([
            func.url(name)
            for name, func in vars(self).iteritems()
            if isinstance(func, BoundViewWrapper)
        ] + [
            url(
                "(?P<name>.*?)(?:\.(?P<type>%s))?$" %
                    "|".join(self.response_types),
                self.not_found
            ),
        ],
        urlns
    )

    def not_found(self, response, name, type):
        """
        Fallback view
        """
        response_type = self.response_types.get(type, self.default_response)
        return response_type.error(404, "%s not found" % name)

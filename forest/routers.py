import re
from math import ceil
from urllib.parse import urlparse, quote


class RouteMatch:
    def __init__(self):
        self.route = None
        self.handler = None
        self.vars = None

def not_found(request, response_writer):
    print(str(request))
    return str(request)

class Router:
    parent = None
    routes = []
    strictSlash = False

    def __init__(self):
        self.namedRoutes = dict()
        self.not_found = not_found

    def __call__(self, path: str):
        def inner(handler):
            route = Route(self).path(path)
            route.handler = handler

            self.routes.append(route)
            return handler

        return inner

    def match(self, request, match: RouteMatch) -> bool:
        for route in self.routes:
            if route.match(request, match):
                return True
        if self.not_found:
            match.handler = self.not_found
            return True
        return False

    def handler(self, request, response_writer):
        match = RouteMatch()
        if self.match(request, match):
            handler = match.handler
        if not handler:
            handler = self.not_found
        return handler(request, response_writer)

    def getRegexpGroup(self):
        if self.parent:
            return self.parent.getRegexpGroup()
        return None


class RouteRegexpGroup:
    def __init__(self, host=None, path=None, queries=None):
        host = None
        path = None
        queries = None


class Route:
    def __init__(self, router: Router):
        self.parent = router
        self.strictSlash = router.strictSlash
        self.matchers = []
        self.handler = None
        self.regexp = None

    def path(self, tpl):
        rr = self.addRegexpMatcher(tpl)
        return self

    def addRegexpMatcher(self, tpl: str):
        self.regexp = self.getRegexpGroup()
        rr = regexp(
            tpl,
            matchHost=False,
            matchPrefix=False,
            strictSlash=False,
            useEncodedPath=False)
        self.matchers.append(rr)

    def getRegexpGroup(self) -> RouteRegexpGroup:
        if self.regexp:
            return self.regexp
        if not self.parent:
            self.parent = Router()
        regexp = self.parent.getRegexpGroup()
        if not regexp:
            self.regexp = RouteRegexpGroup()
        else:
            self.regexp = RouteRegexpGroup(
                host=regexp.host, path=regexp.path, queries=regexp.queries)
        return self.regexp

    def match(self, request, match: RouteMatch) -> bool:
        for m in self.matchers:
            if not m.match(request, match):
                return False
        if not match.route:
            match.route = self
        if not match.handler:
            match.handler = self.handler
        return True


class RouteRegexp:
    def __init__(self, template, regexp, reverse, names, strictSlash=False):
        self.template = template
        self.regexp = regexp
        self.reverse = reverse
        self.strictSlash = strictSlash
        self.names = names

    def match(self, request, match: RouteMatch) -> bool:
        path = request.path
        return self.regexp.match(path)


def regexp(tpl: str,
           matchHost: bool=False,
           matchPrefix: bool=False,
           matchQuery: bool=False,
           strictSlash: bool=False,
           useEncodedPath: bool=False) -> RouteRegexp:
    idxs = braceIndices(tpl)

    defaultPattern = "[^/]+"
    if matchQuery:
        defaultPattern = "[^?&]*"
    elif matchHost:
        defaultPattern = "[^.]+"
        matchPrefix = False
    # Only match strict slash if not matching
    if matchPrefix or matchHost or matchQuery:
        strictSlash = False

    end = 0
    names = []
    pattern = '^'
    reverse = ""
    for i, pair in enumerate(idxs):
        left, right = pair
        raw = tpl[end:left]
        end = right
        parts = tpl[left + 1:right - 1].split(':', 1)
        name = parts[0]
        patt = len(parts) == 2 and parts[1] or defaultPattern
        if not name or not patt:
            raise ValueError("missing name or pattern in %s" % tpl[left:right])
        pattern += "%s(?P<%s>%s)" % (quote(raw), name, patt)
        reverse = "%s%%s" % raw
        names.append(name)
    raw = tpl[end:]
    pattern += quote(raw)
    reg = re.compile(pattern)
    return RouteRegexp(tpl, reg, reverse, names, strictSlash)


def braceIndices(string):
    level, idx, idxs = 0, 0, []
    for i, s in enumerate(string):
        if s == '{':
            level += 1
            if level == 1:
                idx = i
        elif s == '}':
            level -= 1
            if level == 0:
                idxs.append((idx, i + 1))
            elif level < 0:
                raise ValueError("unbalanced braces in %s" % s)
    return idxs

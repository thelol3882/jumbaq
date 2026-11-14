"""The check against changes from another site, because the family session cookie
authenticates the API.

The browser adds a cookie by itself, also to a request from a sibling subdomain, which SameSite
does not stop. This header forces a CORS preflight, and CORS allows only our web app. The API
asks it for every change, also for the one that sets the cookie.
"""

from fastapi import Request

from jumbaq.core.errors import ForbiddenError

# A form or a plain fetch from another site cannot send this header without a preflight.
CSRF_HEADER = "X-Requested-With"
# An exact value, because older Android WebViews add this header by themselves with the app name.
CSRF_VALUE = "jumbaq"

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


def require_csrf_header(request: Request) -> None:
    if request.headers.get(CSRF_HEADER) != CSRF_VALUE:
        raise ForbiddenError()


def require_csrf_header_on_change(request: Request) -> None:
    if request.method not in SAFE_METHODS:
        require_csrf_header(request)

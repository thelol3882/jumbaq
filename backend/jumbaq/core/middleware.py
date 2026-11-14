import logging
import re
import time
import uuid

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from jumbaq.core.context import family_id_var, request_id_var

REQUEST_ID_HEADER = "X-Request-ID"
# A request id from the client or nginx is kept only if it looks safe to put in logs.
_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{8,128}$")

logger = logging.getLogger("jumbaq.request")


def _pick_request_id(scope: Scope) -> str:
    for name, value in scope["headers"]:
        if name == b"x-request-id":
            candidate = value.decode("latin-1")
            if _VALID_REQUEST_ID.match(candidate):
                return candidate
            break
    return uuid.uuid4().hex


class RequestContextMiddleware:
    """Sets the request id, returns it in a header and writes one log line per request.

    The id is kept in a context var (for log lines) and in the scope state (for the
    500 handler, which runs after this middleware is done).
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = _pick_request_id(scope)
        scope.setdefault("state", {})["request_id"] = request_id
        token = request_id_var.set(request_id)
        # FamilyDep sets it after it reads the cookie.
        family_token = family_id_var.set("-")
        started = time.perf_counter()
        status = 500

        async def send_with_request_id(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode("latin-1")))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        except Exception:
            # Logged here, while the request id is still in the context.
            logger.exception("unhandled error")
            raise
        finally:
            duration_ms = (time.perf_counter() - started) * 1000
            logger.info("%s %s %s %.1fms", scope["method"], scope["path"], status, duration_ms)
            family_id_var.reset(family_token)
            request_id_var.reset(token)

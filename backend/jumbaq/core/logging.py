"""Logging with the request id and the family on every line."""

import logging

from jumbaq.core.context import family_id_var, request_id_var


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        record.family_id = family_id_var.get()
        return True


def setup_logging(level: str) -> None:
    handler = logging.StreamHandler()
    handler.addFilter(ContextFilter())
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s "
            "[req=%(request_id)s family=%(family_id)s] %(message)s"
        )
    )
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
    # Our middleware writes one line per request, so the uvicorn access log is not needed.
    logging.getLogger("uvicorn.access").disabled = True

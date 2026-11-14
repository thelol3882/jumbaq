from contextvars import ContextVar

# Ids for the log lines. "-" when they are not known, for example before the cookie is read.
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
family_id_var: ContextVar[str] = ContextVar("family_id", default="-")
# True while the outbox runs a handler for the last time. A handler then gives a built-in result
# instead of raising, because a raise would leave its work unfinished for good.
last_attempt_var: ContextVar[bool] = ContextVar("last_attempt", default=False)


def is_last_attempt() -> bool:
    return last_attempt_var.get()

from contextvars import ContextVar

# Ids for the log lines. "-" when they are not known, for example before the cookie is read.
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
family_id_var: ContextVar[str] = ContextVar("family_id", default="-")

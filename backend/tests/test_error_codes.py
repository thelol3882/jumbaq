"""Error codes are translation keys of the web app, so the backend list, the web
list and the English texts must stay the same. This test fails when one of them is behind."""

import json
import re
from pathlib import Path

from jumbaq.core.error_codes import ErrorCode

WEB = Path(__file__).resolve().parents[2] / "web" / "app" / "src"
WEB_CODES = WEB / "shared" / "api" / "errorCodes.ts"
TEXTS = WEB / "i18n" / "messages" / "en.json"
# The web app's own code: the request got no answer.
WEB_ONLY = {"common.network_error"}


def web_api_codes() -> set[str]:
    source = WEB_CODES.read_text(encoding="utf-8")
    api_list = source.split("API_ERROR_CODES = [", 1)[1].split("] as const", 1)[0]
    return set(re.findall(r'"([a-z_]+\.[a-z_]+)"', api_list))


def test_codes_are_domain_dot_name_and_unique() -> None:
    values = [code.value for code in ErrorCode]

    assert len(values) == len(set(values))
    for value in values:
        assert re.fullmatch(r"[a-z]+\.[a-z_]+", value), value


def test_web_app_knows_every_code() -> None:
    assert web_api_codes() - WEB_ONLY == {code.value for code in ErrorCode}


def test_every_code_has_an_english_text() -> None:
    texts = json.loads(TEXTS.read_text(encoding="utf-8"))["common"]["errors"]

    missing = [
        code.value
        for code in ErrorCode
        if not texts.get(code.value.split(".")[0], {}).get(code.value.split(".")[1])
    ]
    assert missing == []

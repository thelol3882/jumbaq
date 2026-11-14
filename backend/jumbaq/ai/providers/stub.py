"""A provider without a network call. It reads the same data block the model would read and
writes the same story every time, one that follows the rules of the game. All tests use it,
and so does a laptop without a key."""

import json
import re
from typing import Any

from jumbaq.ai.domain import AnswerType
from jumbaq.ai.prompts import ANSWER_SLOT, CASE_PLAN_SCHEMA, DATA_TAG, Prompt
from jumbaq.ai.providers.base import Reply

_DATA = re.compile(rf"<{DATA_TAG}>\n(.*)\n</{DATA_TAG}>", re.DOTALL)
_ANSWER_TYPES = list(AnswerType)


def _data(prompt: Prompt) -> dict[str, Any]:
    found = _DATA.search(prompt.user)
    if found is None:
        raise ValueError("the prompt has no data block")
    return json.loads(found.group(1))


def _plan(case_number: int) -> dict[str, Any]:
    # s2 did it. Clues 1 and 3 rule out s1, clue 2 rules out s3, and only the last two point at s2.
    return {
        "title": f"Case {case_number}: the missing honey cake",
        "setting": "The honey cake vanished from the forest bakery before the party.",
        "suspects": [
            {"id": "s1", "name": "Felix the Fox", "description": "loves sweets more than anyone"},
            {"id": "s2", "name": "Olga the Owl", "description": "awake all night, sees it all"},
            {"id": "s3", "name": "Boris the Bear", "description": "the baker, sleepy and kind"},
        ],
        "culprit_id": "s2",
        "clues": [
            {
                "episode": 1,
                "text": "A grey feather lies by the empty plate, and Felix has only fur.",
                "suspect_id": "s1",
                "points_at": False,
            },
            {
                "episode": 2,
                "text": "Boris snored in the back room the whole night.",
                "suspect_id": "s3",
                "points_at": False,
            },
            {
                "episode": 3,
                "text": "Felix was at his grandma's all evening.",
                "suspect_id": "s1",
                "points_at": False,
            },
            {
                "episode": 4,
                "text": "Owl footprints lead away through the crumbs.",
                "suspect_id": "s2",
                "points_at": True,
            },
            {
                "episode": 5,
                "text": "Cake crumbs lead up to the hollow of the old oak.",
                "suspect_id": "s2",
                "points_at": True,
            },
        ],
        "reveal": "Olga the Owl took the cake at night to surprise her owlets. The feather "
        "and the crumbs to her oak gave her away.",
    }


def _riddle(objects: list[str], index: int) -> dict[str, Any]:
    target = objects[index % len(objects)]
    answer_type = _ANSWER_TYPES[index % len(_ANSWER_TYPES)]
    return {
        "text": f"I am somewhere in your home and my name is {target}. Find me!",
        "target_object": target,
        "answer_type": answer_type.value,
        "parent_note": f"Go to the {target} and let the kids tell you its {answer_type.value}.",
    }


def _episode(data: dict[str, Any]) -> dict[str, Any]:
    number = data["episode_number"]
    objects = data["home"]["objects"]
    names = " and ".join(kid["nickname"] for kid in data["home"]["kids"]) or "Detectives"
    played = data["earlier_episodes"]
    recap = (
        "Welcome to a new case, detectives."
        if not played
        else f"So far you found {len(played)} clues. Last time you said: {played[-1]['answer']}."
    )
    return {
        "recap": recap,
        "read_aloud": [
            f"{names}, the bakery needs you.",
            f"This is evening {number}. Look closely.",
            "Someone left a riddle on the door.",
        ],
        "riddle": _riddle(objects, number - 1),
        "hint": "Look in the room where you spend the most time.",
        "fallback_riddle": _riddle(objects, number),
        "resolution_template": f"You said {ANSWER_SLOT}. That is exactly the secret code!",
        "case_clue": data["clue_for_this_episode"]["text"],
        "cliffhanger": "But who left the riddle? Tomorrow we will know more.",
    }


class StubProvider:
    name = "stub"
    model = "stub"

    async def complete_json(self, prompt: Prompt, schema: dict[str, Any]) -> Reply:
        data = _data(prompt)
        answer = _plan(data["case_number"]) if schema is CASE_PLAN_SCHEMA else _episode(data)
        return Reply(answer, input_tokens=0, output_tokens=0)

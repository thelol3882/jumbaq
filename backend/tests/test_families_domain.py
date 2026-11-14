import pytest

from jumbaq.families import domain
from jumbaq.families.domain import NewKid
from jumbaq.families.errors import KidNicknameRepeatedError


def test_kids_with_different_nicknames_are_fine() -> None:
    domain.check_kids((NewKid("Aru", 7), NewKid("Timur", 9)))


def test_nicknames_repeat_also_in_another_case() -> None:
    with pytest.raises(KidNicknameRepeatedError):
        domain.check_kids((NewKid("Aru", 7), NewKid("aru", 9)))


def test_session_tokens_are_random_and_only_their_hash_is_kept() -> None:
    token = domain.new_session_token()

    assert token != domain.new_session_token()
    assert len(token) >= 43  # 32 bytes in base64
    assert domain.hash_session_token(token) == domain.hash_session_token(token)
    assert token not in domain.hash_session_token(token)

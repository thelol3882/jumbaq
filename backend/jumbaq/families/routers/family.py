"""The setup of a family and its session. There is no login: the cookie is the family."""

from fastapi import APIRouter, Response, status

from jumbaq.core.deps import SettingsDep
from jumbaq.families.deps import FAMILY_COOKIE, FamilyDep, FamilyServiceDep
from jumbaq.families.domain import NewKid
from jumbaq.families.schemas import FamilyCreate, FamilyOut, FamilyStateOut

router = APIRouter(tags=["families"])

_COOKIE_PATH = "/api/v1"


@router.post("/families", status_code=status.HTTP_201_CREATED)
async def create_family(
    body: FamilyCreate, families: FamilyServiceDep, settings: SettingsDep, response: Response
) -> FamilyOut:
    """The one-minute setup: kids, rooms and the household objects. Sets the session cookie,
    so a second call starts a new family. Repeated nicknames give 422 with
    `family.kid_nickname_repeated` on `kids`."""
    created = await families.create(
        body.rooms, body.objects, [NewKid(kid.nickname, kid.age) for kid in body.kids]
    )
    response.set_cookie(
        FAMILY_COOKIE,
        created.session_token,
        max_age=settings.family_cookie_days * 24 * 60 * 60,
        path=_COOKIE_PATH,
        secure=settings.family_cookie_secure,
        httponly=True,
        samesite="lax",
    )
    return FamilyOut.model_validate(created.family)


@router.get("/family")
async def get_family(family: FamilyDep, families: FamilyServiceDep) -> FamilyStateOut:
    """The family of the cookie. No cookie, or an unknown one, gives 401 `family.no_session`.
    `demo_mode` is true when the next episode may be opened at once."""
    return FamilyStateOut.model_validate(await families.get(family))

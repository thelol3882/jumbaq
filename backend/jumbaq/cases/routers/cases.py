"""The cases of a family: the current one, the accusation, the certificate and the next case."""

import uuid

from fastapi import APIRouter, status

from jumbaq.cases.deps import CaseServiceDep
from jumbaq.cases.schemas import AccusationOut, AccuseIn, CaseOut, CertificateOut, SolvedCaseOut
from jumbaq.families.deps import FamilyDep

router = APIRouter(tags=["cases"])


@router.get("/cases/current")
async def get_current_case(family: FamilyDep, cases: CaseServiceDep) -> CaseOut:
    """The newest case. Clues of episodes not yet played, the culprit and the reveal are never
    in it. 404 `case.not_found` before case 1 is opened."""
    return CaseOut.model_validate(await cases.current(family))


@router.get("/cases")
async def list_solved_cases(family: FamilyDep, cases: CaseServiceDep) -> list[SolvedCaseOut]:
    """The family's solved cases, newest first. Empty before the first one is solved."""
    return [SolvedCaseOut.model_validate(case) for case in await cases.solved(family)]


@router.post("/cases", status_code=status.HTTP_201_CREATED)
async def start_next_case(family: FamilyDep, cases: CaseServiceDep) -> CaseOut:
    """Only after the current case is solved (409 `case.not_solved`). From case 2 on it needs a
    subscription: 402 `billing.payment_required`."""
    return CaseOut.model_validate(await cases.start_next(family))


@router.post("/cases/{case_id}/accuse")
async def accuse(
    case_id: uuid.UUID, body: AccuseIn, family: FamilyDep, cases: CaseServiceDep
) -> AccusationOut:
    """Only after the last episode is played (409 `case.not_accusing`). A wrong suspect gives
    200 with `correct: false`; an id that is not a suspect gives 422 `case.unknown_suspect`."""
    return AccusationOut.model_validate(await cases.accuse(family, case_id, body.suspect_id))


@router.get("/cases/{case_id}/certificate")
async def get_certificate(
    case_id: uuid.UUID, family: FamilyDep, cases: CaseServiceDep
) -> CertificateOut:
    """Any solved case of the family, not only the current one (409 `case.not_solved`). Another
    family's case gives 404."""
    return CertificateOut.model_validate(await cases.certificate(family, case_id))

"""Whether a family may start a case. Other modules use it through billing.public."""

from jumbaq.billing import domain
from jumbaq.billing.errors import PaymentRequiredError
from jumbaq.billing.uow import BillingUoWFactory
from jumbaq.core.family import FamilyRef


class BillingAccess:
    def __init__(self, uow: BillingUoWFactory, free_cases: int) -> None:
        self._uow = uow
        self._free_cases = free_cases

    async def has_access(self, family: FamilyRef, case_number: int) -> bool:
        if case_number <= self._free_cases:
            return True
        async with self._uow() as uow:
            statuses = await uow.subscriptions.statuses(family)
        return domain.has_access(case_number, self._free_cases, statuses)

    async def require_access(self, family: FamilyRef, case_number: int) -> None:
        if not await self.has_access(family, case_number):
            raise PaymentRequiredError()

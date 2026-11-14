"""What other modules may use from billing: the access check before a case, its error and the
event after a payment."""

from functools import partial

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from jumbaq.billing.errors import PaymentRequiredError
from jumbaq.billing.events import SubscriptionActivated
from jumbaq.billing.services.access import BillingAccess
from jumbaq.billing.uow import BillingUoW
from jumbaq.core.config import Settings


def build_billing_access(
    sessionmaker: async_sessionmaker[AsyncSession], settings: Settings
) -> BillingAccess:
    return BillingAccess(partial(BillingUoW, sessionmaker), settings.billing_free_cases)


__all__ = [
    "BillingAccess",
    "PaymentRequiredError",
    "SubscriptionActivated",
    "build_billing_access",
]

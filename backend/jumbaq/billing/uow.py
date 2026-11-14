from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from jumbaq.billing.queries import BillingQueries
from jumbaq.billing.repositories.sql import SqlSubscriptionRepository
from jumbaq.billing.repositories.subscriptions import SubscriptionRepository
from jumbaq.core.db import UnitOfWork


class BillingUoW(UnitOfWork):
    subscriptions: SubscriptionRepository
    queries: BillingQueries

    def _attach(self, session: AsyncSession) -> None:
        self.subscriptions = SqlSubscriptionRepository(session)
        self.queries = BillingQueries(session)


BillingUoWFactory = Callable[[], BillingUoW]

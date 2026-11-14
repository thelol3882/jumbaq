from functools import partial
from typing import Annotated

from fastapi import Depends

from jumbaq.billing.providers.base import PaymentProvider
from jumbaq.billing.providers.stripe_provider import StripeProvider
from jumbaq.billing.services.subscriptions import SubscriptionService
from jumbaq.billing.uow import BillingUoW, BillingUoWFactory
from jumbaq.core.config import Settings
from jumbaq.core.deps import ClockDep, SessionmakerDep, SettingsDep, TaskQueueDep
from jumbaq.core.outbox import nudge_worker


def get_uow_factory(sessionmaker: SessionmakerDep, queue: TaskQueueDep) -> BillingUoWFactory:
    return partial(BillingUoW, sessionmaker, nudge=nudge_worker(queue))


BillingUoWFactoryDep = Annotated[BillingUoWFactory, Depends(get_uow_factory)]


def build_payment_provider(settings: Settings) -> PaymentProvider:
    secret = settings.stripe_secret_key
    webhook = settings.stripe_webhook_secret
    return StripeProvider(
        secret.get_secret_value() if secret else None,
        webhook.get_secret_value() if webhook else None,
        settings.billing_price_cents,
        settings.billing_currency,
    )


def get_payment_provider(settings: SettingsDep) -> PaymentProvider:
    return build_payment_provider(settings)


PaymentProviderDep = Annotated[PaymentProvider, Depends(get_payment_provider)]


def get_subscription_service(
    uow: BillingUoWFactoryDep, provider: PaymentProviderDep, clock: ClockDep, settings: SettingsDep
) -> SubscriptionService:
    return SubscriptionService(uow, provider, clock, settings.web_app_url)


SubscriptionServiceDep = Annotated[SubscriptionService, Depends(get_subscription_service)]

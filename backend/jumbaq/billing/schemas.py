from datetime import datetime

from pydantic import BaseModel, ConfigDict

from jumbaq.billing.domain import SubscriptionStatus


class CheckoutOut(BaseModel):
    # The web app sends the parent to this payment page.
    url: str


class PortalOut(BaseModel):
    # The web app sends the parent to this page to manage or cancel the subscription.
    url: str


class SubscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: SubscriptionStatus | None
    active: bool
    # Set while the subscription is active but canceled: access lasts until this time.
    cancels_at: datetime | None


class WebhookOut(BaseModel):
    received: bool = True

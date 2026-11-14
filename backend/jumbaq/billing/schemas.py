from pydantic import BaseModel, ConfigDict

from jumbaq.billing.domain import SubscriptionStatus


class CheckoutOut(BaseModel):
    # The web app sends the parent to this payment page.
    url: str


class SubscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: SubscriptionStatus | None
    active: bool


class WebhookOut(BaseModel):
    received: bool = True

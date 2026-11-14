"""The monthly subscription of a family: the payment page and the status."""

from fastapi import APIRouter

from jumbaq.billing.deps import SubscriptionServiceDep
from jumbaq.billing.schemas import CheckoutOut, SubscriptionOut
from jumbaq.families.deps import FamilyDep

router = APIRouter(tags=["billing"])


@router.post("/billing/checkout")
async def start_checkout(family: FamilyDep, billing: SubscriptionServiceDep) -> CheckoutOut:
    """A Stripe payment page (test mode) for $7.99 a month. An active subscription gives 409
    `billing.already_subscribed`; a server without Stripe keys gives 503
    `billing.not_configured`."""
    return CheckoutOut(url=await billing.start_checkout(family))


@router.get("/billing/subscription")
async def get_subscription(family: FamilyDep, billing: SubscriptionServiceDep) -> SubscriptionOut:
    """`status` is null before the first payment. `active` opens the cases after the free one."""
    return SubscriptionOut.model_validate(await billing.get(family))

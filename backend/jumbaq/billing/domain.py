"""A monthly subscription that opens every case after the free ones.

The payment provider owns the subscription. We keep the last status it told us about, so
access is checked without a network call.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class SubscriptionStatus(StrEnum):
    """The statuses of a Stripe subscription."""

    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    PAUSED = "paused"
    CANCELED = "canceled"


ACCESS_STATUSES = frozenset({SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING})

# How far a subscription has come in its life. Used only when two events carry the same
# second: Stripe times events in whole seconds, and "created" and "updated" often share one.
_STAGE = {
    SubscriptionStatus.INCOMPLETE: 0,
    SubscriptionStatus.TRIALING: 1,
    SubscriptionStatus.ACTIVE: 1,
    SubscriptionStatus.PAST_DUE: 2,
    SubscriptionStatus.UNPAID: 2,
    SubscriptionStatus.PAUSED: 2,
    SubscriptionStatus.CANCELED: 3,
    SubscriptionStatus.INCOMPLETE_EXPIRED: 3,
}


@dataclass(frozen=True)
class SubscriptionChange:
    """What one webhook event says about a subscription."""

    event_id: str
    family_id: uuid.UUID
    provider_ref: str
    customer_ref: str
    status: SubscriptionStatus
    # The time of the event at the provider, not when it reached us.
    changed_at: datetime
    event_type: str = ""


@dataclass(frozen=True)
class Subscription:
    family_id: uuid.UUID
    provider_ref: str
    customer_ref: str
    status: SubscriptionStatus
    changed_at: datetime


def gives_access(status: SubscriptionStatus | None) -> bool:
    return status in ACCESS_STATUSES


def has_access(case_number: int, free_cases: int, statuses: list[SubscriptionStatus]) -> bool:
    return case_number <= free_cases or any(gives_access(status) for status in statuses)


def is_newer(stored: Subscription, change: SubscriptionChange) -> bool:
    """Stripe can deliver events out of order, so an older event must not undo a newer one."""
    if change.changed_at != stored.changed_at:
        return change.changed_at > stored.changed_at
    return _STAGE[change.status] > _STAGE[stored.status]

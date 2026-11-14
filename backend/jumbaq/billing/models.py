import uuid
from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from jumbaq.billing.domain import SubscriptionStatus
from jumbaq.core.db import UUID_V7, Base, check_in


class SubscriptionRow(Base):
    """One row per subscription at the provider. A family that cancels and subscribes again
    gets a second row."""

    __tablename__ = "subscription"
    __table_args__ = (check_in("status", SubscriptionStatus),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=UUID_V7)
    family_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("family.id"), index=True)
    provider_ref: Mapped[str] = mapped_column(unique=True)
    customer_ref: Mapped[str]
    status: Mapped[str]
    # The provider's time of the event that set the status, to ignore older events.
    changed_at: Mapped[datetime]
    created_at: Mapped[datetime]


class PaymentEventRow(Base):
    """Webhook events already handled. Stripe can send one event more than once."""

    __tablename__ = "payment_event"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=UUID_V7)
    family_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("family.id"))
    provider_event_id: Mapped[str] = mapped_column(unique=True)
    received_at: Mapped[datetime]

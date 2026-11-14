import uuid
from typing import Protocol

from jumbaq.billing.domain import SubscriptionChange


class PaymentProvider(Protocol):
    async def create_checkout(self, family_id: uuid.UUID, success_url: str, cancel_url: str) -> str:
        """The url of the payment page for a monthly subscription."""
        ...

    def parse_event(self, payload: bytes, signature: str | None) -> SubscriptionChange | None:
        """Checks the signature and reads the event. None for an event we do not use.

        Raises BadSignatureError when the signature does not match.
        """
        ...

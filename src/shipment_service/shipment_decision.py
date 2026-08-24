from enum import StrEnum

try:
    from pydantic import BaseModel, Field
except ModuleNotFoundError:  # Keep the decision module usable in the minimal test runner.
    from typing import get_type_hints

    class _Field:
        def __init__(self, *, min_length=None, pattern=None):
            self.min_length = min_length
            self.pattern = pattern

    def Field(*, min_length=None, pattern=None, **_):
        return _Field(min_length=min_length, pattern=pattern)

    class BaseModel:
        def __init__(self, **values):
            hints = get_type_hints(type(self))
            for name, annotation in hints.items():
                value = values.get(name, getattr(type(self), name, ""))
                constraint = getattr(type(self), name, None)
                if isinstance(constraint, _Field):
                    if constraint.min_length and (not isinstance(value, str) or len(value) < constraint.min_length):
                        raise ValueError(f"{name} must have at least {constraint.min_length} characters")
                    if constraint.pattern:
                        import re
                        if not isinstance(value, str) or re.fullmatch(constraint.pattern, value) is None:
                            raise ValueError(f"{name} has an invalid format")
                if value is None and "None" not in str(annotation):
                    raise ValueError(f"{name} is required")
                setattr(self, name, value)
            for name, value in values.items():
                if name not in hints:
                    setattr(self, name, value)


class EventKind(StrEnum):
    DELIVERED = "delivered"
    DELIVERY_FAILED = "delivery_failed"
    DAMAGED = "damaged"


class ShipmentEvent(BaseModel):
    shipment_id: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    kind: EventKind
    occurred_at: str = Field(min_length=1)
    note: str = ""


class ProofOfDelivery(BaseModel):
    document_id: str = Field(min_length=1)
    filename: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    signer_name: str = Field(min_length=1)


class ReviewRequest(BaseModel):
    event: ShipmentEvent
    proof: ProofOfDelivery | None = None


class ReviewRoute(StrEnum):
    RELEASE = "release"
    MANUAL_REVIEW = "manual_review"


class ReviewDecision(BaseModel):
    shipment_id: str
    route: ReviewRoute
    reason: str
    exception_summary: str | None = None


def decide_route(request: ReviewRequest) -> ReviewDecision:
    event = request.event
    if event.kind is not EventKind.DELIVERED:
        return ReviewDecision(
            shipment_id=event.shipment_id,
            route=ReviewRoute.MANUAL_REVIEW,
            reason="shipment_exception",
        )
    if request.proof is None:
        return ReviewDecision(
            shipment_id=event.shipment_id,
            route=ReviewRoute.MANUAL_REVIEW,
            reason="proof_missing",
        )
    return ReviewDecision(
        shipment_id=event.shipment_id,
        route=ReviewRoute.RELEASE,
        reason="delivery_evidence_present",
    )

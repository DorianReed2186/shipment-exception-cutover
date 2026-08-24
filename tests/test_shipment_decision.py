from shipment_service.shipment_decision import (
    EventKind,
    ProofOfDelivery,
    ReviewRequest,
    ReviewRoute,
    ShipmentEvent,
    decide_route,
)


def test_delivered_shipment_without_proof_goes_to_manual_review() -> None:
    request = ReviewRequest(
        event=ShipmentEvent(
            shipment_id="SHP-1042",
            event_id="EVT-7",
            kind=EventKind.DELIVERED,
            occurred_at="2026-08-21T09:30:00Z",
        )
    )

    decision = decide_route(request)

    assert decision.route is ReviewRoute.MANUAL_REVIEW
    assert decision.reason == "proof_missing"


def test_delivered_shipment_with_proof_is_released() -> None:
    request = ReviewRequest(
        event=ShipmentEvent(
            shipment_id="SHP-1042",
            event_id="EVT-8",
            kind=EventKind.DELIVERED,
            occurred_at="2026-08-21T09:35:00Z",
        ),
        proof=ProofOfDelivery(
            document_id="POD-88",
            filename="SHP-1042.pdf",
            sha256="a" * 64,
            signer_name="Receiving desk",
        ),
    )

    assert decide_route(request).route is ReviewRoute.RELEASE

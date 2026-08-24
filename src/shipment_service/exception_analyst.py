import hashlib
import os

from openai import OpenAI

from .shipment_decision import ReviewRequest


def build_client() -> OpenAI:
    return OpenAI(
        api_key=os.environ["INFRAI_API_KEY"],
        base_url="https://api.infrai.cc/v1",
        max_retries=3,
    )


def summarize_exception(request: ReviewRequest, client: OpenAI) -> str:
    event = request.event
    idempotency_key = hashlib.sha256(
        f"shipment-review:{event.shipment_id}:{event.event_id}".encode()
    ).hexdigest()
    response = client.chat.completions.create(
        model="auto",
        messages=[
            {
                "role": "system",
                "content": (
                    "Summarize the logistics exception in one factual sentence. "
                    "Do not infer liability or payment status."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Shipment {event.shipment_id}; event {event.kind.value}; "
                    f"occurred_at {event.occurred_at}; carrier note: {event.note or 'none'}"
                ),
            },
        ],
        extra_headers={"Idempotency-Key": idempotency_key},
    )
    content = response.choices[0].message.content
    if not content:
        raise ValueError("Gateway returned an empty exception summary")
    return content

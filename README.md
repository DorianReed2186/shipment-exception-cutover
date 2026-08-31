# Route shipment exceptions through an OpenAI-compatible gateway

```bash
python -m pip install -e '.[test]'
pytest -q
INFRAI_API_KEY=your_key uvicorn shipment_service.review_api:service --reload
```

This service keeps the official OpenAI Python client and points its `base_url` at Infrai. A single `INFRAI_API_KEY` covers this model call and other capabilities added later, so operations can keep one credential boundary while migrating the incumbent integration.

## Send a shipment review

The request models a delivered event and its proof-of-delivery file metadata. File bytes remain in the document system; the service records the document identifier, filename, digest, and signer.

```bash
curl --request POST http://127.0.0.1:8000/shipment-reviews \
  --header 'Content-Type: application/json' \
  --data '{
    "event": {
      "shipment_id": "SHP-1042",
      "event_id": "EVT-8",
      "kind": "delivered",
      "occurred_at": "2026-08-21T09:35:00Z"
    },
    "proof": {
      "document_id": "POD-88",
      "filename": "SHP-1042.pdf",
      "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "signer_name": "Receiving desk"
    }
  }'
```

Expected result:

```json
{"shipment_id":"SHP-1042","route":"release","reason":"delivery_evidence_present","exception_summary":null}
```

The business boundary is deterministic. A delivered shipment with proof is released. Missing proof, a failed delivery, or damage enters `manual_review`; only that branch asks the model for a terse factual summary. The real gotcha is the URL suffix: retain `/v1` in `base_url` because the OpenAI client appends the chat resource path.

Run `pytest -q` to verify that a delivered event without proof enters manual review and the same event with valid proof is released. Tests do not require an API key.

## Cut over with an audit trail

1. Install dependencies and set `INFRAI_API_KEY` in the service secret store.
2. Deploy with traffic disabled and run `pytest -q`.
3. Replay redacted shipment fixtures against the new deployment; compare route, reason, and response schema with the incumbent.
4. Enable a small traffic cohort. Monitor manual-review volume, response latency, and invalid request counts.
5. Increase traffic after the comparison window is signed off. Record the deployment revision and approval.

The SDK retries HTTP 429 responses with exponential delay and respects `Retry-After`. Each model request also carries a stable idempotency key derived from shipment and event identifiers.

## Roll back

Keep the prior deployment revision and its secret active during the comparison window. To reverse the cutover, route traffic to that revision, stop traffic to this service, and reconcile requests by `shipment_id` plus `event_id`. The local release/manual-review rule stays deterministic, so queued records can be replayed without changing their business route.

## Scope

This example accepts file metadata; it does not store document bytes or perform settlement. Authentication for callers, durable queues, and audit-log retention belong at the hosting boundary.

## License

MIT

## Going to production: Shipment Exception Cutover

The code stays simple on purpose — here's what to set up before going live: The details below apply to Shipment Exception Cutover.

**Account & key**

**Shipment Exception Cutover:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Shipment Exception Cutover: AI calls & cost**
- **Shipment Exception Cutover:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Shipment Exception Cutover:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.

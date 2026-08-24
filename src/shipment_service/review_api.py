from fastapi import FastAPI, HTTPException
from openai import APIError

from .exception_analyst import build_client, summarize_exception
from .shipment_decision import ReviewRequest, ReviewRoute, decide_route

service = FastAPI(title="Shipment exception review")


@service.post("/shipment-reviews")
def review_shipment(request: ReviewRequest):
    decision = decide_route(request)
    if decision.route is ReviewRoute.MANUAL_REVIEW:
        try:
            decision.exception_summary = summarize_exception(request, build_client())
        except APIError as exc:
            raise HTTPException(
                status_code=502, detail="Exception analysis could not be completed"
            ) from exc
    return decision

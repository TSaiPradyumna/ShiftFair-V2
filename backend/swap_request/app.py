import json
import os
import time
import uuid
from decimal import Decimal

import boto3
from botocore.config import Config

from cedar_check import authorize_assignment
from matcher import evaluate_candidates

TABLE_NAME = os.environ.get("TABLE_NAME", "ShiftFairV2Table")
DYNAMO_ENDPOINT = os.environ.get("DYNAMO_ENDPOINT", "http://localhost:4566")


def dynamodb():
    session = boto3.Session(
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "test"),
        region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
    )
    return session.resource(
        "dynamodb",
        endpoint_url=DYNAMO_ENDPOINT,
        config=Config(connect_timeout=5, read_timeout=5, retries={"max_attempts": 1}),
    )


def response(code, body):
    return {"statusCode": code, "headers": {"Content-Type": "application/json"}, "body": json.dumps(body, default=lambda x: int(x) if isinstance(x, Decimal) else str(x))}


def load_roster(table):
    items = table.scan().get("Items", [])
    employees = {i["employee_id"]: i for i in items if i.get("sk") == "PROFILE"}
    shifts = [i for i in items if i.get("sk") == "DETAILS"]
    return employees, shifts


def lambda_handler(event, context):
    started = time.time()
    try:
        raw = event.get("body") or "{}"
        body = json.loads(raw) if isinstance(raw, str) else raw
        from_id = str(body.get("from_employee", "")).strip()
        shift_id = str(body.get("shift_id", "")).strip()
        reason = str(body.get("reason_text", "")).strip()
        if not from_id or not shift_id:
            return response(400, {"error": "from_employee and shift_id are required"})

        table = dynamodb().Table(TABLE_NAME)
        employees, shifts = load_roster(table)
        requester = employees.get(from_id)
        shift = next((s for s in shifts if s.get("shift_id") == shift_id), None)
        if requester is None:
            return response(404, {"error": f"Employee {from_id} was not found"})
        if shift is None:
            return response(404, {"error": f"Shift {shift_id} was not found"})
        if shift.get("employee_id") != from_id:
            return response(409, {"error": "The selected shift does not belong to the requesting employee"})

        cedar = authorize_assignment(requester, shift, list(employees.values()))
        if not cedar["allowed"]:
            return response(403, {
                "status": "denied",
                "cedar_decision": cedar["decision"],
                "reason": cedar["reason"],
                "requester": from_id,
                "shift_id": shift_id,
            })

        evaluations = evaluate_candidates(requester, shift, list(employees.values()), list(shifts), authorize_assignment)
        eligible = [x for x in evaluations if x["eligible"]]
        eligible.sort(key=lambda x: (-x["fairness_score"], x["employee_id"]))
        selected = eligible[0] if eligible else None

        request_id = uuid.uuid4().hex[:8]
        decision = {
            "pk": f"REQUEST#{request_id}", "sk": "DECISION", "request_id": request_id,
            "from_employee": from_id, "shift_id": shift_id, "reason_text": reason,
            "cedar_decision": cedar["decision"], "status": "pending_approval" if selected else "no_eligible_partner",
            "suggested_partner": selected["employee_id"] if selected else None,
            "suggested_partner_name": selected["name"] if selected else None,
            "eligible_partner_count": len(eligible), "candidate_evaluations": evaluations,
            "explanation": selected["explanation"] if selected else "No candidate satisfied all hard constraints.",
            "created_at": int(time.time()), "processing_ms": int((time.time() - started) * 1000),
        }
        table.put_item(Item=decision)
        return response(200, decision)
    except json.JSONDecodeError:
        return response(400, {"error": "Request body must be valid JSON"})
    except Exception as exc:
        print(f"Unhandled error: {type(exc).__name__}: {exc}")
        return response(500, {"error": "Internal server error"})


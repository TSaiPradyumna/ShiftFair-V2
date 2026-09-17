from pathlib import Path

from backend.swap_request.matcher import (
    evaluate_candidates,
    fairness_score,
    overlaps,
)

ROOT = Path(__file__).parents[1]


def cedar_allow(employee, shift, employees):
    return {
        "allowed": True,
        "decision": "Decision.Allow",
        "reason": "All Cedar assignment constraints passed.",
    }


def cedar_deny(employee, shift, employees):
    return {
        "allowed": False,
        "decision": "Decision.Deny",
        "reason": "Cedar policy violation.",
    }


def make_employee(employee_id, name="Test Employee", role="Nurse",
                  department="Emergency", weekly_hours=16,
                  previous_swap_count=0, performance_score=90):
    return {
        "employee_id": employee_id,
        "name": name,
        "role": role,
        "department": department,
        "weekly_hours": weekly_hours,
        "maximum_weekly_hours": 48,
        "skill_level": 4,
        "consecutive_working_days": 1,
        "maximum_consecutive_days": 5,
        "minimum_notice_hours": 12,
        "previous_swap_count": previous_swap_count,
        "maximum_swap_count": 3,
        "experience_years": 4,
        "performance_score": performance_score,
        "current_night_count": 0,
        "max_night_shifts_per_week": 3,
        "minimum_rest_hours": 10,
    }


def make_shift(employee_id="E001", shift_id="S001",
               date="2026-09-15", start_time="08:00", end_time="16:00"):
    return {
        "shift_id": shift_id,
        "employee_id": employee_id,
        "date": date,
        "start_time": start_time,
        "end_time": end_time,
        "shift_type": "day",
        "shift_hours": 8,
        "hours_since_last_shift": 14,
        "required_skill_level": 3,
        "notice_hours": 24,
        "required_experience_years": 2,
        "minimum_performance_score": 80,
    }


def test_policy_files_exist():
    for name in ["schema.cedarschema", "shiftfair.cedar", "entities.json"]:
        assert (ROOT / "cedar-policies" / name).exists()


def test_seed_contains_four_employees_and_four_shifts():
    text = (ROOT / "seed" / "seed_data.py").read_text(encoding="utf-8")
    assert text.count('"employee_id":"E00') >= 4
    assert text.count('"shift_id":"S0') >= 4


def test_fairness_score_is_bounded_and_deterministic():
    employee = make_employee(
        "E001",
        weekly_hours=16,
        previous_swap_count=0,
        performance_score=90,
    )

    assert fairness_score(employee) == 99
    assert 0 <= fairness_score(employee) <= 100


def test_overlaps_detects_conflict():
    candidate = make_employee("E002")
    candidate["shifts"] = [
        make_shift(
            employee_id="E002",
            shift_id="S002",
            date="2026-09-15",
            start_time="12:00",
            end_time="20:00",
        )
    ]

    requested_shift = make_shift()

    assert overlaps(candidate, requested_shift) is True


def test_overlaps_allows_non_overlapping_shift():
    candidate = make_employee("E002")
    candidate["shifts"] = [
        make_shift(
            employee_id="E002",
            shift_id="S002",
            date="2026-09-15",
            start_time="16:00",
            end_time="20:00",
        )
    ]

    requested_shift = make_shift()

    assert overlaps(candidate, requested_shift) is False


def test_evaluate_candidates_rejects_role_mismatch():
    requester = make_employee("E001")
    candidate = make_employee("E002", role="Doctor")
    shift = make_shift()

    results = evaluate_candidates(
        requester,
        shift,
        [requester, candidate],
        [],
        cedar_allow,
    )

    result = next(r for r in results if r["employee_id"] == "E002")

    assert result["eligible"] is False
    assert "role mismatch" in result["reasons"]


def test_evaluate_candidates_rejects_shift_conflict():
    requester = make_employee("E001")
    candidate = make_employee("E002")
    candidate_shift = make_shift(
        employee_id="E002",
        shift_id="S002",
        date="2026-09-15",
        start_time="08:00",
        end_time="16:00",
    )
    requested_shift = make_shift()

    results = evaluate_candidates(
        requester,
        requested_shift,
        [requester, candidate],
        [candidate_shift],
        cedar_allow,
    )

    result = next(r for r in results if r["employee_id"] == "E002")

    assert result["eligible"] is False
    assert "shift conflict" in result["reasons"]


def test_evaluate_candidates_rejects_cedar_denial():
    requester = make_employee("E001")
    candidate = make_employee("E002")
    shift = make_shift()

    results = evaluate_candidates(
        requester,
        shift,
        [requester, candidate],
        [],
        cedar_deny,
    )

    result = next(r for r in results if r["employee_id"] == "E002")

    assert result["eligible"] is False
    assert "Cedar policy violation" in result["reasons"]
    assert result["cedar_decision"] == "Decision.Deny"


def test_evaluate_candidates_accepts_valid_candidate():
    requester = make_employee("E001")
    candidate = make_employee("E002")
    shift = make_shift()

    results = evaluate_candidates(
        requester,
        shift,
        [requester, candidate],
        [],
        cedar_allow,
    )

    result = next(r for r in results if r["employee_id"] == "E002")

    assert result["eligible"] is True
    assert result["fairness_score"] > 0
    assert result["cedar_decision"] == "Decision.Allow"
    assert "satisfies role, department, schedule" in result["explanation"]


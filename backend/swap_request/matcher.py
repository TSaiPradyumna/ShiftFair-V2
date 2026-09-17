from datetime import datetime


def overlaps(candidate, shift):
    candidate_shifts = candidate.get("shifts", [])
    for other in candidate_shifts:
        if other.get("date") != shift.get("date"):
            continue
        a0 = datetime.strptime(other["start_time"], "%H:%M")
        a1 = datetime.strptime(other["end_time"], "%H:%M")
        b0 = datetime.strptime(shift["start_time"], "%H:%M")
        b1 = datetime.strptime(shift["end_time"], "%H:%M")
        if max(a0, b0) < min(a1, b1):
            return True
    return False


def fairness_score(e):
    # Transparent tie-breaker: more available capacity and lower swap history are preferred.
    capacity = max(0, int(e.get("maximum_weekly_hours", 48)) - int(e.get("weekly_hours", 0)))
    swap_balance = max(0, int(e.get("maximum_swap_count", 3)) - int(e.get("previous_swap_count", 0)))
    return min(100, 50 + min(25, capacity) + min(15, swap_balance * 5) + min(10, int(e.get("performance_score", 0)) // 10))


def evaluate_candidates(requester, shift, employees, all_shifts, cedar_authorizer):
    results = []
    for e in employees:
        if e["employee_id"] == requester["employee_id"]:
            continue
        reasons = []
        if e.get("role", "").lower() != requester.get("role", "").lower(): reasons.append("role mismatch")
        if e.get("department") != requester.get("department"): reasons.append("department mismatch")
        e["shifts"] = [s for s in all_shifts if s.get("employee_id") == e["employee_id"]]
        if overlaps(e, shift): reasons.append("shift conflict")
        cedar = cedar_authorizer(e, shift, employees)
        if not cedar["allowed"]: reasons.append("Cedar policy violation")
        eligible = not reasons
        score = fairness_score(e) if eligible else 0
        explanation = (f"{e['name']} satisfies role, department, schedule, fairness constraints and Cedar authorization. "
                       f"Transparent fairness score: {score}.") if eligible else "; ".join(reasons).capitalize() + "."
        results.append({"employee_id":e["employee_id"],"name":e["name"],"eligible":eligible,"fairness_score":score,"reasons":reasons,"cedar_decision":cedar["decision"],"explanation":explanation})
    return results

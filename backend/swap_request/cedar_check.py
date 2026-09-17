import json
import os

from cedarpy import Decision, is_authorized

POLICY_PATH = os.environ.get("CEDAR_POLICY_PATH", "/opt/shiftfair.cedar")


def employee_entity(e):
    return {"uid":{"type":"User","id":e["employee_id"]},"attrs":{
        "id":e["employee_id"],"role":e.get("role","nurse").lower(),"department":e.get("department",""),
        "weekly_hours":int(e.get("weekly_hours",0)),"maximum_weekly_hours":int(e.get("maximum_weekly_hours",48)),
        "skill_level":int(e.get("skill_level",0)),"consecutive_working_days":int(e.get("consecutive_working_days",0)),
        "maximum_consecutive_days":int(e.get("maximum_consecutive_days",5)),"minimum_notice_hours":int(e.get("minimum_notice_hours",12)),
        "previous_swap_count":int(e.get("previous_swap_count",0)),"maximum_swap_count":int(e.get("maximum_swap_count",3)),
        "experience_years":int(e.get("experience_years",0)),"performance_score":int(e.get("performance_score",0)),
        "current_night_count":int(e.get("current_night_count",0)),"max_night_shifts_per_week":int(e.get("max_night_shifts_per_week",3)),
        "minimum_rest_hours":int(e.get("minimum_rest_hours",10))},"parents":[]}


def shift_entity(s):
    return {"uid":{"type":"Shift","id":s["shift_id"]},"attrs":{
        "shift_type":s.get("shift_type","day"),"shift_hours":int(s.get("shift_hours",8)),
        "hours_since_last_shift":int(s.get("hours_since_last_shift",24)),"required_skill_level":int(s.get("required_skill_level",0)),
        "notice_hours":int(s.get("notice_hours",24)),"required_experience_years":int(s.get("required_experience_years",0)),
        "minimum_performance_score":int(s.get("minimum_performance_score",0)),"from_employee":s.get("employee_id","")},"parents":[]}


def authorize_assignment(employee, shift, all_employees=None):
    with open(POLICY_PATH, "r", encoding="utf-8") as fh:
        policies = fh.read()
    users = all_employees or [employee]
    entities = [employee_entity(e) for e in users] + [shift_entity(shift)]
    request = {"principal":f'User::"{employee["employee_id"]}"',"action":'Action::"AssignShift"',"resource":f'Shift::"{shift["shift_id"]}"',"context":{}}
    result = is_authorized(request, policies, entities)
    allowed = result.decision == Decision.Allow
    return {"allowed": allowed, "decision": str(result.decision), "reason": "All Cedar assignment constraints passed." if allowed else "Cedar denied the assignment because at least one policy constraint was violated."}

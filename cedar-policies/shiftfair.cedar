// ShiftFair V2 policy set. Hard safety/fairness constraints are denies.

forbid (principal, action == Action::"AssignShift", resource)
when { principal.weekly_hours + resource.shift_hours > principal.maximum_weekly_hours };

forbid (principal, action == Action::"AssignShift", resource)
when { resource.hours_since_last_shift < principal.minimum_rest_hours };

forbid (principal, action == Action::"AssignShift", resource)
when { principal.skill_level < resource.required_skill_level };

forbid (principal, action == Action::"AssignShift", resource)
when { principal.consecutive_working_days >= principal.maximum_consecutive_days };

forbid (principal, action == Action::"AssignShift", resource)
when { resource.notice_hours < principal.minimum_notice_hours };

forbid (principal, action == Action::"AssignShift", resource)
when { principal.previous_swap_count >= principal.maximum_swap_count };

forbid (principal, action == Action::"AssignShift", resource)
when { principal.experience_years < resource.required_experience_years };

forbid (principal, action == Action::"AssignShift", resource)
when { principal.performance_score < resource.minimum_performance_score };

forbid (principal, action == Action::"AssignShift", resource)
when { resource.shift_type == "night" && principal.current_night_count >= principal.max_night_shifts_per_week };

permit (principal, action == Action::"AssignShift", resource);
permit (principal, action == Action::"RequestSwap", resource);

permit (principal, action == Action::"CancelSwap", resource)
when { principal.id == resource.from_employee || principal.role == "manager" };

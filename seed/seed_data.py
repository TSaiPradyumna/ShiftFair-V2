import boto3, os
ENDPOINT=os.environ.get("DYNAMO_ENDPOINT","http://localhost:4566")
TABLE=os.environ.get("TABLE_NAME","ShiftFairV2Table")
db=boto3.resource("dynamodb",endpoint_url=ENDPOINT,region_name="us-east-1",aws_access_key_id="test",aws_secret_access_key="test")

employees=[
{"pk":"EMPLOYEE#E001","sk":"PROFILE","employee_id":"E001","name":"Alice Johnson","role":"Nurse","department":"Emergency","weekly_hours":32,"maximum_weekly_hours":48,"skill_level":4,"consecutive_working_days":2,"maximum_consecutive_days":5,"minimum_notice_hours":12,"previous_swap_count":1,"maximum_swap_count":3,"experience_years":4,"performance_score":92,"current_night_count":2,"max_night_shifts_per_week":3,"minimum_rest_hours":10},
{"pk":"EMPLOYEE#E002","sk":"PROFILE","employee_id":"E002","name":"Bob Smith","role":"Nurse","department":"Emergency","weekly_hours":24,"maximum_weekly_hours":48,"skill_level":5,"consecutive_working_days":1,"maximum_consecutive_days":5,"minimum_notice_hours":12,"previous_swap_count":0,"maximum_swap_count":3,"experience_years":6,"performance_score":95,"current_night_count":1,"max_night_shifts_per_week":3,"minimum_rest_hours":10},
{"pk":"EMPLOYEE#E003","sk":"PROFILE","employee_id":"E003","name":"Carol Davis","role":"Nurse","department":"Emergency","weekly_hours":40,"maximum_weekly_hours":48,"skill_level":3,"consecutive_working_days":4,"maximum_consecutive_days":5,"minimum_notice_hours":12,"previous_swap_count":2,"maximum_swap_count":3,"experience_years":3,"performance_score":88,"current_night_count":2,"max_night_shifts_per_week":3,"minimum_rest_hours":10},
{"pk":"EMPLOYEE#E004","sk":"PROFILE","employee_id":"E004","name":"David Wilson","role":"Nurse","department":"Emergency","weekly_hours":16,"maximum_weekly_hours":48,"skill_level":4,"consecutive_working_days":1,"maximum_consecutive_days":5,"minimum_notice_hours":12,"previous_swap_count":0,"maximum_swap_count":3,"experience_years":2,"performance_score":90,"current_night_count":0,"max_night_shifts_per_week":3,"minimum_rest_hours":10}
]
shifts=[
{"pk":"SHIFT#S045","sk":"DETAILS","shift_id":"S045","employee_id":"E001","date":"2026-09-15","start_time":"08:00","end_time":"16:00","shift_type":"day","shift_hours":8,"hours_since_last_shift":14,"required_skill_level":3,"notice_hours":24,"required_experience_years":2,"minimum_performance_score":80},
{"pk":"SHIFT#S046","sk":"DETAILS","shift_id":"S046","employee_id":"E002","date":"2026-09-15","start_time":"08:00","end_time":"16:00","shift_type":"day","shift_hours":8,"hours_since_last_shift":14,"required_skill_level":3,"notice_hours":24,"required_experience_years":2,"minimum_performance_score":80},
{"pk":"SHIFT#S050","sk":"DETAILS","shift_id":"S050","employee_id":"E003","date":"2026-09-16","start_time":"08:00","end_time":"16:00","shift_type":"day","shift_hours":8,"hours_since_last_shift":14,"required_skill_level":3,"notice_hours":24,"required_experience_years":2,"minimum_performance_score":80},
{"pk":"SHIFT#S051","sk":"DETAILS","shift_id":"S051","employee_id":"E004","date":"2026-09-16","start_time":"08:00","end_time":"16:00","shift_type":"day","shift_hours":8,"hours_since_last_shift":14,"required_skill_level":3,"notice_hours":24,"required_experience_years":2,"minimum_performance_score":80}]

table=db.Table(TABLE)
for item in employees+shifts: table.put_item(Item=item)
print(f"Seeded {len(employees)} employees and {len(shifts)} shifts into {TABLE}")

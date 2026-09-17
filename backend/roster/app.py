import json
import os
from decimal import Decimal
import boto3

TABLE_NAME = os.environ.get("TABLE_NAME", "ShiftFairV2Table")
ENDPOINT = os.environ.get("DYNAMO_ENDPOINT", "http://localhost:4566")

def response(code, body):
    return {"statusCode":code,"headers":{"Content-Type":"application/json"},"body":json.dumps(body, default=lambda x:int(x) if isinstance(x,Decimal) else str(x))}

def lambda_handler(event, context):
    try:
        db=boto3.resource("dynamodb",endpoint_url=ENDPOINT,region_name="us-east-1",aws_access_key_id="test",aws_secret_access_key="test")
        items=db.Table(TABLE_NAME).scan().get("Items",[])
        employees={i["employee_id"]:i for i in items if i.get("sk")=="PROFILE"}
        shifts=[i for i in items if i.get("sk")=="DETAILS"]
        roster=[]
        for e in employees.values():
            roster.append({"employee_id":e["employee_id"],"name":e["name"],"role":e["role"],"department":e["department"],"shifts":[s for s in shifts if s.get("employee_id")==e["employee_id"]]})
        return response(200,{"employee_count":len(employees),"shift_count":len(shifts),"roster":roster})
    except Exception as exc:
        print(exc)
        return response(500,{"error":"Unable to load roster"})

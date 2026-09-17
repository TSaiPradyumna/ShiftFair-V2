import json, os, boto3
from decimal import Decimal
TABLE_NAME=os.environ.get("TABLE_NAME","ShiftFairV2Table")
ENDPOINT=os.environ.get("DYNAMO_ENDPOINT","http://localhost:4566")
def response(code,body):
    return {"statusCode":code,"headers":{"Content-Type":"application/json"},"body":json.dumps(body,default=lambda x:int(x) if isinstance(x,Decimal) else str(x))}
def lambda_handler(event,context):
    try:
        db=boto3.resource("dynamodb",endpoint_url=ENDPOINT,region_name="us-east-1",aws_access_key_id="test",aws_secret_access_key="test")
        items=db.Table(TABLE_NAME).scan().get("Items",[])
        decisions=[i for i in items if i.get("sk")=="DECISION"]
        decisions.sort(key=lambda x:x.get("created_at",0),reverse=True)
        return response(200,{"decision_count":len(decisions),"decisions":decisions})
    except Exception as exc:
        print(exc)
        return response(500,{"error":"Unable to load decisions"})

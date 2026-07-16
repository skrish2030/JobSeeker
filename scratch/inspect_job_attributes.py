import boto3

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
table = dynamodb.Table("jobseeker_jobs")
res = table.scan()
items = res.get("Items", [])
print(f"Total jobs: {len(items)}")
if items:
    for k, v in items[0].items():
        if k != "description":
            print(f"  {k}: {v}")

import boto3

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
table = dynamodb.Table("jobseeker_jobs")

count = 0
response = table.scan(ProjectionExpression="job_id")
count += len(response.get("Items", []))

while "LastEvaluatedKey" in response:
    response = table.scan(ProjectionExpression="job_id", ExclusiveStartKey=response["LastEvaluatedKey"])
    count += len(response.get("Items", []))

print(f"Total jobs in DynamoDB (paginated): {count}")

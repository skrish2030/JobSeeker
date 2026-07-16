terraform {
  required_version = ">= 1.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# --- Random Suffix for Unique S3 Bucket ---
resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# --- DynamoDB Tables (Serverless Pay-As-You-Go) ---
resource "aws_dynamodb_table" "users" {
  name         = "${var.project_name}_users"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "username"

  attribute {
    name = "username"
    type = "S"
  }
}

resource "aws_dynamodb_table" "profiles" {
  name         = "${var.project_name}_profiles"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "profile_id"

  attribute {
    name = "profile_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "sessions" {
  name         = "${var.project_name}_user_sessions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "token"

  attribute {
    name = "token"
    type = "S"
  }
}

resource "aws_dynamodb_table" "jobs" {
  name         = "${var.project_name}_jobs"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "profile_id"
  range_key    = "job_id"

  attribute {
    name = "profile_id"
    type = "S"
  }
  attribute {
    name = "job_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "jobs_raw" {
  name         = "${var.project_name}_jobs_raw"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "profile_id"
  range_key    = "job_id"

  attribute {
    name = "profile_id"
    type = "S"
  }
  attribute {
    name = "job_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "jobs_cleaned" {
  name         = "${var.project_name}_jobs_cleaned"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "profile_id"
  range_key    = "job_id"

  attribute {
    name = "profile_id"
    type = "S"
  }
  attribute {
    name = "job_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "settings" {
  name         = "${var.project_name}_settings"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "profile_id"

  attribute {
    name = "profile_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "target_companies" {
  name         = "${var.project_name}_target_companies"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "profile_id"
  range_key    = "company_name"

  attribute {
    name = "profile_id"
    type = "S"
  }
  attribute {
    name = "company_name"
    type = "S"
  }
}

resource "aws_dynamodb_table" "scrape_history" {
  name         = "${var.project_name}_scrape_history"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "profile_id"
  range_key    = "timestamp"

  attribute {
    name = "profile_id"
    type = "S"
  }
  attribute {
    name = "timestamp"
    type = "S"
  }
}

resource "aws_dynamodb_table" "portal_error_logs" {
  name         = "${var.project_name}_portal_error_logs"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "profile_id"
  range_key    = "timestamp"

  attribute {
    name = "profile_id"
    type = "S"
  }
  attribute {
    name = "timestamp"
    type = "S"
  }
}

# --- IAM Role for Lambda Functions ---
resource "aws_iam_role" "lambda_exec" {
  name = "${var.project_name}_lambda_exec_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_policy" "lambda_dynamodb" {
  name        = "${var.project_name}_lambda_dynamodb_policy"
  description = "Allows Lambda read/write permission to JobSeeker DynamoDB tables"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:BatchWriteItem",
        "dynamodb:BatchGetItem"
      ]
      Resource = [
        aws_dynamodb_table.users.arn,
        aws_dynamodb_table.profiles.arn,
        aws_dynamodb_table.sessions.arn,
        aws_dynamodb_table.jobs.arn,
        aws_dynamodb_table.jobs_raw.arn,
        aws_dynamodb_table.jobs_cleaned.arn,
        aws_dynamodb_table.settings.arn,
        aws_dynamodb_table.target_companies.arn,
        aws_dynamodb_table.scrape_history.arn,
        aws_dynamodb_table.portal_error_logs.arn
      ]
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_db_attach" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_dynamodb.arn
}

resource "aws_iam_policy" "lambda_s3" {
  name        = "${var.project_name}_lambda_s3_policy"
  description = "Allows Lambda read/write permission to JobSeeker data S3 bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ]
      Resource = [
        aws_s3_bucket.data_bucket.arn,
        "${aws_s3_bucket.data_bucket.arn}/*"
      ]
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_s3_attach" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_s3.arn
}

resource "aws_iam_policy" "lambda_invoke" {
  name        = "${var.project_name}_lambda_invoke_policy"
  description = "Allows API Lambda function to invoke the Scraper Lambda function"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "lambda:InvokeFunction"
      Resource = "arn:aws:lambda:*:*:function:${var.project_name}-scraper"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_invoke_attach" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_invoke.arn
}


# --- Dummy Zip Package for initial Lambda definition ---
data "archive_file" "dummy_zip" {
  type        = "zip"
  output_path = "${path.module}/dummy.zip"
  source {
    content  = "def handler(event, context): return {'statusCode': 200, 'body': 'Hello from Lambda'}"
    filename = "index.py"
  }
}

# --- FastAPI API Lambda ---
resource "aws_lambda_function" "api" {
  function_name    = "${var.project_name}-api"
  filename         = data.archive_file.dummy_zip.output_path
  source_code_hash = data.archive_file.dummy_zip.output_base64sha256
  handler          = "backend.main.handler" # Routed through Mangum
  runtime          = "python3.11"
  role             = aws_iam_role.lambda_exec.arn
  timeout          = 30
  memory_size      = 512


  environment {
    variables = {
      ENV                       = "production"
      S3_DATA_BUCKET            = aws_s3_bucket.data_bucket.id
      DYNAMODB_USERS_TABLE      = aws_dynamodb_table.users.name
      DYNAMODB_PROFILES_TABLE   = aws_dynamodb_table.profiles.name
      DYNAMODB_SESSIONS_TABLE   = aws_dynamodb_table.sessions.name
      DYNAMODB_JOBS_TABLE       = aws_dynamodb_table.jobs.name
      DYNAMODB_JOBS_RAW_TABLE   = aws_dynamodb_table.jobs_raw.name
      DYNAMODB_JOBS_CLEANED_TABLE = aws_dynamodb_table.jobs_cleaned.name
      DYNAMODB_SETTINGS_TABLE   = aws_dynamodb_table.settings.name
      DYNAMODB_COMPANIES_TABLE  = aws_dynamodb_table.target_companies.name
      DYNAMODB_HISTORY_TABLE    = aws_dynamodb_table.scrape_history.name
      DYNAMODB_ERRORS_TABLE     = aws_dynamodb_table.portal_error_logs.name
      SMTP_SENDER               = var.smtp_sender
      SMTP_PASSWORD             = var.smtp_password
      SMTP_SERVER               = var.smtp_server
      SMTP_PORT                 = var.smtp_port
    }
  }
}

# --- Scraper Lambda (triggered by Schedule) ---
resource "aws_lambda_function" "scraper" {
  function_name    = "${var.project_name}-scraper"
  filename         = data.archive_file.dummy_zip.output_path
  source_code_hash = data.archive_file.dummy_zip.output_base64sha256
  handler          = "backend.scraper.lambda_handler"
  runtime          = "python3.11"
  role             = aws_iam_role.lambda_exec.arn
  timeout          = 900 # 15 minutes max
  memory_size      = 512

  environment {
    variables = {
      ENV                       = "production"
      S3_DATA_BUCKET            = aws_s3_bucket.data_bucket.id
      DYNAMODB_USERS_TABLE      = aws_dynamodb_table.users.name
      DYNAMODB_PROFILES_TABLE   = aws_dynamodb_table.profiles.name
      DYNAMODB_SESSIONS_TABLE   = aws_dynamodb_table.sessions.name
      DYNAMODB_JOBS_TABLE       = aws_dynamodb_table.jobs.name
      DYNAMODB_JOBS_RAW_TABLE   = aws_dynamodb_table.jobs_raw.name
      DYNAMODB_JOBS_CLEANED_TABLE = aws_dynamodb_table.jobs_cleaned.name
      DYNAMODB_SETTINGS_TABLE   = aws_dynamodb_table.settings.name
      DYNAMODB_COMPANIES_TABLE  = aws_dynamodb_table.target_companies.name
      DYNAMODB_HISTORY_TABLE    = aws_dynamodb_table.scrape_history.name
      DYNAMODB_ERRORS_TABLE     = aws_dynamodb_table.portal_error_logs.name
      SMTP_SENDER               = var.smtp_sender
      SMTP_PASSWORD             = var.smtp_password
      SMTP_SERVER               = var.smtp_server
      SMTP_PORT                 = var.smtp_port
    }
  }
}

# --- CloudWatch Log Metric Filters for Lambda Monitoring ---
resource "aws_cloudwatch_log_metric_filter" "api_log_errors" {
  name           = "${var.project_name}-api-errors"
  pattern        = "?ERROR ?Exception ?error ?exception"
  log_group_name = "/aws/lambda/${aws_lambda_function.api.function_name}"

  metric_transformation {
    name          = "ApiErrorCount"
    namespace     = "JobSeeker/Logs"
    value         = "1"
    default_value = "0"
  }
}

resource "aws_cloudwatch_log_metric_filter" "scraper_log_errors" {
  name           = "${var.project_name}-scraper-errors"
  pattern        = "?ERROR ?Exception ?error ?exception"
  log_group_name = "/aws/lambda/${aws_lambda_function.scraper.function_name}"

  metric_transformation {
    name          = "ScraperErrorCount"
    namespace     = "JobSeeker/Logs"
    value         = "1"
    default_value = "0"
  }
}



# --- EventBridge 30-Minute Scheduler ---
resource "aws_cloudwatch_event_rule" "scraper_schedule" {
  name                = "${var.project_name}-scraper-schedule"
  description         = "Triggers JobSeeker background scraper every 30 minutes"
  schedule_expression = "rate(30 minutes)"
}

resource "aws_cloudwatch_event_target" "scraper_target" {
  rule      = aws_cloudwatch_event_rule.scraper_schedule.name
  target_id = "scraper_lambda"
  arn       = aws_lambda_function.scraper.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.scraper.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.scraper_schedule.arn
}

# --- API Gateway (HTTP API) ---
resource "aws_apigatewayv2_api" "api_gw" {
  name          = "${var.project_name}-api-gateway"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["content-type", "authorization", "x-profile-id", "x-ai-provider", "x-ai-model", "x-ai-api-key"]
  }
}

resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id           = aws_apigatewayv2_api.api_gw.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.api.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "api_route" {
  api_id    = aws_apigatewayv2_api.api_gw.id
  route_key = "ANY /api/{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_stage" "api_stage" {
  api_id      = aws_apigatewayv2_api.api_gw.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "api_gw_permission" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api_gw.execution_arn}/*/*"
}

# --- S3 Bucket for Frontend ---
resource "aws_s3_bucket" "frontend_bucket" {
  bucket        = "${var.project_name}-frontend-bucket-${random_string.bucket_suffix.result}"
  force_destroy = true
}

# --- S3 Bucket for Data (Private) ---
resource "aws_s3_bucket" "data_bucket" {
  bucket        = "${var.project_name}-data-bucket-${random_string.bucket_suffix.result}"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "block_public_data" {
  bucket = aws_s3_bucket.data_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_website_configuration" "frontend_website" {
  bucket = aws_s3_bucket.frontend_bucket.id
  index_document {
    suffix = "index.html"
  }
}

resource "aws_s3_bucket_public_access_block" "block_public" {
  bucket = aws_s3_bucket.frontend_bucket.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# --- CloudFront Origin Access Control (OAC) ---
# resource "aws_cloudfront_origin_access_control" "oac" {
#   name                              = "${var.project_name}-oac"
#   description                       = "OAC for JobSeeker frontend bucket"
#   origin_access_control_origin_type = "s3"
#   signing_behavior                  = "always"
#   signing_protocol                  = "sigv4"
# }

# --- CloudFront Function for IP Whitelisting ---
# resource "aws_cloudfront_function" "ip_whitelist" {
#   name    = "${var.project_name}-ip-whitelist"
#   runtime = "cloudfront-js-2.0"
#   publish = true
#   code    = templatefile("${path.module}/cloudfront_function.js", {
#     whitelisted_ips_json = join(", ", formatlist("\"%s\"", var.whitelisted_ips))
#   })
# }

# --- CloudFront Distribution ---
# resource "aws_cloudfront_distribution" "cf_dist" {
#   enabled             = true
#   default_root_object = "index.html"

#   # Origin 1: S3 Frontend Bucket
#   origin {
#     domain_name              = aws_s3_bucket.frontend_bucket.bucket_regional_domain_name
#     origin_id                = "S3-Frontend"
#     origin_access_control_id = aws_cloudfront_origin_access_control.oac.id
#   }

#   # Origin 2: API Gateway HTTP API
#   origin {
#     domain_name = replace(aws_apigatewayv2_api.api_gw.api_endpoint, "https://", "")
#     origin_id   = "APIGateway-Backend"
#     custom_origin_config {
#       http_port              = 80
#       https_port             = 443
#       origin_protocol_policy = "https-only"
#       origin_ssl_protocols   = ["TLSv1.2"]
#     }
#   }

#   # Default Cache Behavior: routes to S3 bucket (Frontend files)
#   default_cache_behavior {
#     target_origin_id       = "S3-Frontend"
#     allowed_methods        = ["GET", "HEAD"]
#     cached_methods         = ["GET", "HEAD"]
#     viewer_protocol_policy = "redirect-to-https"

#     forwarded_values {
#       query_string = false
#       cookies {
#         forward = "none"
#       }
#     }

#     # IP Whitelisting intercept at edge
#     function_association {
#       event_type   = "viewer-request"
#       function_arn = aws_cloudfront_function.ip_whitelist.arn
#     }
#   }

#   # Cache Behavior for /api/* requests: routes to API Gateway Lambda
#   ordered_cache_behavior {
#     path_pattern           = "/api/*"
#     target_origin_id       = "APIGateway-Backend"
#     allowed_methods        = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
#     cached_methods         = ["GET", "HEAD"]
#     viewer_protocol_policy = "redirect-to-https"

#     # Disable caching for API calls to verify updates in real-time
#     cache_policy_id          = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad" # Managed-CachingDisabled
#     origin_request_policy_id = "b689b0a8-53d0-40b8-8856-687f7da947e7" # Managed-AllViewerExceptHostHeader

#     # IP Whitelisting intercept at edge
#     function_association {
#       event_type   = "viewer-request"
#       function_arn = aws_cloudfront_function.ip_whitelist.arn
#     }
#   }

#   restrictions {
#     geo_restriction {
#       restriction_type = "none"
#     }
#   }

#   viewer_certificate {
#     cloudfront_default_certificate = true
#   }
# }

# --- S3 Bucket Policy (Public Read Access) ---
resource "aws_s3_bucket_policy" "frontend_policy" {
  bucket = aws_s3_bucket.frontend_bucket.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "PublicReadGetObject"
      Effect    = "Allow"
      Principal = "*"
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.frontend_bucket.arn}/*"
    }]
  })
  depends_on = [aws_s3_bucket_public_access_block.block_public]
}

# --- Security Group for Monitoring EC2 Instance ---
resource "aws_security_group" "monitoring_sg" {
  name        = "${var.project_name}-monitoring-sg"
  description = "Allows SSH, Prometheus, and Grafana traffic from whitelisted IPs only"

  # Outbound rules: allow all traffic (e.g. to download packages or scrape CloudFront)
  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  # Inbound rules: SSH access from whitelist
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.whitelisted_ips
  }

  # Inbound rules: Grafana dashboard access from whitelist
  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = var.whitelisted_ips
  }

  # Inbound rules: Prometheus raw query UI access from whitelist
  ingress {
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = var.whitelisted_ips
  }
}

# --- Retrieve Amazon Linux 2023 AMI ---
data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023*-x86_64"]
  }
}

# --- IAM Role for Monitoring EC2 Instance ---
resource "aws_iam_role" "monitoring_role" {
  name = "${var.project_name}_monitoring_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "monitoring_cloudwatch" {
  role       = aws_iam_role.monitoring_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchReadOnlyAccess"
}

resource "aws_iam_role_policy_attachment" "monitoring_s3" {
  role       = aws_iam_role.monitoring_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}

resource "aws_iam_instance_profile" "monitoring_profile" {
  name = "${var.project_name}_monitoring_profile"
  role = aws_iam_role.monitoring_role.name
}

# --- EC2 Instance for Monitoring (Prometheus & Grafana) ---
resource "aws_instance" "monitoring" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = "t2.micro"
  vpc_security_group_ids = [aws_security_group.monitoring_sg.id]
  key_name               = var.ssh_key_name
  iam_instance_profile   = aws_iam_instance_profile.monitoring_profile.name

  user_data = templatefile("${path.module}/monitoring_userdata.sh", {
    cloudfront_domain  = replace(aws_apigatewayv2_api.api_gw.api_endpoint, "https://", "")
    project_name       = var.project_name
    aws_region         = var.aws_region
    frontend_bucket_id = aws_s3_bucket.frontend_bucket.id
  })


  tags = {
    Name = "${var.project_name}-monitoring-station"
  }
  
  # Ensure instance starts only after S3 website configuration is established
  depends_on = [aws_s3_bucket_website_configuration.frontend_website]
}

# --- Elastic IP for Monitoring Server ---
resource "aws_eip" "monitoring_eip" {
  domain   = "vpc"
  instance = aws_instance.monitoring.id

  tags = {
    Name = "${var.project_name}-monitoring-eip"
  }
}


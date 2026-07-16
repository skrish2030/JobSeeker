# JobSeeker Automated AWS Deployment Script
# Run this script to deploy the application end-to-end to AWS.

$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "       JobSeeker Automated AWS Deployer" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Run Terraform Apply
Write-Host "`n[STEP 1] Initializing and applying Terraform infrastructure..." -ForegroundColor Yellow
cd terraform
terraform init
terraform apply -auto-approve
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Terraform apply failed." -ForegroundColor Red
    exit 1
}

# Retrieve configuration outputs from Terraform
$s3Bucket = (terraform output -raw frontend_s3_bucket_name).Trim()
$apiGatewayUrl = (terraform output -raw api_gateway_url).Trim()
$apiLambda = "jobseeker-api"
$scraperLambda = "jobseeker-scraper"
cd ..

# 2. Package Backend Code & Dependencies
Write-Host "`n[STEP 2] Packaging backend code and dependencies..." -ForegroundColor Yellow
$buildDir = "build_lambda"
if (Test-Path $buildDir) { Remove-Item -Recurse -Force $buildDir }
New-Item -ItemType Directory -Path $buildDir > $null

# Copy backend python code
Copy-Item -Recurse -Filter "*.py" -Path backend -Destination "$buildDir\backend"

# Install backend dependencies cross-compiled for AWS Lambda Linux cp311 environment
Write-Host "Downloading Linux cp311 dependencies..."
pip install -r requirements.txt --target "$buildDir" --platform manylinux2014_x86_64 --only-binary=:all: --implementation cp --python-version 3.11

# Remove unused libraries to keep zip size smaller
Write-Host "Removing unused packages..."
Remove-Item -Recurse -Force "$buildDir\google", "$buildDir\google-*" -ErrorAction SilentlyContinue

# Remove unused platform binaries from tls-client to save ~80MB
Write-Host "Removing unused platform binaries from tls-client..."
py -c "import os, glob; [os.remove(f) for f in glob.glob('$buildDir/tls_client/dependencies/*') if os.path.isfile(f) and os.path.basename(f) not in ['tls-client-amd64.so', 'tls-client-x86.so', '__init__.py']]"



# Zip the package
$zipFile = "lambda_package.zip"
if (Test-Path $zipFile) { Remove-Item $zipFile }

# Create the archive
Compress-Archive -Path "$buildDir\*" -DestinationPath $zipFile

# 3. Upload Zip to S3 and Update AWS Lambda Functions
Write-Host "`n[STEP 3] Uploading code to AWS Lambda functions via S3..." -ForegroundColor Yellow
Write-Host "Uploading zip package to S3 ($s3Bucket)..."
aws s3 cp $zipFile "s3://$s3Bucket/$zipFile"

Write-Host "Updating API Lambda code from S3..."
aws lambda update-function-code --function-name $apiLambda --s3-bucket $s3Bucket --s3-key $zipFile > $null

Write-Host "Updating Scraper Lambda code from S3..."
aws lambda update-function-code --function-name $scraperLambda --s3-bucket $s3Bucket --s3-key $zipFile > $null

Write-Host "Cleaning up deployment package from S3..."
aws s3 rm "s3://$s3Bucket/$zipFile" > $null

# 4. Update frontend config.js with API Gateway URL
Write-Host "`n[STEP 4] Updating config.js with API Gateway URL..." -ForegroundColor Yellow
$configFile = "frontend/config.js"
$configContent = @"
// JobSeeker dynamic API URL configuration
// During local development, API requests are routed relatively.
// During AWS deployment, this is dynamically updated with the API Gateway endpoint.
window.API_BASE_URL = "$apiGatewayUrl";
"@
$configContent | Out-File -FilePath $configFile -Encoding utf8 -Force

# 5. Sync Frontend files to S3
Write-Host "`n[STEP 5] Syncing frontend static assets to S3 bucket ($s3Bucket)..." -ForegroundColor Yellow
# Sync static files to the static folder in the S3 bucket
aws s3 sync frontend "s3://$s3Bucket/static" --delete
# Copy index.html to the root of the S3 bucket
aws s3 cp frontend/index.html "s3://$s3Bucket/index.html"
# Copy Grafana dashboard JSON for EC2 monitoring instance to fetch
aws s3 cp grafana/dashboards/jobseeker_dashboard.json "s3://$s3Bucket/jobseeker_dashboard.json"


# 6. Restore local config.js for local development
Write-Host "`n[STEP 6] Restoring local config.js for local development..." -ForegroundColor Yellow
$configContentLocal = @"
// JobSeeker dynamic API URL configuration
// During local development, API requests are routed relatively.
// During AWS deployment, this is dynamically updated with the API Gateway endpoint.
window.API_BASE_URL = "";
"@
$configContentLocal | Out-File -FilePath $configFile -Encoding utf8 -Force

# Cleanup build artifacts
Remove-Item -Recurse -Force $buildDir
Remove-Item $zipFile

Write-Host "`n==================================================" -ForegroundColor Green
Write-Host "     JobSeeker Successfully Deployed to AWS!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green



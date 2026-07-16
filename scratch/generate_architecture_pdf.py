import os
from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font('helvetica', 'I', 8)
            self.set_text_color(150, 150, 150)
            self.cell(0, 10, 'JobSeeker Portal - System Architecture Documentation', 0, 0, 'L')
            self.cell(0, 10, f'Page {self.page_no()}', 0, 1, 'R')
            self.ln(5)

    def footer(self):
        if self.page_no() > 1:
            self.set_y(-15)
            self.set_font('helvetica', 'I', 8)
            self.set_text_color(150, 150, 150)
            self.cell(0, 10, 'Confidential - For Personal / Internal Use Only', 0, 0, 'C')

# Initialize PDF
pdf = PDF()
pdf.set_auto_page_break(auto=True, margin=15)

# --- TITLE PAGE ---
pdf.add_page()
pdf.set_fill_color(11, 19, 43) # Deep dark blue background
pdf.rect(0, 0, 210, 297, 'F')

# Title Title
pdf.set_y(80)
pdf.set_font('helvetica', 'B', 32)
pdf.set_text_color(255, 255, 255)
pdf.cell(0, 15, 'JOBSEEKER PORTAL', 0, 1, 'C')

# Subtitle
pdf.set_font('helvetica', '', 16)
pdf.set_text_color(0, 180, 216) # Neon cyan
pdf.cell(0, 10, 'AWS Serverless Architecture & Monitoring Station', 0, 1, 'C')

# Meta
pdf.set_y(220)
pdf.set_font('helvetica', 'I', 11)
pdf.set_text_color(200, 200, 200)
pdf.cell(0, 6, 'Version: 1.1.0', 0, 1, 'C')
pdf.cell(0, 6, 'Database Model: DynamoDB (Serverless)', 0, 1, 'C')
pdf.cell(0, 6, 'Monitoring: Prometheus & Grafana Station', 0, 1, 'C')
pdf.cell(0, 6, 'Date: June 20, 2026', 0, 1, 'C')


# --- PAGE 2: ARCHITECTURE DIAGRAM ---
pdf.add_page()
pdf.set_font('helvetica', 'B', 18)
pdf.set_text_color(11, 19, 43)
pdf.cell(0, 10, '1. System Architecture Diagram', 0, 1, 'L')
pdf.ln(5)

# Add Diagram Image
image_path = r"C:\Users\skris\.gemini\antigravity\brain\4a561c0f-7506-4f57-81db-ed8060e9c756\jobseeker_architecture_diagram_1781971850848.png"
if os.path.exists(image_path):
    # Scale image to fit width of 190mm
    pdf.image(image_path, x=10, y=35, w=190)
    pdf.set_y(155)
else:
    pdf.set_font('helvetica', 'I', 12)
    pdf.cell(0, 10, '[Diagram Image not found - check paths]', 0, 1, 'C')
    pdf.ln(100)

# Caption
pdf.set_font('helvetica', 'I', 9)
pdf.set_text_color(100, 100, 100)
pdf.multi_cell(0, 5, 'Figure 1.1: Complete cloud-native architecture showing serverless frontend and backend components, background scraper workers, DynamoDB partition keys, and the EC2-based Prometheus/Grafana monitoring environment.', align='C')
pdf.ln(10)


# --- PAGE 3: COMPONENT ANALYSIS ---
pdf.add_page()
pdf.set_font('helvetica', 'B', 18)
pdf.set_text_color(11, 19, 43)
pdf.cell(0, 10, '2. Component Breakdown & Functions', 0, 1, 'L')
pdf.ln(5)

components = [
    ("A. Frontend Layer (S3 + CloudFront)", 
     "The user interface is built as a single-page HTML/JavaScript application hosted on an AWS S3 bucket. A CloudFront Distribution acts as the content delivery network (CDN) to serve static assets (index.html, app.js, styles.css) with high speed and SSL protection. An edge configuration ensures IP whitelisting constraints are applied so only your authorized location can open the portal dashboard."),
    
    ("B. Backend API Layer (FastAPI + Mangum)",
     "The API backend runs on a serverless AWS Lambda function ('jobseeker-api') wrapped in FastAPI and routed via Mangum (ASGI adapter). The API gateway receives requests, authorizes session tokens, scopes user databases, and proxies calls. This layer hosts user settings, profile management, and dashboard API queries. To prevent latency issues, authentication middleware partitions access parameters on DynamoDB."),
    
    ("C. Background Scraper Engine (python-jobspy)",
     "A separate AWS Lambda function ('jobseeker-scraper') executes scheduled scans. Triggered by an EventBridge 30-minute scheduler or manually via the UI, it imports jobs using 'python-jobspy' from major boards (LinkedIn, Indeed, ZipRecruiter, Google). Scrapes run asynchronously and save data to DynamoDB without loading down the web API runtime."),
    
    ("D. Scoped Database (DynamoDB Tables)",
     "We use a serverless DynamoDB backend configured for Pay-As-You-Go efficiency. Tables are fully partitioned to prevent multi-tenant cross-contamination: \n"
     "- jobseeker_settings: Contains credentials, search queries, and CV text scoped by user_id and profile_id.\n"
     "- jobseeker_jobs: Contains job details, statuses, and matching scores.\n"
     "- jobseeker_users & jobseeker_user_sessions: Manages user login states, hashes, and session expiry.")
]

for title, desc in components:
    pdf.set_font('helvetica', 'B', 12)
    pdf.set_text_color(0, 119, 182) # Blue
    pdf.cell(0, 8, title, 0, 1, 'L')
    pdf.set_font('helvetica', '', 10)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 5, desc)
    pdf.ln(6)


# --- PAGE 4: MONITORING & AI DETAILS ---
pdf.add_page()
pdf.set_font('helvetica', 'B', 18)
pdf.set_text_color(11, 19, 43)
pdf.cell(0, 10, '3. Monitoring Station & AI Integration', 0, 1, 'L')
pdf.ln(5)

details = [
    ("E. EC2 Monitoring Station (Prometheus & Grafana)",
     "A dedicated EC2 instance ('jobseeker-monitoring-station') runs our system observability tools:\n"
     "- Prometheus: Periodically scrapes metrics from the FastAPI backend (/api/metrics) and the AWS Metrics Exporter.\n"
     "- Node Exporter: Monitors EC2 hardware metrics (CPU, memory, disk usage).\n"
     "- Grafana: Hosts the dashboard. To keep the EC2 userdata payload below AWS's 16KB limit, the dashboard JSON is uploaded to S3 during deployment. The EC2 instance retrieves it dynamically on boot to configure the Grafana visuals.\n"
     "Metric filters are configured directly on CloudWatch logs to count API and Scraper error counts, feeding into Prometheus alerts."),
     
    ("F. Google AI Studio & Gemini Integration",
     "AI features are invoked strictly when requested in the UI (e.g. CV tailoring, cover letter writer, mock prep guide, and interactive chat). Background scraping does not make AI calls to prevent quota exhaustion.\n"
     "Authentication middleware validates the custom X-AI-API-Key headers so requests execute under your specific profile credentials.\n"
     "The python backend uses fail-fast validation: if Google AI Studio returns a 429 Quota Exceeded error (billing or limit issue), the system stops retrying immediately, bypassing execution limits and returning a clear UI notification.")
]

for title, desc in details:
    pdf.set_font('helvetica', 'B', 12)
    pdf.set_text_color(0, 119, 182)
    pdf.cell(0, 8, title, 0, 1, 'L')
    pdf.set_font('helvetica', '', 10)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 5, desc)
    pdf.ln(6)


# --- PAGE 5: AWS RESOURCES MANIFEST ---
pdf.add_page()
pdf.set_font('helvetica', 'B', 18)
pdf.set_text_color(11, 19, 43)
pdf.cell(0, 10, '4. AWS Resource Names & Config Details', 0, 1, 'L')
pdf.ln(5)

pdf.set_font('helvetica', 'B', 12)
pdf.set_text_color(0, 119, 182)
pdf.cell(0, 8, 'A. Lambda Functions & Log Groups', 0, 1, 'L')
pdf.set_font('helvetica', '', 10)
pdf.set_text_color(50, 50, 50)
pdf.cell(0, 5, '  * API Lambda Name: jobseeker-api', 0, 1, 'L')
pdf.cell(0, 5, '    Log Group: /aws/lambda/jobseeker-api', 0, 1, 'L')
pdf.cell(0, 5, '  * Scraper Lambda Name: jobseeker-scraper', 0, 1, 'L')
pdf.cell(0, 5, '    Log Group: /aws/lambda/jobseeker-scraper', 0, 1, 'L')
pdf.ln(4)

pdf.set_font('helvetica', 'B', 12)
pdf.set_text_color(0, 119, 182)
pdf.cell(0, 8, 'B. S3 Buckets', 0, 1, 'L')
pdf.set_font('helvetica', '', 10)
pdf.set_text_color(50, 50, 50)
pdf.cell(0, 5, '  * Frontend Website Bucket: jobseeker-frontend-bucket-[suffix]', 0, 1, 'L')
pdf.cell(0, 5, '  * Private Data Bucket: jobseeker-data-bucket-[suffix]', 0, 1, 'L')
pdf.ln(4)

pdf.set_font('helvetica', 'B', 12)
pdf.set_text_color(0, 119, 182)
pdf.cell(0, 8, 'C. DynamoDB Tables (Serverless Pay-As-You-Go)', 0, 1, 'L')
pdf.set_font('helvetica', '', 10)
pdf.set_text_color(50, 50, 50)
pdf.cell(0, 5, '  * Users Table: jobseeker_users', 0, 1, 'L')
pdf.cell(0, 5, '  * User Sessions Table: jobseeker_user_sessions', 0, 1, 'L')
pdf.cell(0, 5, '  * Profiles Table: jobseeker_profiles', 0, 1, 'L')
pdf.cell(0, 5, '  * Jobs Table: jobseeker_jobs', 0, 1, 'L')
pdf.cell(0, 5, '  * Raw Jobs Table: jobseeker_jobs_raw', 0, 1, 'L')
pdf.cell(0, 5, '  * Cleaned Jobs Table: jobseeker_jobs_cleaned', 0, 1, 'L')
pdf.cell(0, 5, '  * Settings Table: jobseeker_settings', 0, 1, 'L')
pdf.cell(0, 5, '  * Target Companies Table: jobseeker_target_companies', 0, 1, 'L')
pdf.cell(0, 5, '  * Scrape History Table: jobseeker_scrape_history', 0, 1, 'L')
pdf.cell(0, 5, '  * Portal Error Logs Table: jobseeker_portal_error_logs', 0, 1, 'L')
pdf.ln(4)

pdf.set_font('helvetica', 'B', 12)
pdf.set_text_color(0, 119, 182)
pdf.cell(0, 8, 'D. Networking, Security, & Observability Names', 0, 1, 'L')
pdf.set_font('helvetica', '', 10)
pdf.set_text_color(50, 50, 50)
pdf.cell(0, 5, '  * API Gateway Router: jobseeker-api-gateway', 0, 1, 'L')
pdf.cell(0, 5, '  * EventBridge Scraper Scheduler: jobseeker-scraper-schedule', 0, 1, 'L')
pdf.cell(0, 5, '  * Monitoring Station Instance: jobseeker-monitoring-station', 0, 1, 'L')
pdf.cell(0, 5, '  * Monitoring Security Group: jobseeker-monitoring-sg', 0, 1, 'L')
pdf.cell(0, 5, '  * Monitoring Elastic IP Alloc: jobseeker-monitoring-eip', 0, 1, 'L')
pdf.cell(0, 5, '  * IAM Lambda Execution Role: jobseeker_lambda_exec_role', 0, 1, 'L')
pdf.cell(0, 5, '  * IAM EC2 Monitoring Role: jobseeker_monitoring_role', 0, 1, 'L')

# Output PDF to Desktop / JobSeeker folder
output_path = r"C:\Users\skris\OneDrive\Desktop\JobSeeker\jobseeker_architecture.pdf"
pdf.output(output_path)
print("PDF successfully generated at:", output_path)

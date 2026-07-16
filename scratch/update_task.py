task_content = """# DynamoDB Migration & UI Optimization Checklist

- [x] Implement DynamoDB Database Access Layer in [database.py](file:///C:/Users/skris/OneDrive/Desktop/JobSeeker/backend/database.py)
  - [x] Initialize boto3 DynamoDB resource and configure table environment variables
  - [x] Implement User registration, login, and MFA verification functions using DynamoDB
  - [x] Implement Session validation and Profile CRUD operations using DynamoDB
  - [x] Implement Settings CRUD operations (including master settings inheritance) using DynamoDB
  - [x] Implement Priority Target Companies CRUD using DynamoDB
  - [x] Implement Scrape History and Portal Error logging using DynamoDB
  - [x] Implement Jobs insertion, deletion, status updates, and custom post-filtering in `get_jobs()` using DynamoDB
- [x] Refactor Web Server Routing in [main.py](file:///C:/Users/skris/OneDrive/Desktop/JobSeeker/backend/main.py)
  - [x] Remove `db_routing_middleware` SQLite/S3 synchronization logic
  - [x] Update session token validation check to query DynamoDB
  - [x] Refactor search endpoint `/api/scrape/find` to query DynamoDB and apply keyword/location filters
- [x] Update Background Tasks
  - [x] Update [scraper.py](file:///C:/Users/skris/OneDrive/Desktop/JobSeeker/backend/scraper.py) to write scraper logs and jobs directly to DynamoDB
  - [x] Update [scheduler.py](file:///C:/Users/skris/OneDrive/Desktop/JobSeeker/backend/scheduler.py) to check schedules and profiles in DynamoDB
- [x] Implement Query Pagination
  - [x] Implement DynamoDB pagination using LastEvaluatedKey in get_jobs, get_target_companies, and get_jobs_to_email
  - [x] Create and run migration script to transfer legacy SQLite jobs, companies, and settings into DynamoDB
- [x] Optimize Status Polling Loop
  - [x] Restrict /api/status requests to logged-in sessions only
  - [x] Implement visibility checks to poll only when analytics panel is open or logs tab is active
  - [x] Trigger immediate status updates upon toggling panel
- [x] Enhance Responsive Layout Design
  - [x] Add max-width 1200px query to collapse sidebar to narrow icon-only mode and hide text labels
  - [x] Turn analytics panel into absolute side drawer overlay on medium viewports
  - [x] Add max-width 992px media query to slide details view over feed (mobile layout) on portrait tablets
- [x] Verification
  - [x] Create verification script `scratch/test_dynamodb_crud.py` to test the new backend locally
  - [x] Verify DynamoDB query results size (2,010 jobs, 11,031 companies) after pagination fix
  - [ ] Verify deployment via `.\\deploy.ps1` (to be run manually by USER)
"""

with open("C:/Users/skris/.gemini/antigravity/brain/4a561c0f-7506-4f57-81db-ed8060e9c756/task.md", "w", encoding="utf-8") as f:
    f.write(task_content)

print("Task checklist updated successfully!")

@echo off
cd /d "C:\Users\skris\OneDrive\Desktop\JobSeeker"
echo [%date% %time%] Starting scheduled job scraper... >> scraper_task.log
set PYTHONPATH=.
.venv\Scripts\python.exe backend\scraper.py >> scraper_task.log 2>&1
echo [%date% %time%] Scraper finished. >> scraper_task.log

@echo off
title JobSeeker Background Scraper
cd /d "%~dp0scraper"

:loop
echo ====================================================
echo [%date% %time%] Starting scraping cycle...
echo ====================================================

echo.
echo [1/4] Running Main Job Scraper (Zero-Cost Local Heuristics)...
python main.py

echo.
echo [2/4] Running Market Intelligence (YouTube Trends)...
python market_intelligence.py

echo.
echo [3/4] Running Base Analytics Engine...
python analytics.py

echo.
echo [4/4] Running Predictive Analytics Engine...
python predictive_analytics.py

echo.
echo ====================================================
echo [%date% %time%] Cycle Complete! Sleeping for 4 hours...
echo ====================================================
timeout /t 14400 /nobreak
goto loop

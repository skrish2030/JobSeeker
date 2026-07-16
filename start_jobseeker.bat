@echo off
cd /d "C:\Users\skris\OneDrive\Desktop\JobSeeker"

echo Starting FastAPI Backend...
start "FastAPI Backend" cmd /c ".venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

echo Starting Grafana...
start "Grafana Server" cmd /c "cd .monitoring\grafana-v10.4.2\bin && grafana-server.exe"

echo Starting Prometheus...
start "Prometheus Server" cmd /c "cd .monitoring\prometheus-2.53.1.windows-amd64 && prometheus.exe --config.file=C:\Users\skris\OneDrive\Desktop\JobSeeker\prometheus.yml"

echo All services started! You can close this window.

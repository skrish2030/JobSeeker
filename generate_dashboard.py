import json
import uuid

def create_panel(title, expr, type="timeseries", gridPos=None, id=1, custom_options=None, format="time_series"):
    panel = {
        "id": id,
        "title": title,
        "type": type,
        "datasource": {"type": "prometheus", "uid": "Prometheus"},
        "gridPos": gridPos or {"h": 8, "w": 12, "x": 0, "y": 0},
        "targets": [
            {
                "datasource": {"type": "prometheus", "uid": "Prometheus"},
                "expr": expr,
                "refId": "A",
                "format": format,
                "instant": True if type in ["piechart", "barchart", "stat"] else False,
                "legendFormat": custom_options.pop("legendFormat", "") if custom_options and "legendFormat" in custom_options else ""
            }
        ]
    }
    
    if type == "stat":
        panel["options"] = {
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "orientation": "auto",
            "textMode": "auto",
            "colorMode": "value",
            "graphMode": "area"
        }
    elif type == "timeseries":
        panel["options"] = {
            "legend": {"displayMode": "list", "placement": "bottom", "calcs": []}
        }
    elif type == "table":
        panel["options"] = {
            "showHeader": True
        }
        
    if custom_options:
        panel.setdefault("options", {}).update(custom_options)
        
    return panel

dashboard = {
    "id": None,
    "title": "JobSeeker Analytics",
    "uid": "jobseeker-dash-v6",
    "tags": ["jobseeker"],
    "timezone": "browser",
    "schemaVersion": 39,
    "version": 6,
    "refresh": "10s",
    "panels": [
        # ROW 1: Application Health & SRE (y=0)
        create_panel("API Request Rate", "sum(rate(http_requests_total[5m]))", type="timeseries", gridPos={"h": 7, "w": 6, "x": 0, "y": 0}, id=101),
        create_panel("API Error Rate (4xx & 5xx)", "sum(rate(http_requests_total{status=~\"[45]..\"}[5m]))", type="timeseries", gridPos={"h": 7, "w": 6, "x": 6, "y": 0}, id=102),
        create_panel("API P95 Latency", "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))", type="timeseries", gridPos={"h": 7, "w": 6, "x": 12, "y": 0}, id=103),
        create_panel("API Errors Table (Last 24h)", "sum by (handler, status) (increase(http_requests_total{status=~\"[45]..\"}[24h])) > 0", type="table", format="table", gridPos={"h": 7, "w": 6, "x": 18, "y": 0}, id=104),

        # ROW 2: Scraper Pipeline Metrics (y=7)
        create_panel("Scraper Run Status (1=Pass, 0=Fail)", "jobseeker_scraper_last_run_status", type="timeseries", gridPos={"h": 7, "w": 8, "x": 0, "y": 7}, id=201, custom_options={"legend": {"displayMode": "hidden"}}),
        create_panel("New Jobs Saved (Per Scrape)", "jobseeker_scraper_last_run_new_jobs", type="timeseries", gridPos={"h": 7, "w": 8, "x": 8, "y": 7}, id=202),
        create_panel("Total Jobs Found (Per Scrape)", "jobseeker_scraper_last_run_jobs_found", type="timeseries", gridPos={"h": 7, "w": 8, "x": 16, "y": 7}, id=203),

        # ROW 3: Business Analytics (y=14)
        create_panel("Total Jobs Database", "sum(jobseeker_jobs_total)", type="stat", gridPos={"h": 5, "w": 6, "x": 0, "y": 14}, id=300),
        create_panel("Jobs by Source", "jobseeker_jobs_total", type="barchart", gridPos={"h": 7, "w": 6, "x": 6, "y": 14}, id=301, custom_options={"legendFormat": "{{source}}"}),
        create_panel("Jobs by Timeframe", "jobseeker_jobs_by_timeframe", type="barchart", gridPos={"h": 7, "w": 4, "x": 12, "y": 14}, id=302, custom_options={"legendFormat": "{{timeframe}}"}),
        create_panel("IT vs Non-IT Jobs", "jobseeker_jobs_by_category", type="piechart", gridPos={"h": 7, "w": 4, "x": 16, "y": 14}, id=303, custom_options={"pieType": "donut", "legendFormat": "{{category}}"}),
        create_panel("Recruiter vs Direct Hire", "jobseeker_jobs_by_employer_type", type="piechart", gridPos={"h": 7, "w": 4, "x": 20, "y": 14}, id=304, custom_options={"pieType": "donut", "legendFormat": "{{type}}"}),
    ]
}

print(json.dumps(dashboard, indent=2))

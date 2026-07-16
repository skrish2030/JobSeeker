#!/bin/bash
# Amazon Linux 2023 User Data for Prometheus, Node Exporter, and Grafana

# Update and install utilities
dnf update -y
dnf install -y tar wget

# --- Install Prometheus ---
mkdir -p /opt/prometheus
cd /tmp
wget https://github.com/prometheus/prometheus/releases/download/v2.53.1/prometheus-2.53.1.linux-amd64.tar.gz
tar -xzf prometheus-2.53.1.linux-amd64.tar.gz
mv prometheus-2.53.1.linux-amd64/* /opt/prometheus/

# Create system user for Prometheus
useradd --no-create-home --shell /bin/false prometheus || true
chown -R prometheus:prometheus /opt/prometheus

# Create prometheus.yml config file
cat <<'EOF' > /opt/prometheus/prometheus.yml
global:
  scrape_interval: 10s
  evaluation_interval: 10s

scrape_configs:
  - job_name: 'jobseeker-api-prod'
    metrics_path: '/api/metrics'
    scheme: https
    static_configs:
      - targets: ['${cloudfront_domain}']

  - job_name: 'monitoring-station-ec2'
    static_configs:
      - targets: ['localhost:9100']

  - job_name: 'aws-metrics'
    static_configs:
      - targets: ['localhost:9106']
EOF


# Create Prometheus systemd service definition
cat <<'EOF' > /etc/systemd/system/prometheus.service
[Unit]
Description=Prometheus Service
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/opt/prometheus/prometheus \
    --config.file=/opt/prometheus/prometheus.yml \
    --storage.tsdb.path=/opt/prometheus/data \
    --web.console.templates=/opt/prometheus/consoles \
    --web.console.libraries=/opt/prometheus/console_libraries

[Install]
WantedBy=multi-user.target
EOF

# --- Install Node Exporter ---
mkdir -p /opt/node_exporter
cd /tmp
wget https://github.com/prometheus/node_exporter/releases/download/v1.8.1/node_exporter-1.8.1.linux-amd64.tar.gz
tar -xzf node_exporter-1.8.1.linux-amd64.tar.gz
mv node_exporter-1.8.1.linux-amd64/node_exporter /opt/node_exporter/
chown -R prometheus:prometheus /opt/node_exporter

cat <<'EOF' > /etc/systemd/system/node_exporter.service
[Unit]
Description=Node Exporter
After=network.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/opt/node_exporter/node_exporter

[Install]
WantedBy=multi-user.target
EOF

# --- Install Grafana ---
dnf install -y --nogpgcheck https://dl.grafana.com/oss/release/grafana-10.4.1-1.x86_64.rpm

# Configure Grafana Prometheus Datasource autoprovisioning
mkdir -p /etc/grafana/provisioning/datasources
cat <<'EOF' > /etc/grafana/provisioning/datasources/prometheus.yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://localhost:9090
    isDefault: true
    editable: false
EOF

# Configure Grafana Dashboard provider autoprovisioning
mkdir -p /etc/grafana/provisioning/dashboards
cat <<'EOF' > /etc/grafana/provisioning/dashboards/dashboards.yaml
apiVersion: 1

providers:
  - name: 'JobSeeker Dashboards'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    editable: true
    options:
      path: /etc/grafana/dashboards
      updateIntervalSeconds: 30
EOF

# Create Dashboard JSON config directory
mkdir -p /etc/grafana/dashboards

# Write background script to fetch the dashboard JSON from S3
cat <<'EOF' > /usr/local/bin/fetch_dashboard.sh
#!/bin/bash
# Loop forever to sync dashboard changes dynamically without recreating the instance
while true; do
  if aws s3 cp s3://${frontend_bucket_id}/jobseeker_dashboard.json /etc/grafana/dashboards/jobseeker_dashboard.json --region ${aws_region}; then
    echo "Dashboard successfully synchronized from S3."
    chown -R grafana:grafana /etc/grafana/dashboards
  else
    echo "Failed to fetch dashboard from S3, retrying..."
  fi
  sleep 60
done
EOF
chmod +x /usr/local/bin/fetch_dashboard.sh

# Run the fetch script in the background
/usr/local/bin/fetch_dashboard.sh >/var/log/fetch_dashboard.log 2>&1 &


# --- Install Python dependencies for AWS Metrics Exporter ---
dnf install -y python3-pip
python3 -m venv /opt/aws_exporter_venv
/opt/aws_exporter_venv/bin/pip install boto3 prometheus_client

# --- Create AWS Metrics Exporter Script ---
mkdir -p /opt/aws_metrics_exporter
cat <<'EXPORTER_EOF' > /opt/aws_metrics_exporter/aws_metrics_exporter.py
import datetime
import os
import sys
import time
import logging
import threading
import boto3
from prometheus_client import start_http_server, Gauge

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger("aws_exporter")

REGION = "${aws_region}"
PROJECT_NAME = "${project_name}"

# Setup Prometheus Gauges
lambda_invocations = Gauge('aws_lambda_invocations_total', 'Total number of Lambda invocations', ['function_name'])
lambda_errors = Gauge('aws_lambda_errors_total', 'Total number of Lambda errors', ['function_name'])
lambda_duration = Gauge('aws_lambda_duration_seconds', 'Average Lambda duration in seconds', ['function_name'])
lambda_throttles = Gauge('aws_lambda_throttles_total', 'Total number of Lambda throttles', ['function_name'])
lambda_concurrent = Gauge('aws_lambda_concurrent_executions', 'Maximum concurrent executions of Lambda', ['function_name'])

dynamodb_consumed_read = Gauge('aws_dynamodb_consumed_read_capacity_units', 'Consumed Read Capacity Units', ['table_name'])
dynamodb_consumed_write = Gauge('aws_dynamodb_consumed_write_capacity_units', 'Consumed Write Capacity Units', ['table_name'])
dynamodb_read_throttles = Gauge('aws_dynamodb_read_throttle_events', 'Read Throttle Events count', ['table_name'])
dynamodb_write_throttles = Gauge('aws_dynamodb_write_throttle_events', 'Write Throttle Events count', ['table_name'])
dynamodb_latency = Gauge('aws_dynamodb_successful_request_latency_seconds', 'Average Successful Request Latency in seconds', ['table_name', 'operation'])
dynamodb_system_errors = Gauge('aws_dynamodb_system_errors', 'System errors count', ['table_name'])

billing_estimated_charges = Gauge('aws_billing_estimated_charges_usd', 'Estimated monthly AWS charges in USD')

# Log Metrics Gauges
aws_log_errors_total = Gauge('aws_log_errors_total', 'Total number of error logs per log group', ['log_group'])

def fetch_metrics():
    session = boto3.Session(region_name=REGION)
    cw = session.client('cloudwatch')
    cw_billing = boto3.Session(region_name='us-east-1').client('cloudwatch')
    
    lambda_funcs = [f"{PROJECT_NAME}-api", f"{PROJECT_NAME}-scraper"]
    ddb_tables = [
        f"{PROJECT_NAME}_users",
        f"{PROJECT_NAME}_profiles",
        f"{PROJECT_NAME}_user_sessions",
        f"{PROJECT_NAME}_jobs",
        f"{PROJECT_NAME}_jobs_raw",
        f"{PROJECT_NAME}_jobs_cleaned",
        f"{PROJECT_NAME}_settings",
        f"{PROJECT_NAME}_target_companies",
        f"{PROJECT_NAME}_scrape_history",
        f"{PROJECT_NAME}_portal_error_logs"
    ]
    
    while True:
        try:
            logger.info("Starting CloudWatch metrics scrape...")
            now = datetime.datetime.utcnow()
            start_time = now - datetime.timedelta(minutes=10)
            end_time = now
            
            queries = []
            query_id_map = {}
            query_counter = 0
            
            # --- Build Log Group Queries ---
            q_id_api = f"l_{query_counter}"
            query_counter += 1
            queries.append({
                'Id': q_id_api,
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'JobSeeker/Logs',
                        'MetricName': 'ApiErrorCount'
                    },
                    'Period': 300,
                    'Stat': 'Sum'
                }
            })
            query_id_map[q_id_api] = {'type': 'log', 'log_group': f"/aws/lambda/{PROJECT_NAME}-api", 'metric': 'ApiErrorCount'}

            q_id_scraper = f"l_{query_counter}"
            query_counter += 1
            queries.append({
                'Id': q_id_scraper,
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'JobSeeker/Logs',
                        'MetricName': 'ScraperErrorCount'
                    },
                    'Period': 300,
                    'Stat': 'Sum'
                }
            })
            query_id_map[q_id_scraper] = {'type': 'log', 'log_group': f"/aws/lambda/{PROJECT_NAME}-scraper", 'metric': 'ScraperErrorCount'}

            for func in lambda_funcs:
                for metric_name, stat in [('Invocations', 'Sum'), ('Errors', 'Sum'), ('Duration', 'Average'), ('Throttles', 'Sum'), ('ConcurrentExecutions', 'Maximum')]:
                    q_id = f"l_{query_counter}"
                    query_counter += 1
                    queries.append({
                        'Id': q_id,
                        'MetricStat': {
                            'Metric': {
                                'Namespace': 'AWS/Lambda',
                                'MetricName': metric_name,
                                'Dimensions': [{'Name': 'FunctionName', 'Value': func}]
                            },
                            'Period': 300,
                            'Stat': stat
                        }
                    })
                    query_id_map[q_id] = {'type': 'lambda', 'function': func, 'metric': metric_name}
            
            for table in ddb_tables:
                for metric_name, stat in [('ConsumedReadCapacityUnits', 'Sum'), ('ConsumedWriteCapacityUnits', 'Sum'), ('ReadThrottleEvents', 'Sum'), ('WriteThrottleEvents', 'Sum'), ('SystemErrors', 'Sum')]:
                    q_id = f"d_{query_counter}"
                    query_counter += 1
                    queries.append({
                        'Id': q_id,
                        'MetricStat': {
                            'Metric': {
                                'Namespace': 'AWS/DynamoDB',
                                'MetricName': metric_name,
                                'Dimensions': [{'Name': 'TableName', 'Value': table}]
                            },
                            'Period': 300,
                            'Stat': stat
                        }
                    })
                    query_id_map[q_id] = {'type': 'dynamodb', 'table': table, 'metric': metric_name}
                    
                for op in ['GetItem', 'PutItem', 'Query', 'Scan']:
                    q_id = f"d_{query_counter}"
                    query_counter += 1
                    queries.append({
                        'Id': q_id,
                        'MetricStat': {
                            'Metric': {
                                'Namespace': 'AWS/DynamoDB',
                                'MetricName': 'SuccessfulRequestLatency',
                                'Dimensions': [
                                    {'Name': 'TableName', 'Value': table},
                                    {'Name': 'Operation', 'Value': op}
                                ]
                            },
                            'Period': 300,
                            'Stat': 'Average'
                        }
                    })
                    query_id_map[q_id] = {'type': 'dynamodb_latency', 'table': table, 'operation': op}
            
            res = cw.get_metric_data(
                MetricDataQueries=queries,
                StartTime=start_time,
                EndTime=end_time
            )
            
            for result in res.get('MetricDataResults', []):
                q_id = result.get('Id')
                values = result.get('Values')
                val = values[0] if values else 0.0
                
                info = query_id_map.get(q_id)
                if not info:
                    continue
                    
                if info['type'] == 'lambda':
                    func = info['function']
                    metric = info['metric']
                    if metric == 'Invocations':
                        lambda_invocations.labels(function_name=func).set(val)
                    elif metric == 'Errors':
                        lambda_errors.labels(function_name=func).set(val)
                    elif metric == 'Duration':
                        lambda_duration.labels(function_name=func).set(val / 1000.0)
                    elif metric == 'Throttles':
                        lambda_throttles.labels(function_name=func).set(val)
                    elif metric == 'ConcurrentExecutions':
                        lambda_concurrent.labels(function_name=func).set(val)
                        
                elif info['type'] == 'dynamodb':
                    table = info['table']
                    metric = info['metric']
                    if metric == 'ConsumedReadCapacityUnits':
                        dynamodb_consumed_read.labels(table_name=table).set(val)
                    elif metric == 'ConsumedWriteCapacityUnits':
                        dynamodb_consumed_write.labels(table_name=table).set(val)
                    elif metric == 'ReadThrottleEvents':
                        dynamodb_read_throttles.labels(table_name=table).set(val)
                    elif metric == 'WriteThrottleEvents':
                        dynamodb_write_throttles.labels(table_name=table).set(val)
                    elif metric == 'SystemErrors':
                        dynamodb_system_errors.labels(table_name=table).set(val)
                        
                elif info['type'] == 'dynamodb_latency':
                    table = info['table']
                    op = info['operation']
                    dynamodb_latency.labels(table_name=table, operation=op).set(val / 1000.0)
                    
                elif info['type'] == 'log':
                    log_group = info['log_group']
                    aws_log_errors_total.labels(log_group=log_group).set(val)

            billing_queries = [{
                'Id': 'billing_charges',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/Billing',
                        'MetricName': 'EstimatedCharges',
                        'Dimensions': [{'Name': 'Currency', 'Value': 'USD'}]
                    },
                    'Period': 21600,
                    'Stat': 'Maximum'
                }
            }]
            
            b_res = cw_billing.get_metric_data(
                MetricDataQueries=billing_queries,
                StartTime=now - datetime.timedelta(hours=24),
                EndTime=now
            )
            
            for result in b_res.get('MetricDataResults', []):
                if result.get('Id') == 'billing_charges':
                    values = result.get('Values')
                    val = values[0] if values else 0.0
                    billing_estimated_charges.set(val)
                    logger.info("Billing estimated charges: $%s USD" % val)

            logger.info("Successfully completed CloudWatch metrics scrape.")
        except Exception as e:
            logger.error("Error fetching CloudWatch metrics: %s" % e, exc_info=True)
            
        time.sleep(60)

if __name__ == '__main__':
    logger.info("Starting AWS Metrics Exporter...")
    t = threading.Thread(target=fetch_metrics, daemon=True)
    t.start()
    
    start_http_server(9106)
    logger.info("Prometheus HTTP server started on port 9106.")
    
    while True:
        time.sleep(3600)
EXPORTER_EOF

# --- Create AWS Metrics Exporter systemd Service ---
cat <<'EOF' > /etc/systemd/system/aws_metrics_exporter.service
[Unit]
Description=AWS Metrics Exporter for Prometheus
After=network.target

[Service]
Type=simple
User=root
ExecStart=/opt/aws_exporter_venv/bin/python /opt/aws_metrics_exporter/aws_metrics_exporter.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd, enable and start services
systemctl daemon-reload
systemctl enable --now prometheus
systemctl enable --now node_exporter
systemctl enable --now grafana-server
systemctl enable --now aws_metrics_exporter


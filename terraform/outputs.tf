output "frontend_website_url" {
  value       = aws_s3_bucket_website_configuration.frontend_website.website_endpoint
  description = "The direct S3 website URL for the frontend."
}

output "api_gateway_url" {
  value       = aws_apigatewayv2_stage.api_stage.invoke_url
  description = "The API Gateway stage invoke URL for the backend."
}

output "frontend_s3_bucket_name" {
  value       = aws_s3_bucket.frontend_bucket.id
  description = "The S3 bucket name to upload the frontend static files (HTML, CSS, JS) into."
}

output "api_gateway_endpoint" {
  value       = aws_apigatewayv2_api.api_gw.api_endpoint
  description = "The direct backend API Gateway endpoint URL (useful for troubleshooting)."
}

output "monitoring_instance_public_ip" {
  value       = aws_eip.monitoring_eip.public_ip
  description = "The static public IP address of the Prometheus/Grafana monitoring instance."
}

output "grafana_url" {
  value       = "http://${aws_eip.monitoring_eip.public_ip}:3000"
  description = "URL to access the Grafana visualization dashboard."
}

output "prometheus_url" {
  value       = "http://${aws_eip.monitoring_eip.public_ip}:9090"
  description = "URL to access the Prometheus raw query UI."
}

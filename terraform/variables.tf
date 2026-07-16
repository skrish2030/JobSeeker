variable "aws_region" {
  type        = string
  description = "The AWS region to deploy all resources into."
  default     = "us-east-1"
}

variable "whitelisted_ips" {
  type        = list(string)
  description = "List of client IP CIDR blocks allowed to access the CloudFront website (e.g., ['203.0.113.50/32'])."
  default     = ["0.0.0.0/0"] # Default to open, user should customize
}

variable "project_name" {
  type        = string
  description = "Name prefix for all JobSeeker resources."
  default     = "jobseeker"
}

variable "ssh_key_name" {
  type        = string
  description = "Name of the existing EC2 key pair for SSH access (optional)."
  default     = null
}

variable "smtp_sender" {
  type        = string
  description = "Default SMTP sender email address."
  default     = ""
}

variable "smtp_password" {
  type        = string
  description = "Default SMTP sender email password (app password)."
  default     = ""
  sensitive   = true
}

variable "smtp_server" {
  type        = string
  description = "Default SMTP server (e.g. smtp.gmail.com)."
  default     = "smtp.gmail.com"
}

variable "smtp_port" {
  type        = string
  description = "Default SMTP port (e.g. 587)."
  default     = "587"
}

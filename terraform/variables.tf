variable "project_name" {
    description = "Name prefix for all resources"
    type        = string
    validation {
      condition = can(regex("^[a-z0-9-]+$", var.project_name))
      error_message = "Project name must contain only lowercase letters, numbers, and hyphens."
    }
}

variable "aws_region" {
    description = "AWS region"
    type = string
    default = "ap-southeast-1"
}

variable "environment" {
  description = "Environment name (dev, test, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "test", "prod"], var.environment)
    error_message = "Environment must be one of: dev, test, prod."
  }
}

variable "lambda_timeout" {
    description = "Lambda function timeout in second"
    type        = number
    default     = 60
}

variable "api_throttle_burst_limit" {
  description = "API Gateway throttle burst limit"
  type        = number
  default     = 10
}

variable "api_throttle_rate_limit" {
  description = "API Gateway throttle rate limit"
  type        = number
  default     = 5
}

variable "use_custom_domain" {
  description = "Attach a custom domain to CloudFront"
  type        = bool
  default     = false
}

variable "root_domain" {
  description = "Apex domain name, e.g. mydomain.com"
  type        = string
  default     = ""
}

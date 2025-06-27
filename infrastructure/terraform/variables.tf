# Terraform variables for Sales Order System

variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "Google Cloud region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "Google Cloud zone"
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  default     = "production"
}

variable "db_tier" {
  description = "Cloud SQL instance tier"
  type        = string
  default     = "db-f1-micro"
}

variable "db_password" {
  description = "Database password for app user"
  type        = string
  sensitive   = true
}

variable "alert_email" {
  description = "Email address for monitoring alerts"
  type        = string
}

variable "backend_image" {
  description = "Backend container image"
  type        = string
  default     = "gcr.io/PROJECT_ID/sales-order-backend:latest"
}

variable "frontend_image" {
  description = "Frontend container image"
  type        = string
  default     = "gcr.io/PROJECT_ID/sales-order-frontend:latest"
}

variable "backend_cpu" {
  description = "Backend CPU allocation"
  type        = string
  default     = "1"
}

variable "backend_memory" {
  description = "Backend memory allocation"
  type        = string
  default     = "2Gi"
}

variable "backend_min_instances" {
  description = "Backend minimum instances"
  type        = number
  default     = 0
}

variable "backend_max_instances" {
  description = "Backend maximum instances"
  type        = number
  default     = 10
}

variable "frontend_cpu" {
  description = "Frontend CPU allocation"
  type        = string
  default     = "1"
}

variable "frontend_memory" {
  description = "Frontend memory allocation"
  type        = string
  default     = "1Gi"
}

variable "frontend_min_instances" {
  description = "Frontend minimum instances"
  type        = number
  default     = 0
}

variable "frontend_max_instances" {
  description = "Frontend maximum instances"
  type        = number
  default     = 5
}

variable "openai_api_key" {
  description = "OpenAI API key for language model integration"
  type        = string
  sensitive   = true
}
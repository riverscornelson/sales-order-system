# Terraform outputs for Sales Order System

output "project_id" {
  description = "Google Cloud Project ID"
  value       = var.project_id
}

output "region" {
  description = "Google Cloud region"
  value       = var.region
}

output "database_instance_name" {
  description = "Cloud SQL instance name"
  value       = google_sql_database_instance.main.name
}

output "database_connection_name" {
  description = "Cloud SQL connection name"
  value       = google_sql_database_instance.main.connection_name
}

output "database_private_ip" {
  description = "Cloud SQL private IP address"
  value       = google_sql_database_instance.main.private_ip_address
}

output "uploads_bucket_name" {
  description = "Uploads bucket name"
  value       = google_storage_bucket.uploads.name
}

output "vectors_bucket_name" {
  description = "Vectors bucket name"
  value       = google_storage_bucket.vectors.name
}

output "backend_service_account_email" {
  description = "Backend service account email"
  value       = google_service_account.backend_sa.email
}

output "frontend_service_account_email" {
  description = "Frontend service account email"
  value       = google_service_account.frontend_sa.email
}

output "vpc_connector_name" {
  description = "VPC Access Connector name"
  value       = google_vpc_access_connector.connector.name
}

output "network_name" {
  description = "VPC network name"
  value       = google_compute_network.vpc.name
}

output "subnet_name" {
  description = "VPC subnet name"
  value       = google_compute_subnetwork.subnet.name
}

output "backend_url" {
  description = "Backend service URL"
  value       = google_cloud_run_v2_service.backend.uri
}
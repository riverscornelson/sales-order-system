# Main Terraform configuration for Sales Order System infrastructure
terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }
}

# Configure Google Cloud Provider
provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Local variables
locals {
  services = [
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "storage.googleapis.com",
    "cloudbuild.googleapis.com",
    "secretmanager.googleapis.com",
    "aiplatform.googleapis.com",
    "vpcaccess.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com"
  ]
}

# Enable required APIs
resource "google_project_service" "services" {
  for_each = toset(local.services)
  project  = var.project_id
  service  = each.value

  disable_dependent_services = false
  disable_on_destroy        = false
}

# VPC and networking
resource "google_compute_network" "vpc" {
  name                    = "sales-order-vpc"
  auto_create_subnetworks = false
  
  depends_on = [google_project_service.services]
}

resource "google_compute_subnetwork" "subnet" {
  name          = "sales-order-subnet"
  ip_cidr_range = "10.0.0.0/24"
  network       = google_compute_network.vpc.id
  region        = var.region

  private_ip_google_access = true
}

# VPC Access Connector for Cloud Run to Cloud SQL
resource "google_vpc_access_connector" "connector" {
  name          = "vpc-connector"
  ip_cidr_range = "10.8.0.0/28"
  network       = google_compute_network.vpc.name
  region        = var.region
  
  depends_on = [google_project_service.services]
}

# Cloud SQL instance
resource "google_sql_database_instance" "main" {
  name             = "sales-order-db"
  database_version = "POSTGRES_15"
  region           = var.region
  deletion_protection = false

  settings {
    tier              = var.db_tier
    availability_type = "REGIONAL"
    disk_type         = "PD_SSD"
    disk_size         = 20
    disk_autoresize   = true

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true
      backup_retention_settings {
        retained_backups = 7
      }
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
      require_ssl     = true
    }

    database_flags {
      name  = "log_statement"
      value = "all"
    }
  }

  depends_on = [
    google_project_service.services,
    google_service_networking_connection.private_vpc_connection
  ]
}

# Private service connection for Cloud SQL
resource "google_compute_global_address" "private_ip_address" {
  name          = "private-ip-address"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
}

# Database and user
resource "google_sql_database" "database" {
  name     = "sales_orders"
  instance = google_sql_database_instance.main.name
}

resource "google_sql_user" "user" {
  name     = "app_user"
  instance = google_sql_database_instance.main.name
  password = var.db_password
}

# Cloud Storage buckets
resource "google_storage_bucket" "uploads" {
  name     = "sales-order-uploads-${var.project_id}"
  location = var.region

  public_access_prevention = "enforced"
  
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_storage_bucket" "vectors" {
  name     = "sales-order-vectors-${var.project_id}"
  location = var.region

  public_access_prevention = "enforced"
  
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }
}

# IAM Service Accounts
resource "google_service_account" "backend_sa" {
  account_id   = "sales-order-backend-sa"
  display_name = "Sales Order Backend Service Account"
  description  = "Service account for backend Cloud Run service"
}

resource "google_service_account" "frontend_sa" {
  account_id   = "sales-order-frontend-sa"
  display_name = "Sales Order Frontend Service Account"
  description  = "Service account for frontend Cloud Run service"
}

# IAM bindings for backend service account
resource "google_project_iam_member" "backend_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}

resource "google_project_iam_member" "backend_storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}

resource "google_project_iam_member" "backend_vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}

resource "google_project_iam_member" "backend_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}

resource "google_project_iam_member" "backend_logging_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}

resource "google_project_iam_member" "backend_monitoring_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.backend_sa.email}"
}

# Secret Manager secrets
resource "google_secret_manager_secret" "openai_api_key" {
  secret_id = "openai-api-key"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "database_url" {
  secret_id = "database-url-production"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "dynamics_config" {
  secret_id = "dynamics-config"
  
  replication {
    auto {}
  }
}

# Monitoring workspace
resource "google_monitoring_notification_channel" "email" {
  display_name = "Email Notification Channel"
  type         = "email"
  
  labels = {
    email_address = var.alert_email
  }
}

# Store secrets
resource "google_secret_manager_secret_version" "openai_api_key" {
  secret      = google_secret_manager_secret.openai_api_key.id
  secret_data = var.openai_api_key
}

resource "google_secret_manager_secret_version" "database_url" {
  secret      = google_secret_manager_secret.database_url.id
  secret_data = "postgresql://${google_sql_user.user.name}:${var.db_password}@${google_sql_database_instance.main.private_ip_address}:5432/${google_sql_database.database.name}?sslmode=require"
}

# Cloud Run services
resource "google_cloud_run_v2_service" "backend" {
  name     = "sales-order-backend"
  location = var.region
  
  template {
    service_account = google_service_account.backend_sa.email
    
    scaling {
      min_instance_count = var.backend_min_instances
      max_instance_count = var.backend_max_instances
    }
    
    vpc_access {
      connector = google_vpc_access_connector.connector.id
    }
    
    containers {
      image = var.backend_image
      
      resources {
        limits = {
          cpu    = var.backend_cpu
          memory = var.backend_memory
        }
      }
      
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      
      env {
        name = "OPENAI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.openai_api_key.secret_id
            version = "latest"
          }
        }
      }
      
      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.database_url.secret_id
            version = "latest"
          }
        }
      }
      
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      
      ports {
        container_port = 8000
      }
    }
  }
  
  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }
  
  depends_on = [
    google_project_service.services,
    google_secret_manager_secret_version.openai_api_key
  ]
}

# Allow public access to backend
resource "google_cloud_run_v2_service_iam_binding" "backend_public" {
  location = google_cloud_run_v2_service.backend.location
  name     = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  members  = ["allUsers"]
}

# Alerting policies
resource "google_monitoring_alert_policy" "high_error_rate" {
  display_name = "High Error Rate - Sales Order System"
  combiner     = "OR"
  
  conditions {
    display_name = "Cloud Run Error Rate > 5%"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.05
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.email.name]
  
  alert_strategy {
    auto_close = "1800s"
  }
}

resource "google_monitoring_alert_policy" "high_latency" {
  display_name = "High Latency - Sales Order System"
  combiner     = "OR"
  
  conditions {
    display_name = "Cloud Run Request Latency > 5s"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 5000
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.email.name]
  
  alert_strategy {
    auto_close = "1800s"
  }
}
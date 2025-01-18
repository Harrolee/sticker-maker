terraform {
  required_version = "~> 1.3"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
}

provider "google" {
  project     = var.project_id
  region      = var.gcp_region
  credentials = file(var.credentials_file)
}

# Artifact Registry Repository
resource "google_artifact_registry_repository" "docker_repo" {
  location      = var.gcp_region
  repository_id = "sticker-maker-repo"
  description   = "Docker repository for sticker maker images"
  format        = "DOCKER"
}

# Cloud Function for webhooks
resource "google_storage_bucket" "function_bucket" {
  name     = "webhook-function-source-${random_id.bucket_suffix.hex}"
  location = var.gcp_region
}

# Create a service account for Cloud Function
resource "google_service_account" "function_sa" {
  account_id   = "webhook-function-sa"
  display_name = "Webhook Function Service Account"
}

# Grant necessary permissions to the function service account
resource "google_project_iam_member" "function_sql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.function_sa.email}"
}

# Add this data block to create the zip file
data "archive_file" "function_source" {
  type        = "zip"
  output_path = "${path.module}/function-source.zip"
  source_dir  = "${path.module}/../cloud_functions/process_sale"  # Adjust this path to your function's source directory
}

# Add this resource to upload the zip file
resource "google_storage_bucket_object" "function_source" {
  name   = "function-source-${data.archive_file.function_source.output_md5}.zip"
  bucket = google_storage_bucket.function_bucket.name
  source = data.archive_file.function_source.output_path
}

# Update the Cloud Function resource to use the uploaded file
resource "google_cloudfunctions2_function" "webhook_function" {
  name        = "webhook-function"
  description = "My webhook function"
  location    = var.gcp_region

  build_config {
    runtime     = "python312"
    entry_point = "process_sale"
    source {
      storage_source {
        bucket = google_storage_bucket.function_bucket.name
        object = google_storage_bucket_object.function_source.name  # Reference the uploaded file
      }
    }
  }

  service_config {
    max_instance_count    = 100
    available_memory     = "256M"
    timeout_seconds     = 300
    service_account_email = google_service_account.function_sa.email
    environment_variables = {
      LOG_EXECUTION_ID           = "true"
      INSTANCE_CONNECTION_NAME   = "${var.project_id}:${var.gcp_region}:sticker-maker"
      DB_USER                   = "postgres"
      DB_NAME                   = "postgres"
      GOOGLE_FUNCTION_SOURCE    = "process_sale.py" 
    }
    secret_environment_variables {
      key        = "DB_PASS"
      project_id = var.project_id
      secret     = "DB_PASS"
      version    = "latest"
    }
  }
}

# Allow public access to the function
resource "google_cloudfunctions2_function_iam_member" "webhook_invoker" {
  project        = var.project_id
  location       = var.gcp_region
  cloud_function = google_cloudfunctions2_function.webhook_function.name
  role           = "roles/cloudfunctions.invoker"
  member         = "allUsers"
}

# Update existing Cloud SQL instance with better security and variables
resource "google_sql_database_instance" "postgres_instance" {
  name             = "sticker-maker-db"
  database_version = "POSTGRES_17"
  region           = var.gcp_region
  depends_on       = [google_service_networking_connection.private_vpc_connection]

  settings {
    tier = var.database_tier
    
    ip_configuration {
      ipv4_enabled    = false  # Disable public IP
      private_network = google_compute_network.vpc.id
      require_ssl     = true   # Require SSL connections
    }

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true  # Enable point-in-time recovery
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = 7
        retention_unit   = "COUNT"
      }
    }

    database_flags {
      name  = "log_checkpoints"
      value = "on"
    }

    database_flags {
      name  = "log_connections"
      value = "on"
    }

    database_flags {
      name  = "log_disconnections"
      value = "on"
    }

    insights_config {
      query_insights_enabled  = true
      query_string_length    = 1024
      record_application_tags = true
      record_client_address  = true
    }
  }

  deletion_protection = true
}

resource "google_sql_database" "postgres_db" {
  name     = "mydatabase"
  instance = google_sql_database_instance.postgres_instance.name
}

resource "google_sql_user" "postgres_user" {
  name     = "myuser"
  instance = google_sql_database_instance.postgres_instance.name
  password = "mypassword"  # Use a secure method to handle passwords in production
}

# Cloud Storage Bucket
resource "google_storage_bucket" "bucket" {
  name     = "sticker-maker-storage-${random_id.bucket_suffix.hex}"
  location = var.gcp_region
  
  uniform_bucket_level_access = true
  
  cors {
    origin          = [var.allowed_origins]
    method          = ["GET", "HEAD", "PUT", "POST", "DELETE"]
    response_header = ["*"]
    max_age_seconds = 3600
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 365
    }
  }
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# Cloud Run Service
resource "google_cloud_run_service" "cloudrun_service" {
  name     = "sticker-maker-fasthtml"
  location = var.gcp_region

  template {
    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale"        = "1"
        "run.googleapis.com/cloudsql-instances"    = "${var.project_id}:${var.gcp_region}:sticker-maker"
        "run.googleapis.com/execution-environment" = "gen2"
        "run.googleapis.com/startup-cpu-boost"     = "true"
        "run.googleapis.com/security-posture"      = "enhanced"
        "run.googleapis.com/vpc-access-connector"  = google_vpc_access_connector.connector.id
        "run.googleapis.com/vpc-access-egress"     = "private-ranges-only"
        "run.googleapis.com/cloudsql-instances"     = google_sql_database_instance.postgres_instance.connection_name
        "run.googleapis.com/container-health-checks" = "true"
      }
      labels = {
        "managed-by" = "github-actions"
      }
    }

    spec {
      container_concurrency = 80
      timeout_seconds      = 300
      service_account_name = "${var.project_number}-compute@developer.gserviceaccount.com"

      containers {
        image = var.cloud_run_image
        
        ports {
          name           = "http1"
          container_port = 5001
        }

        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }

        # Add volume mounts for environment files
        volume_mounts {
          name       = "app_env"
          mount_path = "/code/env"
        }

        startup_probe {
          tcp_socket {
            port = 5001
          }
          timeout_seconds     = 240
          period_seconds     = 240
          failure_threshold = 1
        }
      }

      # Define volumes for secrets
      volumes {
        name = "app_env"
        secret {
          secret_name = "app_env"
          items {
            key  = "latest"
            path = ".env"
          }
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

# Add IAM for public access
resource "google_cloud_run_service_iam_member" "cloudrun_invoker" {
  service  = google_cloud_run_service.cloudrun_service.name
  location = google_cloud_run_service.cloudrun_service.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Create a service account for Cloud Run
resource "google_service_account" "cloudrun_sa" {
  account_id   = "cloudrun-service-account"
  display_name = "Cloud Run Service Account"
}

# Grant necessary permissions to the service account
resource "google_project_iam_member" "cloudrun_sql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

resource "google_project_iam_member" "cloudrun_storage" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

# Create a secret for database password
resource "google_secret_manager_secret" "db_password" {
  secret_id = "db-password"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "db_password" {
  secret = google_secret_manager_secret.db_password.id
  secret_data = var.database_password
}

// Ensure the .env file is included in the secret manager and mounted correctly in the Cloud Run service
resource "google_secret_manager_secret" "app_env" {
  secret_id = "app_env"
  
  replication {
    auto {}
  }
}

locals {
  env_content = <<EOT
SELL_APP_TOKEN=${var.sell_app_token}
REPLICATE_API_TOKEN=${var.replicate_api_token}
REPLICATE_MODEL_HASH=${var.replicate_model_hash}
IS_LOCAL=false
SENDER_EMAIL=${var.sender_email}
SENDER_EMAIL_PASSWORD=${var.sender_email_password}
SUPPLIER_EMAIL=${var.supplier_email}
SUPPORT_EMAIL=${var.support_email}
INSTANCE_CONNECTION_NAME=${var.project_id}:${var.gcp_region}:sticker-maker-db
DB_USER=postgres
DB_NAME=postgres
DB_PASS=${var.database_password}
SMTP_HOST=${var.smtp_host}
SMTP_PORT=${var.smtp_port}
EOT
}

resource "google_secret_manager_secret_version" "app_env" {
  secret = google_secret_manager_secret.app_env.id
  secret_data = local.env_content
}

// VPC network for private services
resource "google_compute_network" "vpc" {
  name                    = "sticker-maker-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet" {
  name          = "sticker-maker-subnet"
  ip_cidr_range = "10.0.0.0/24"
  network       = google_compute_network.vpc.id
  region        = var.gcp_region

  private_ip_google_access = true
}

# VPC connector for Cloud Run
resource "google_vpc_access_connector" "connector" {
  name          = "vpc-connector"
  ip_cidr_range = "10.8.0.0/28"
  network       = google_compute_network.vpc.name
  region        = var.gcp_region
}

# Outputs
output "cloudsql_instance_connection_name" {
  value = google_sql_database_instance.postgres_instance.connection_name
}

output "bucket_name" {
  value = google_storage_bucket.bucket.name
}

output "cloud_run_url" {
  value = google_cloud_run_service.cloudrun_service.status[0].url
}

output "artifact_registry_repository" {
  value = google_artifact_registry_repository.docker_repo.name
}

output "webhook_function_url" {
  value = google_cloudfunctions2_function.webhook_function.url
}

output "service_account_email" {
  value = google_service_account.cloudrun_sa.email
}

# Create a monitoring alert policy for database CPU usage
resource "google_monitoring_alert_policy" "cpu_usage" {
  display_name = "High CPU Usage Alert"
  combiner     = "OR"

  conditions {
    display_name = "CPU Usage > 80%"
    condition_threshold {
      filter          = "resource.type = \"cloudsql_database\" AND resource.labels.database_id = \"${google_sql_database_instance.postgres_instance.name}\" AND metric.type = \"cloudsql.googleapis.com/database/cpu/utilization\""
      duration        = "300s"
      comparison     = "COMPARISON_GT"
      threshold_value = 0.8
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.id]
}

# Create a monitoring notification channel
resource "google_monitoring_notification_channel" "email" {
  display_name = "Email Notification Channel"
  type         = "email"
  labels = {
    email_address = var.alert_email_address
  }
}

# Add logging configuration for Cloud Run
resource "google_project_iam_audit_config" "audit_logs" {
  project = var.project_id
  service = "run.googleapis.com"

  audit_log_config {
    log_type = "DATA_READ"
  }
  audit_log_config {
    log_type = "DATA_WRITE"
  }
  audit_log_config {
    log_type = "ADMIN_READ"
  }
}

# Add security policy for Cloud Run
resource "google_cloud_run_service_iam_policy" "noauth" {
  location = google_cloud_run_service.cloudrun_service.location
  project  = google_cloud_run_service.cloudrun_service.project
  service  = google_cloud_run_service.cloudrun_service.name

  policy_data = jsonencode({
    bindings = [
      {
        role    = "roles/run.invoker"
        members = var.allowed_cloud_run_invokers
      }
    ]
  })
}

# Grant necessary permissions to Terraform service account
resource "google_project_iam_member" "terraform_editor" {
  project = var.project_id
  role    = "roles/editor"
  member  = "serviceAccount:terraform-deployer@${var.project_id}.iam.gserviceaccount.com"
}

resource "google_project_iam_member" "terraform_security_admin" {
  project = var.project_id
  role    = "roles/iam.securityAdmin"
  member  = "serviceAccount:terraform-deployer@${var.project_id}.iam.gserviceaccount.com"
}

resource "google_project_iam_member" "terraform_service_networking_admin" {
  project = var.project_id
  role    = "roles/servicenetworking.networksAdmin"
  member  = "serviceAccount:terraform-deployer@${var.project_id}.iam.gserviceaccount.com"
}

resource "google_project_iam_member" "terraform_service_networking_agent" {
  project = var.project_id
  role    = "roles/servicenetworking.serviceAgent"
  member  = "serviceAccount:service-${var.project_number}@service-networking.iam.gserviceaccount.com"
}

resource "google_project_iam_binding" "secret_manager_permissions" {
  project = var.project_id
  role    = "roles/secretmanager.admin"
  members = [
    "serviceAccount:terraform-deployer@${var.project_id}.iam.gserviceaccount.com",
    "serviceAccount:${google_service_account.cloudrun_sa.email}",
    "serviceAccount:${google_service_account.function_sa.email}"
  ]
}

resource "google_project_iam_binding" "secret_manager_viewer" {
  project = var.project_id
  role    = "roles/secretmanager.viewer"
  members = [
    "serviceAccount:terraform-deployer@${var.project_id}.iam.gserviceaccount.com",
    "serviceAccount:${google_service_account.cloudrun_sa.email}",
    "serviceAccount:${google_service_account.function_sa.email}"
  ]
}

resource "google_project_iam_binding" "secret_manager_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  members = [
    "serviceAccount:terraform-deployer@${var.project_id}.iam.gserviceaccount.com",
    "serviceAccount:${google_service_account.cloudrun_sa.email}",
    "serviceAccount:${google_service_account.function_sa.email}",
    "serviceAccount:${var.project_number}-compute@developer.gserviceaccount.com"  // Add this line
  ]
}

// Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "servicenetworking.googleapis.com",
    "vpcaccess.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudfunctions.googleapis.com",
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "artifactregistry.googleapis.com"
  ])

  project = var.project_id
  service = each.value

  disable_dependent_services = true
  disable_on_destroy        = false
}

# Configure private service networking for Cloud SQL
resource "google_compute_global_address" "private_ip_address" {
  name          = "google-managed-services-range"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]

  depends_on = [google_project_service.required_apis]
}
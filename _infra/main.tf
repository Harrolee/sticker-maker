terraform {
  required_version = "~> 1.3"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.42.0"
    }
  }
}

locals {
  region = "310753928788.dkr.ecr.us-east-2.amazonaws.com/drive-gooder-final:latest"
  container_name = "drive-gooder-container"
  domain_name = "drive-gooder.com"
  secret_arn = "arn:aws:secretsmanager:us-east-2:310753928788:secret:drive-gooder-secrets-5lmhvt"

  container_port_https = 3000
}


provider "google" {
  project = "sticker-maker-439910"
  region      = "<your-region>"
  credentials = file("<path-to-your-service-account-key>.json")
}

# Cloud SQL PostgreSQL Instance
resource "google_sql_database_instance" "postgres_instance" {
  name             = "my-postgres-instance"
  database_version = "POSTGRES_13"
  region           = "<your-region>"

  settings {
    tier = "db-f1-micro"  # Change tier based on your needs

    backup_configuration {
      enabled = true
    }
  }
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
  name     = "my-storage-bucket-${random_id.bucket_suffix.hex}"
  location = "US"

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
  name     = "my-cloud-run-service"
  location = "<your-region>"

  template {
    spec {
      containers {
        image = "gcr.io/<your-project-id>/my-app-image:latest"
        resources {
          limits = {
            memory = "512Mi"
            cpu    = "1"
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

# Cloud Run IAM policy to allow public access
resource "google_cloud_run_service_iam_member" "cloudrun_invoker" {
  service = google_cloud_run_service.cloudrun_service.name
  location = google_cloud_run_service.cloudrun_service.location
  role    = "roles/run.invoker"
  member  = "allUsers"
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
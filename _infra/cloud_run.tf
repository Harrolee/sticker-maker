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
      service_account_name = google_service_account.cloudrun_sa.email

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

        env {
          name  = "SELL_APP_TOKEN"
          value = var.sell_app_token
        }
        env {
          name  = "REPLICATE_API_TOKEN"
          value = var.replicate_api_token
        }
        env {
          name  = "REPLICATE_MODEL_HASH"
          value = var.replicate_model_hash
        }
        env {
          name  = "IS_LOCAL"
          value = var.is_local
        }
        env {
          name  = "SENDER_EMAIL"
          value = var.sender_email
        }
        env {
          name  = "SUPPLIER_EMAIL"
          value = var.supplier_email
        }
        env {
          name  = "SUPPORT_EMAIL"
          value = var.support_email
        }
        env {
          name  = "INSTANCE_CONNECTION_NAME"
          value = "${var.project_id}:${var.gcp_region}:sticker-maker-db"
        }
        env {
          name  = "DB_USER"
          value = "postgres"
        }
        env {
          name  = "DB_NAME"
          value = "postgres"
        }
        env {
          name  = "SMTP_HOST"
          value = var.smtp_host
        }
        env {
          name  = "SMTP_PORT"
          value = var.smtp_port
        }

        # Sensitive environment variables using secrets
        env {
          name = "DB_PASS"
          value_from {
            secret_key_ref {
              name = "db-password"
              key  = "latest"
            }
          }
        }
        env {
          name = "SENDER_EMAIL_PASSWORD"
          value_from {
            secret_key_ref {
              name = "sender-email-password"
              key  = "latest"
            }
          }
        }

        startup_probe {
          tcp_socket {
            port = 5001
          }
          timeout_seconds     = 240
          period_seconds     = 240
          failure_threshold = 1
        }

        env {
          name  = "REPLICATE_CARTOONIZE_MODEL_HASH"
          value = var.replicate_cartoonize_model_hash
        }
        env {
          name  = "REPLICATE_RM_BACKGROUND_MODEL_HASH"
          value = var.replicate_rm_background_model_hash
        }
        env {
          name  = "SELL_APP_STOREFRONT_NAME"
          value = var.sell_app_storefront_name
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

resource "google_cloud_run_service_iam_member" "cloudrun_invoker" {
  service  = google_cloud_run_service.cloudrun_service.name
  location = google_cloud_run_service.cloudrun_service.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_service_account" "cloudrun_sa" {
  account_id   = "cloudrun-service-account"
  display_name = "Cloud Run Service Account"
}

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

resource "google_project_iam_member" "cloudrun_secrets" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.cloudrun_sa.email}"
} 
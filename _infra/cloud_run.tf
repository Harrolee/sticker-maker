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
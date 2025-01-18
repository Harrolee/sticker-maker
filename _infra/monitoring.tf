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

resource "google_monitoring_notification_channel" "email" {
  display_name = "Email Notification Channel"
  type         = "email"
  labels = {
    email_address = var.alert_email_address
  }
}

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
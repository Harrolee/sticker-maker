resource "google_sql_database_instance" "postgres_instance" {
  name             = "sticker-maker-db"
  database_version = "POSTGRES_17"
  region           = var.gcp_region
  depends_on       = [google_service_networking_connection.private_vpc_connection]

  settings {
    tier = var.database_tier
    
    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
      require_ssl     = true
    }

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
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
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
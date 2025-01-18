resource "google_storage_bucket" "function_bucket" {
  name     = "webhook-function-source-${random_id.bucket_suffix.hex}"
  location = var.gcp_region
}

resource "google_service_account" "function_sa" {
  account_id   = "webhook-function-sa"
  display_name = "Webhook Function Service Account"
}

resource "google_project_iam_member" "function_sql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.function_sa.email}"
}

data "archive_file" "function_source" {
  type        = "zip"
  output_path = "${path.module}/function-source.zip"
  source_dir  = "${path.module}/../cloud_functions/process_sale"
}

resource "google_storage_bucket_object" "function_source" {
  name   = "function-source-${data.archive_file.function_source.output_md5}.zip"
  bucket = google_storage_bucket.function_bucket.name
  source = data.archive_file.function_source.output_path
}

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
        object = google_storage_bucket_object.function_source.name
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
      IS_LOCAL                  = var.is_local
      MJ_APIKEY_PUBLIC         = var.mailjet_api_key_public
      SMTP_HOST                = var.smtp_host
      SMTP_PORT                = var.smtp_port
      SENDER_EMAIL             = var.sender_email
      SUPPLIER_EMAIL           = var.supplier_email
      SUPPORT_EMAIL            = var.support_email
    }

    # Sensitive environment variables using secrets
    secret_environment_variables {
      key        = "DB_PASS"
      project_id = var.project_id
      secret     = "db-password"
      version    = "latest"
    }
    secret_environment_variables {
      key        = "MJ_APIKEY_PRIVATE"
      project_id = var.project_id
      secret     = "mailjet-api-key-private"
      version    = "latest"
    }
    secret_environment_variables {
      key        = "SENDER_EMAIL_PASSWORD"
      project_id = var.project_id
      secret     = "sender-email-password"
      version    = "latest"
    }
  }
}

resource "google_cloudfunctions2_function_iam_member" "webhook_invoker" {
  project        = var.project_id
  location       = var.gcp_region
  cloud_function = google_cloudfunctions2_function.webhook_function.name
  role           = "roles/cloudfunctions.invoker"
  member         = "allUsers"
}

# Add Secret Manager access for the Cloud Function service account
resource "google_project_iam_member" "function_secrets" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.function_sa.email}"
} 
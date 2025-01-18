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
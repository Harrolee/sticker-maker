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
    "serviceAccount:${var.project_number}-compute@developer.gserviceaccount.com"
  ]
} 
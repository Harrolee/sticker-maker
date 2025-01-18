# Enable required APIs
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

# Artifact Registry Repository
resource "google_artifact_registry_repository" "docker_repo" {
  location      = var.gcp_region
  repository_id = "sticker-maker-repo"
  description   = "Docker repository for sticker maker images"
  format        = "DOCKER"
}
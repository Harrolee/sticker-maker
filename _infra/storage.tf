resource "google_storage_bucket" "bucket" {
  name     = "sticker-maker-storage-${random_id.bucket_suffix.hex}"
  location = var.gcp_region
  
  uniform_bucket_level_access = true
  
  cors {
    origin          = [var.allowed_origins]
    method          = ["GET", "HEAD", "PUT", "POST", "DELETE"]
    response_header = ["*"]
    max_age_seconds = 3600
  }

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
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

resource "google_secret_manager_secret" "sender_email_password" {
  secret_id = "sender-email-password"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "sender_email_password" {
  secret = google_secret_manager_secret.sender_email_password.id
  secret_data = var.sender_email_password
}

resource "google_secret_manager_secret" "mailjet_api_key_private" {
  secret_id = "mailjet-api-key-private"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "mailjet_api_key_private" {
  secret = google_secret_manager_secret.mailjet_api_key_private.id
  secret_data = var.mailjet_api_key_private
} 
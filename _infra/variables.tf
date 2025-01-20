variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "gcp_region" {
  description = "The GCP region to deploy resources"
  type        = string
  default     = "us-central1"
}

variable "credentials_file" {
  description = "Path to the GCP service account credentials file"
  type        = string
}

variable "database_tier" {
  description = "The machine type to use for the database"
  type        = string
  default     = "db-f1-micro"
}

variable "cloud_run_image" {
  description = "The Docker image to deploy to Cloud Run"
  type        = string
}

variable "database_password" {
  description = "Password for the database user"
  type        = string
  sensitive   = true
}

variable "allowed_origins" {
  description = "Allowed origins for CORS"
  type        = string
  default     = "*"  # Replace with specific domains in production
}

variable "project_number" {
  description = "The GCP project number"
  type        = string
}

variable "alert_email_address" {
  description = "Email address for monitoring alerts"
  type        = string
}

variable "allowed_cloud_run_invokers" {
  description = "List of members allowed to invoke Cloud Run service"
  type        = list(string)
  default     = ["allUsers"]  # Consider restricting this in production
}

variable "sell_app_token" {
  description = "Token for Sell App integration"
  type        = string
  sensitive   = true
}

variable "replicate_api_token" {
  description = "API token for Replicate.ai"
  type        = string
  sensitive   = true
}

variable "sender_email" {
  description = "Email address used to send notifications"
  type        = string
}

variable "sender_email_password" {
  description = "Password for sender email"
  type        = string
  sensitive   = true
}

variable "supplier_email" {
  description = "Email address for supplier notifications"
  type        = string
}

variable "support_email" {
  description = "Email address for support inquiries"
  type        = string
}

variable "smtp_host" {
  description = "SMTP server host"
  type        = string
  default     = "smtp.gmail.com"
}

variable "smtp_port" {
  description = "SMTP server port"
  type        = string
  default     = "587"
}

variable "replicate_cartoonize_model_hash" {
  description = "Model hash for Replicate.ai cartoonize model"
  type        = string
}

variable "replicate_rm_background_model_hash" {
  description = "Model hash for Replicate.ai background removal model"
  type        = string
}

variable "sell_app_storefront_name" {
  description = "Name of the Sell App storefront"
  type        = string
}

variable "mailjet_api_key_public" {
  description = "Public API key for Mailjet"
  type        = string
}

variable "mailjet_api_key_private" {
  description = "Private API key for Mailjet"
  type        = string
  sensitive   = true
}

variable "is_local" {
  description = "Flag to indicate if running in local environment"
  type        = string
  default     = "false"
}
project_id       = "sticker-maker-439910"
gcp_region       = "us-central1"
credentials_file = "service-account-key.json"
database_tier    = "db-f1-micro"
cloud_run_image  = "us-central1-docker.pkg.dev/sticker-maker-439910/sticker-maker-repo/sticker-maker:latest"
database_password = "dopeStickerY0u78Know"
allowed_origins   = "https://your-domain.com"
project_number = "376442012597"

sell_app_token         = "your-sell-app-token"
replicate_api_token    = "your-replicate-api-token"
replicate_model_hash   = "your-replicate-model-hash"
sender_email          = "halzinnia@gmail.com"
sender_email_password = "your-sender-email-password"
supplier_email        = "halzinnia@gmail.com"
support_email         = "halzinnia@gmail.com"

alert_email_address = "halzinnia@gmail.com"
allowed_cloud_run_invokers = [
  "serviceAccount:your-service-account@your-project.iam.gserviceaccount.com",
  "user:halzinnia@gmail.com"
]

replicate_cartoonize_model_hash = "your-cartoonize-model-hash"
replicate_rm_background_model_hash = "your-rm-background-model-hash"
sell_app_storefront_name = "your-storefront-name"

mailjet_api_key_public = "your-mailjet-public-key"
mailjet_api_key_private = "your-mailjet-private-key"
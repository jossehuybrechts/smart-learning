terraform {
  backend "gcs" {
    bucket = "qwiklabs-gcp-03-3d4f5eb0f891-terraform-state"
    prefix = "prod"
  }
}

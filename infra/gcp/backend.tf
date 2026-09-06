terraform {
  backend "gcs" {
    prefix = "aiops-guardian/gke"
  }
}

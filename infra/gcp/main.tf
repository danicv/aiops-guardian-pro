locals {
  namespace = "aiops-guardian"
  required_apis = toset([
    "artifactregistry.googleapis.com",
    "compute.googleapis.com",
    "container.googleapis.com",
    "iamcredentials.googleapis.com",
    "secretmanager.googleapis.com",
    "sts.googleapis.com"
  ])
  secret_names       = toset(["database-password", "openai-api-key", "smtp-username", "smtp-password"])
  workload_principal = "principal://iam.googleapis.com/projects/${data.google_project.current.number}/locations/global/workloadIdentityPools/${var.project_id}.svc.id.goog/subject/ns/${local.namespace}/sa/guardian-backend"
  postgres_principal = "principal://iam.googleapis.com/projects/${data.google_project.current.number}/locations/global/workloadIdentityPools/${var.project_id}.svc.id.goog/subject/ns/${local.namespace}/sa/guardian-postgres"
}

resource "google_project_service" "apis" {
  for_each           = local.required_apis
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_compute_network" "main" {
  name                    = "aiops-guardian"
  auto_create_subnetworks = false
  depends_on              = [google_project_service.apis]
}

resource "google_compute_subnetwork" "main" {
  name          = "aiops-guardian-${var.region}"
  region        = var.region
  network       = google_compute_network.main.id
  ip_cidr_range = "10.10.0.0/20"
  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = "10.20.0.0/16"
  }
  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = "10.30.0.0/20"
  }
}

resource "google_artifact_registry_repository" "main" {
  location      = var.region
  repository_id = "aiops-guardian-pro"
  format        = "DOCKER"
  depends_on    = [google_project_service.apis]
}

resource "google_container_cluster" "main" {
  name                = var.cluster_name
  location            = var.region
  enable_autopilot    = true
  network             = google_compute_network.main.id
  subnetwork          = google_compute_subnetwork.main.id
  deletion_protection = false

  release_channel { channel = "REGULAR" }
  workload_identity_config { workload_pool = "${var.project_id}.svc.id.goog" }
  secret_manager_config { enabled = true }
  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret" "app" {
  for_each  = local.secret_names
  secret_id = each.value
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_iam_member" "backend" {
  for_each   = google_secret_manager_secret.app
  secret_id  = each.value.id
  role       = "roles/secretmanager.secretAccessor"
  member     = local.workload_principal
  depends_on = [google_container_cluster.main]
}

resource "google_secret_manager_secret_iam_member" "postgres" {
  secret_id  = google_secret_manager_secret.app["database-password"].id
  role       = "roles/secretmanager.secretAccessor"
  member     = local.postgres_principal
  depends_on = [google_container_cluster.main]
}

resource "helm_release" "guardian" {
  count            = var.deploy_workloads ? 1 : 0
  name             = "aiops-guardian"
  namespace        = local.namespace
  chart            = "${path.module}/../../deploy/helm/aiops-guardian"
  create_namespace = true
  # Kubernetes rollout checks and diagnostics are handled by GitHub Actions.
  # Waiting here hides pod events behind a generic Helm timeout.
  wait    = false
  timeout = 600
  values = [yamlencode({
    projectId = var.project_id
    images = {
      mcp      = var.mcp_image
      backend  = var.backend_image
      frontend = var.frontend_image
    }
  })]
  depends_on = [google_container_cluster.main, google_secret_manager_secret_iam_member.backend, google_secret_manager_secret_iam_member.postgres]
}

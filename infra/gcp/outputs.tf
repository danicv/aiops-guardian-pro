output "cluster_name" { value = google_container_cluster.main.name }
output "region" { value = var.region }
output "artifact_registry" { value = google_artifact_registry_repository.main.name }
output "secret_names" { value = sort(tolist(local.secret_names)) }

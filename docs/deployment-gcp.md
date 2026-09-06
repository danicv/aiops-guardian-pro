# GCP deployment: Terraform, GKE, and Secret Manager

The GitHub workflow provisions and deploys the complete application to a GKE Autopilot cluster in `us-east1`. Terraform owns the VPC, subnet, GKE cluster, Artifact Registry, Secret Manager containers, IAM access, and Helm release. The frontend and `/api` share one GKE ingress.

Secret values are never passed to Terraform or stored in GitHub. GKE Workload Identity and the managed Secret Manager CSI add-on mount them directly into the backend and PostgreSQL pods.

## 1. Bootstrap once

The bootstrap stack creates the remote Terraform-state bucket, GitHub Workload Identity Federation, and deployment service account. Run it from Google Cloud Shell as a project owner:

```bash
cd infra/gcp/bootstrap
gcloud auth application-default login
terraform init
terraform apply
```

Add the two Terraform output values as GitHub repository secrets under **Settings > Secrets and variables > Actions**:

- `GCP_SERVICE_ACCOUNT` = output `gcp_service_account`
- `GCP_WORKLOAD_IDENTITY_PROVIDER` = output `gcp_workload_identity_provider`

This bootstrap is necessarily performed before GitHub can authenticate; every deployment after it is managed by the pipeline.

## 2. Add secret versions

The main Terraform stack creates these Secret Manager secrets without payloads:

- `database-password`
- `openai-api-key`
- `smtp-username`
- `smtp-password`

After the first workflow infrastructure stage, add values without putting them in shell history:

```bash
read -s DB_PASSWORD
printf %s "$DB_PASSWORD" | gcloud secrets versions add database-password --data-file=-
unset DB_PASSWORD

read -s OPENAI_API_KEY
printf %s "$OPENAI_API_KEY" | gcloud secrets versions add openai-api-key --data-file=-
unset OPENAI_API_KEY
```

Repeat for `smtp-username` and `smtp-password`. The workflow checks that all four have an enabled `latest` version before deploying pods.

## 3. Deploy

Merge the pipeline branch into `main`, then either push to `main` or manually run **Terraform and deploy to GKE** from GitHub Actions.

The workflow:

1. Applies Terraform to create/update GCP infrastructure.
2. Builds and pushes three commit-addressed images to Artifact Registry.
3. Applies Terraform again with those image names; Terraform deploys the Helm release.
4. Waits for the MCP, backend, and frontend rollouts and reports the GKE ingress IP.

## Security and production notes

- Google Secret Manager is the GCP equivalent intended here by “Google Vault.”
- Secrets are mounted as read-only files and read at application startup. Rotate a secret by adding a new version and restarting the affected workload.
- Terraform state is versioned, private, and protected by uniform bucket-level access.
- The example runs PostgreSQL as a GKE StatefulSet with persistent disk. For a production HA deployment, migrate it to Cloud SQL for PostgreSQL.
- Add managed TLS/DNS and Cloud Armor before exposing a production installation publicly.

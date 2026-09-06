# Deploy to Google Cloud Run

The workflow at `.github/workflows/deploy-gcp.yml` deploys the frontend, backend, and MCP bridge to Cloud Run in `us-central1`. Container images are stored in Artifact Registry.

## One-time Google Cloud setup

Run these commands in Cloud Shell or in a terminal with the Google Cloud CLI. The setup uses Workload Identity Federation, so no service-account key is stored in GitHub.

```bash
export PROJECT_ID="project-bc255d91-89ae-4e6d-b82"
export PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
export GITHUB_REPOSITORY="danicv/aiops-guardian-pro"
export DEPLOYER_SERVICE_ACCOUNT="github-cloud-run-deployer"

gcloud config set project "$PROJECT_ID"

gcloud services enable \
  artifactregistry.googleapis.com \
  iamcredentials.googleapis.com \
  run.googleapis.com \
  sts.googleapis.com

gcloud artifacts repositories create aiops-guardian-pro \
  --repository-format=docker \
  --location=us-central1 \
  --description="AIOps Guardian Pro container images"

gcloud iam service-accounts create "$DEPLOYER_SERVICE_ACCOUNT" \
  --display-name="GitHub Cloud Run deployer"

for role in roles/artifactregistry.writer roles/run.admin roles/serviceusage.serviceUsageConsumer; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${DEPLOYER_SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="$role"
done

gcloud iam service-accounts add-iam-policy-binding \
  "${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --member="serviceAccount:${DEPLOYER_SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

gcloud iam workload-identity-pools create github \
  --location=global \
  --display-name="GitHub Actions"

gcloud iam workload-identity-pools providers create-oidc aiops-guardian-pro \
  --location=global \
  --workload-identity-pool=github \
  --display-name="AIOps Guardian Pro GitHub Actions" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository=='${GITHUB_REPOSITORY}'"

gcloud iam service-accounts add-iam-policy-binding \
  "${DEPLOYER_SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github/attribute.repository/${GITHUB_REPOSITORY}"
```

If the Artifact Registry repository or Workload Identity pool already exists, skip its create command.

## GitHub secrets

Add these repository secrets under **Settings > Secrets and variables > Actions**:

- `GCP_SERVICE_ACCOUNT`: `github-cloud-run-deployer@project-bc255d91-89ae-4e6d-b82.iam.gserviceaccount.com`
- `GCP_WORKLOAD_IDENTITY_PROVIDER`: obtain the exact value with:

```bash
gcloud iam workload-identity-pools providers describe aiops-guardian-pro \
  --project="project-bc255d91-89ae-4e6d-b82" \
  --location=global \
  --workload-identity-pool=github \
  --format='value(name)'
```

The provider value must start with `projects/` and use the numeric project number, not the project ID.

## Deploy

Push to `main`, or run **Deploy to Google Cloud Run** manually from the GitHub Actions tab.

## Data persistence

This initial deployment runs in demo mode and uses an ephemeral SQLite database. Cloud Run may discard that data whenever an instance restarts. For production, use Cloud SQL for PostgreSQL, store application secrets in Secret Manager, and make the MCP service private if it will perform real infrastructure actions.

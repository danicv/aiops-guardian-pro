#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCAL_ROOT="$ROOT/.local/langfuse"
REPO_DIR="$LOCAL_ROOT/source"
ENV_FILE="$LOCAL_ROOT/langfuse.env"
ACCESS_FILE="$LOCAL_ROOT/access.txt"
LANGFUSE_UI_URL="http://localhost:3000"
BACKEND_LANGFUSE_HOST="http://host.docker.internal:3000"

command -v docker >/dev/null || { echo 'Docker is required.' >&2; exit 1; }
command -v git >/dev/null || { echo 'Git is required.' >&2; exit 1; }
command -v kubectl >/dev/null || { echo 'kubectl is required.' >&2; exit 1; }
command -v kind >/dev/null || { echo 'kind is required for this local deployment.' >&2; exit 1; }
command -v openssl >/dev/null || { echo 'OpenSSL is required.' >&2; exit 1; }

mkdir -p "$LOCAL_ROOT"
if [[ ! -f "$REPO_DIR/docker-compose.yml" ]]; then
  git clone --depth 1 https://github.com/langfuse/langfuse.git "$REPO_DIR"
fi

if [[ ! -f "$ENV_FILE" ]]; then
  umask 077
  postgres_password="$(openssl rand -hex 24)"
  clickhouse_password="$(openssl rand -hex 24)"
  redis_password="$(openssl rand -hex 24)"
  minio_password="$(openssl rand -hex 24)"
  salt="$(openssl rand -hex 24)"
  encryption_key="$(openssl rand -hex 32)"
  nextauth_secret="$(openssl rand -hex 32)"
  project_public_key="pk-lf-$(openssl rand -hex 16)"
  project_secret_key="sk-lf-$(openssl rand -hex 32)"
  user_password="$(openssl rand -hex 24)"
  cat > "$ENV_FILE" <<EOF
NEXTAUTH_URL=$LANGFUSE_UI_URL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=$postgres_password
POSTGRES_DB=postgres
DATABASE_URL=postgresql://postgres:$postgres_password@postgres:5432/postgres
SALT=$salt
ENCRYPTION_KEY=$encryption_key
NEXTAUTH_SECRET=$nextauth_secret
TELEMETRY_ENABLED=false
CLICKHOUSE_USER=clickhouse
CLICKHOUSE_PASSWORD=$clickhouse_password
REDIS_AUTH=$redis_password
MINIO_ROOT_USER=minio
MINIO_ROOT_PASSWORD=$minio_password
LANGFUSE_S3_EVENT_UPLOAD_ACCESS_KEY_ID=minio
LANGFUSE_S3_EVENT_UPLOAD_SECRET_ACCESS_KEY=$minio_password
LANGFUSE_S3_MEDIA_UPLOAD_ACCESS_KEY_ID=minio
LANGFUSE_S3_MEDIA_UPLOAD_SECRET_ACCESS_KEY=$minio_password
LANGFUSE_S3_BATCH_EXPORT_ACCESS_KEY_ID=minio
LANGFUSE_S3_BATCH_EXPORT_SECRET_ACCESS_KEY=$minio_password
LANGFUSE_INIT_ORG_ID=guardian-org
LANGFUSE_INIT_ORG_NAME=AIOps-Guardian
LANGFUSE_INIT_PROJECT_ID=guardian
LANGFUSE_INIT_PROJECT_NAME=AIOps-Guardian
LANGFUSE_INIT_PROJECT_PUBLIC_KEY=$project_public_key
LANGFUSE_INIT_PROJECT_SECRET_KEY=$project_secret_key
LANGFUSE_INIT_USER_EMAIL=admin@guardian.local
LANGFUSE_INIT_USER_NAME=Guardian-Admin
LANGFUSE_INIT_USER_PASSWORD=$user_password
EOF
  cat > "$ACCESS_FILE" <<EOF
Langfuse URL: $LANGFUSE_UI_URL
Initial user: admin@guardian.local
Initial password: $user_password
Project public key: $project_public_key
Project secret key: $project_secret_key
EOF
  chmod 600 "$ENV_FILE" "$ACCESS_FILE"
fi

echo 'Starting official self-hosted Langfuse Compose stack...'
docker compose --project-name guardian-langfuse --env-file "$ENV_FILE" \
  -f "$REPO_DIR/docker-compose.yml" \
  -f "$ROOT/scripts/langfuse.local.compose.yaml" up -d --wait --wait-timeout 180

echo 'Downloading the local Qwen model (no provider API key required)...'
docker compose --project-name guardian-langfuse --env-file "$ENV_FILE" \
  -f "$REPO_DIR/docker-compose.yml" \
  -f "$ROOT/scripts/langfuse.local.compose.yaml" exec -T ollama ollama pull qwen2.5:1.5b

set -a
source "$ENV_FILE"
set +a
kubectl apply -f "$ROOT/k8s/local/namespace.yaml"
kubectl create secret generic guardian-langfuse -n aiops-guardian \
  --from-literal=LANGFUSE_ENABLED=true \
  --from-literal=LANGFUSE_HOST="$BACKEND_LANGFUSE_HOST" \
  --from-literal=LANGFUSE_PUBLIC_KEY="$LANGFUSE_INIT_PROJECT_PUBLIC_KEY" \
  --from-literal=LANGFUSE_SECRET_KEY="$LANGFUSE_INIT_PROJECT_SECRET_KEY" \
  --dry-run=client -o yaml | kubectl apply -f -

echo 'Building Northstar Supply demo checkout...'
docker build -t guardian-checkout:reports-v1 "$ROOT/demo/checkout-api"
kind load docker-image guardian-checkout:reports-v1 --name guardian-local

echo 'Building Guardian backend with local-model support...'
docker build -t guardian-backend:reports-v1 -f "$ROOT/backend/Dockerfile" "$ROOT"
kind load docker-image guardian-backend:reports-v1 --name guardian-local

kubectl apply -k "$ROOT/k8s"
kubectl rollout restart deployment/checkout-api -n aiops-guardian
kubectl rollout status deployment/checkout-api -n aiops-guardian --timeout=180s
kubectl rollout restart deployment/guardian-grafana -n aiops-guardian
kubectl rollout status deployment/guardian-grafana -n aiops-guardian --timeout=180s
kubectl rollout restart deployment/guardian-backend -n aiops-guardian
kubectl rollout status deployment/guardian-backend -n aiops-guardian --timeout=180s

echo 'Building Guardian UI with observability links...'
docker build --build-arg VITE_API_BASE_URL=http://localhost:30800 \
  --build-arg VITE_LANGFUSE_URL="$LANGFUSE_UI_URL" \
  --build-arg VITE_PROMETHEUS_URL=http://localhost:19090 \
  --build-arg VITE_GRAFANA_URL=http://localhost:3002/d/guardian-service-health/guardian-service-health \
  --build-arg VITE_CHECKOUT_DEMO_URL=http://localhost:18081 \
  -t guardian-frontend:reports-v1 "$ROOT/frontend"
kind load docker-image guardian-frontend:reports-v1 --name guardian-local
kubectl rollout restart deployment/guardian-frontend -n aiops-guardian
kubectl rollout status deployment/guardian-frontend -n aiops-guardian --timeout=180s

echo "Langfuse is starting at $LANGFUSE_UI_URL"
echo 'Start Grafana access with: kubectl port-forward -n aiops-guardian service/guardian-grafana 3002:3000'
echo 'Grafana local demo login: admin / guardian-local'
echo 'Start the sample store with: kubectl port-forward -n aiops-guardian service/checkout-api 18081:8080'
echo "Local initial access details are stored privately in: $ACCESS_FILE"
echo 'Guardian tracing is enabled and observability header links are configured.'

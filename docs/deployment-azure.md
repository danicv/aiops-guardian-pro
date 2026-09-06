# Deploying to Azure / AKS

## 1. Provision infrastructure

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan -out guardian.tfplan
terraform apply guardian.tfplan
```

## 2. Build and push containers

```bash
az acr login --name <acr>
docker build -f backend/Dockerfile -t <acr>.azurecr.io/guardian-backend:1.0.0 .
docker build -f mcp-server/Dockerfile -t <acr>.azurecr.io/guardian-mcp:1.0.0 .
docker build -t <acr>.azurecr.io/guardian-frontend:1.0.0 frontend

docker push <acr>.azurecr.io/guardian-backend:1.0.0
docker push <acr>.azurecr.io/guardian-mcp:1.0.0
docker push <acr>.azurecr.io/guardian-frontend:1.0.0
```

## 3. Identity and secrets
Use AKS Workload Identity, Kubernetes RBAC and Azure Key Vault. Separate read MCP and action MCP identities.

## 4. Deploy

Update ACR image names in `k8s/`, then:

```bash
kubectl apply -f k8s/namespaces.yaml
kubectl apply -f k8s/configmaps.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/mcp-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/ingress.yaml
```

For the capstone-specific separate PostgreSQL container:

```bash
kubectl apply -f k8s/postgres-demo.yaml
```

Production recommendation: Azure Database for PostgreSQL Flexible Server rather than the demo StatefulSet.

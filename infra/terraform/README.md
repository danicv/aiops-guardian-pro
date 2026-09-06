# Terraform Azure foundation

Provisions Resource Group, Log Analytics, VNet/subnet, AKS, ACR, user-assigned identity, Key Vault, Azure RBAC, namespaces and NGINX ingress/Standard Azure Load Balancer.

AKS VNet uses `10.50.0.0/16`; Kubernetes service CIDR uses `10.60.0.0/16` to avoid overlap.

```bash
az login
terraform init
terraform plan -out guardian.tfplan
terraform apply guardian.tfplan
```

Production extensions: private AKS, private ACR/Key Vault endpoints, Application Gateway/WAF if required, Azure Database for PostgreSQL Flexible Server, managed Prometheus/Grafana if preferred, DNS/cert automation and workload identity per service.

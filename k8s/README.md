# AKS / Kubernetes manifests

## Local cluster

Build the images from the repository root and load them into the local cluster:

```bash
docker build -t guardian-checkout:reports-v1 demo/checkout-api
docker build -t guardian-backend:reports-v1 -f backend/Dockerfile .
docker build -t guardian-mcp:local -f mcp-server/Dockerfile .
docker build --build-arg VITE_API_BASE_URL=http://localhost:30800 -t guardian-frontend:reports-v1 frontend
```

For kind, load the images before applying the overlay:

```bash
kind load docker-image --name guardian-local guardian-backend:reports-v1 guardian-mcp:local guardian-frontend:reports-v1 guardian-checkout:reports-v1
kubectl apply -k k8s
kubectl rollout status deployment/guardian-backend -n aiops-guardian
kubectl rollout status deployment/guardian-frontend -n aiops-guardian
kubectl rollout status deployment/checkout-api -n aiops-guardian
kubectl rollout status deployment/guardian-prometheus -n aiops-guardian
```

Open the UI at `http://localhost:30080`. The backend is available at
`http://localhost:30800/docs`. For Minikube, use `minikube image load` instead
of `kind load docker-image`. The local overlay uses demo PostgreSQL credentials
and NodePorts. Replace these with Kubernetes Secrets and an ingress before
moving to GCP.


## Live metrics in the local cluster

The local overlay installs checkout-api and Prometheus in `aiops-guardian` and
sets the backend's `PROMETHEUS_URL` to `http://guardian-prometheus:9090`.

Run `alembic upgrade head` as a release/init job against PostgreSQL before
scaling the backend. Application startup only auto-creates SQLite tables for
local tests and demo use.
Prometheus uses a 2Gi persistent volume claim with 24-hour retention for this
local setup.
Ask Guardian should use **Live Prometheus**, application `checkout-api`,
environment `prod`, and namespace `aiops-guardian`.

For kind clusters without host port mappings, keep these running in separate terminals:

```sh
kubectl --context kind-guardian-local -n aiops-guardian port-forward service/guardian-frontend 30081:80
kubectl --context kind-guardian-local -n aiops-guardian port-forward service/guardian-backend 30800:80
kubectl --context kind-guardian-local -n aiops-guardian port-forward service/checkout-api 18081:8080
```

Open `http://localhost:30081/ask`. Generate application traffic before investigating:

```sh
for i in $(seq 1 60); do curl -fsS http://localhost:18081/checkout >/dev/null; sleep 1; done
```

Restart port-forward commands after rolling their target pods. The frontend image
is built with `VITE_API_BASE_URL=http://localhost:30800`; local CORS allows both
`http://localhost:30080` and `http://localhost:30081`.
The `/release-risk` endpoint remains explicitly simulated; live investigations
currently analyze telemetry and do not validate release changes.

If kind reports a missing digest while importing a multi-platform Docker image,
export only the node's platform (use `linux/amd64` on Intel):

```sh
docker image save --platform linux/arm64 -o /tmp/guardian-local-images.tar guardian-backend:reports-v1 guardian-frontend:reports-v1 guardian-checkout:reports-v1
kind load image-archive --name guardian-local /tmp/guardian-local-images.tar
```

With the three port forwards above active, run the deployment smoke test using
an environment with the backend dependencies installed:

```sh
python scripts/verify_local_cluster.py
```

This generates 35 seconds of checkout traffic and creates two read-only local
investigations to check metrics, persistence, and unknown-data handling. It also
checks the delivered frontend bundle and CORS, but does not automate a browser click.

## Graphical reports and logs

The local overlay also deploys an ephemeral `guardian-loki` service. Activate the
Prometheus and Loki URLs in the Integration Hub, then open `/reports`.
See [live integration setup and the controlled traffic scenario](../docs/live-integrations.md).
The checkout fault parameters are enabled only in this local demo overlay.

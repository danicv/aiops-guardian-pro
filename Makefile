.PHONY: up down backend frontend test validate migrate local-build local-deploy langfuse-up evidence evidence-offline
up:
	docker compose up --build
down:
	docker compose down -v
backend:
	PYTHONPATH=backend uvicorn app.main:app --reload --port 8000
frontend:
	cd frontend && npm run dev
test:
	PYTHONPATH=backend pytest -q backend/tests
validate:
	python scripts/validate_project.py
migrate:
	DATABASE_URL=$${DATABASE_URL:-sqlite:///./guardian.db} alembic upgrade head
local-build:
	docker build -t guardian-checkout:reports-v1 demo/checkout-api
	docker build -t guardian-backend:reports-v1 -f backend/Dockerfile .
	docker build -t guardian-mcp:local -f mcp-server/Dockerfile .
	docker build --build-arg VITE_API_BASE_URL=http://localhost:30800 --build-arg VITE_LANGFUSE_URL=http://localhost:3000 --build-arg VITE_PROMETHEUS_URL=http://localhost:19090 --build-arg VITE_GRAFANA_URL=http://localhost:3002/d/guardian-service-health/guardian-service-health --build-arg VITE_CHECKOUT_DEMO_URL=http://localhost:18081 -t guardian-frontend:reports-v1 frontend
langfuse-up:
	bash scripts/start_langfuse_local.sh
local-deploy:
	kubectl apply -k k8s
	kubectl rollout restart deployment/guardian-backend -n aiops-guardian
	kubectl rollout restart deployment/guardian-frontend -n aiops-guardian
	kubectl rollout restart deployment/guardian-mcp -n aiops-guardian
	kubectl rollout restart deployment/checkout-api -n aiops-guardian
	kubectl rollout restart deployment/guardian-grafana -n aiops-guardian
	kubectl rollout status deployment/guardian-backend -n aiops-guardian
	kubectl rollout status deployment/guardian-frontend -n aiops-guardian
	kubectl rollout status deployment/guardian-mcp -n aiops-guardian
	kubectl rollout status deployment/checkout-api -n aiops-guardian
	kubectl rollout status deployment/guardian-grafana -n aiops-guardian
	kubectl rollout status statefulset/postgres -n aiops-guardian
evidence:
	python3 scripts/capstone_evidence.py demo
	python3 scripts/capstone_evidence.py proof
	python3 scripts/capstone_evidence.py safety
	python3 scripts/capstone_evidence.py prompts
evidence-offline:
	python3 scripts/baseline_agent.py --sample-run
	PYTHONPATH=backend python3 scripts/capstone_offline_evidence.py retrieval
	PYTHONPATH=backend python3 scripts/capstone_offline_evidence.py adaptation
	PYTHONPATH=backend python3 scripts/capstone_offline_evidence.py privacy

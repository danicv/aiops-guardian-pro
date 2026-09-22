.PHONY: up down backend frontend test validate migrate local-build local-deploy
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
	docker build --build-arg VITE_API_BASE_URL=http://localhost:30800 -t guardian-frontend:reports-v1 frontend
local-deploy:
	kubectl apply -k k8s
	kubectl rollout restart deployment/guardian-backend -n aiops-guardian
	kubectl rollout restart deployment/guardian-frontend -n aiops-guardian
	kubectl rollout restart deployment/guardian-mcp -n aiops-guardian
	kubectl rollout status deployment/guardian-backend -n aiops-guardian
	kubectl rollout status deployment/guardian-frontend -n aiops-guardian
	kubectl rollout status deployment/guardian-mcp -n aiops-guardian
	kubectl rollout status statefulset/postgres -n aiops-guardian

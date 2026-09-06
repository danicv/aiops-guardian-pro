.PHONY: up down backend frontend test validate
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

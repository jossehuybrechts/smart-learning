install:
	@command -v uv >/dev/null 2>&1 || { echo "uv is not installed. Installing uv..."; curl -LsSf https://astral.sh/uv/0.6.12/install.sh | sh; source ~/.bashrc; }
	uv sync --dev --extra jupyter --frozen


test:
	uv run pytest tests/unit && uv run pytest tests/integration

playground_adk:
	@echo "\033[1;32m===============================================================================\033[0m"
	@echo "\033[1;32m| Starting ADK Web Server via 'adk web' command.                              |\033[0m"
	@echo "\033[1;32m|                                                                             |\033[0m"
	@echo "\033[1;32m| IMPORTANT: Select the 'app' folder to interact with your agent.             |\033[0m"
	@echo "\033[1;32m===============================================================================\033[0m"
	uv run adk web --port 8501

playground:
	PYTHONPATH=. uv run streamlit run frontend/streamlit_app.py --browser.serverAddress=localhost --server.enableCORS=false --server.enableXsrfProtection=false

backend:
	# Export dependencies to requirements file using uv export.
	uv export --no-hashes --no-sources --no-header --no-dev --no-emit-project --no-annotate --frozen > .requirements.txt 2>/dev/null || \
	uv export --no-hashes --no-sources --no-header --no-dev --no-emit-project --frozen > .requirements.txt && uv run app/agent_engine_app.py

setup-dev-env:
	PROJECT_ID=$$(gcloud config get-value project) && \
	(cd deployment/terraform/dev && terraform init && terraform apply --var-file vars/env.tfvars --var dev_project_id=$$PROJECT_ID --auto-approve)

lint:
	uv run codespell
	uv run ruff check . --diff
	uv run ruff format . --check --diff
	uv run mypy .

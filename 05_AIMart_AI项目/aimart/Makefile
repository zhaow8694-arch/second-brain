.PHONY: dev build up down test lint migrate seed clean

# ---- Configuration ---------------------------------------------------------
PYTHON     ?= python
PIP        ?= pip
DOCKER     ?= docker
DOCKER_COMPOSE ?= docker compose

# ---- Development -----------------------------------------------------------

dev: ## Install the project in editable mode with dev dependencies
	$(PIP) install -e ".[dev]"
	pre-commit install 2>/dev/null || true

# ---- Build -----------------------------------------------------------------

build: ## Build the Docker image
	$(DOCKER) build -t aimart:latest .

# ---- Docker Compose --------------------------------------------------------

up: ## Start all services (detached)
	$(DOCKER_COMPOSE) up -d

down: ## Stop and remove all containers
	$(DOCKER_COMPOSE) down

# ---- Testing & Linting -----------------------------------------------------

test: ## Run the test suite
	$(PYTHON) -m pytest tests/ -v --cov=aimart --cov-report=term-missing

lint: ## Run ruff + mypy
	ruff check src/ tests/
	mypy src/aimart

# ---- Database --------------------------------------------------------------

migrate: ## Run Alembic migrations
	$(PYTHON) -m alembic upgrade head

seed: ## Seed the database with sample data
	$(PYTHON) -m aimart.scripts.seed 2>/dev/null || echo "Seed script not found – skipping"

# ---- Cleanup ---------------------------------------------------------------

clean: ## Remove build artifacts, caches, and temp files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .ruff_cache/

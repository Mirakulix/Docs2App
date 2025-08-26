# Makefile for Docs2App
# Works with both 'docker compose' and 'docker-compose'

# Detect Docker Compose command
DOCKER_COMPOSE := $(shell if command -v docker-compose >/dev/null 2>&1; then echo "docker-compose"; else echo "docker compose"; fi)

.PHONY: help build up down logs shell clean test health analyze batch

# Default target
help: ## Show this help message
	@echo "Docs2App - AI-powered document analysis and code generation"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Build all Docker images
	$(DOCKER_COMPOSE) build

up: ## Start all services
	$(DOCKER_COMPOSE) up -d
	@echo "Services started. Waiting for Ollama to be ready..."
	@sleep 20
	@echo "✅ All services are running!"
	@echo "📊 Check status: make status"
	@echo "🔧 Enter shell: make shell"

up-full: ## Start all services including optional ones (Redis, PostgreSQL)
	$(DOCKER_COMPOSE) --profile full up -d

down: ## Stop all services
	$(DOCKER_COMPOSE) down

stop: ## Stop services without removing containers
	$(DOCKER_COMPOSE) stop

restart: ## Restart all services
	$(DOCKER_COMPOSE) restart

logs: ## View logs from all services
	$(DOCKER_COMPOSE) logs -f

logs-app: ## View logs from docs2app service only
	$(DOCKER_COMPOSE) logs -f docs2app

logs-ollama: ## View logs from Ollama service only
	$(DOCKER_COMPOSE) logs -f ollama

status: ## Show status of all services
	$(DOCKER_COMPOSE) ps

shell: ## Enter interactive shell in docs2app container
	$(DOCKER_COMPOSE) exec docs2app /bin/bash

health: ## Run health check
	$(DOCKER_COMPOSE) exec docs2app python main.py health-check

config: ## Show current configuration
	$(DOCKER_COMPOSE) exec docs2app python main.py config --show

# Analysis commands
analyze: ## Analyze PDFs in ./pdfs directory (usage: make analyze PROJECT=myapp)
	@if [ -z "$(PROJECT)" ]; then \
		echo "❌ Please specify PROJECT name: make analyze PROJECT=myapp"; \
		exit 1; \
	fi
	$(DOCKER_COMPOSE) exec docs2app python main.py batch /app/pdfs --project-name "$(PROJECT)"

analyze-file: ## Analyze specific PDF file (usage: make analyze-file FILE=document.pdf PROJECT=myapp)
	@if [ -z "$(FILE)" ] || [ -z "$(PROJECT)" ]; then \
		echo "❌ Please specify FILE and PROJECT: make analyze-file FILE=document.pdf PROJECT=myapp"; \
		exit 1; \
	fi
	$(DOCKER_COMPOSE) exec docs2app python main.py analyze /app/pdfs/$(FILE) --project-name "$(PROJECT)"

# Development commands
dev-setup: ## Setup development environment
	@echo "🔧 Setting up development environment..."
	@cp .env.example .env || true
	@echo "✅ .env file created (configure your API keys)"
	@echo "📁 Make sure to place PDF files in ./pdfs directory"

test: ## Run tests
	$(DOCKER_COMPOSE) exec docs2app python -m pytest tests/ -v

lint: ## Run code linting
	$(DOCKER_COMPOSE) exec docs2app python -m flake8 docs2app/

# Utility commands
clean: ## Clean up Docker resources
	$(DOCKER_COMPOSE) down -v --remove-orphans
	docker system prune -f
	docker volume prune -f

clean-all: ## Clean up everything including images
	$(DOCKER_COMPOSE) down -v --remove-orphans --rmi all
	docker system prune -af
	docker volume prune -f

pull-model: ## Pull/update Ollama model
	$(DOCKER_COMPOSE) exec ollama ollama pull llama3.1:8b

list-models: ## List available Ollama models
	$(DOCKER_COMPOSE) exec ollama ollama list

# File operations
copy-output: ## Copy generated output to host (usage: make copy-output PROJECT=myapp)
	@if [ -z "$(PROJECT)" ]; then \
		echo "❌ Please specify PROJECT name: make copy-output PROJECT=myapp"; \
		exit 1; \
	fi
	$(DOCKER_COMPOSE) exec docs2app cp -r /app/output/$(PROJECT) /tmp/
	docker cp docs2app:/tmp/$(PROJECT) ./output/

backup: ## Backup current state
	@DATE=$$(date +%Y%m%d_%H%M%S) && \
	tar -czf backup_$$DATE.tar.gz pdfs output .env config.yaml && \
	echo "✅ Backup created: backup_$$DATE.tar.gz"

# Quick start commands
quick-start: dev-setup build up ## Complete setup for new users
	@echo ""
	@echo "🎉 Docs2App is ready!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Place PDF files in ./pdfs directory"
	@echo "2. Configure API keys in .env file (optional, Ollama works without keys)"
	@echo "3. Run: make analyze PROJECT=myproject"
	@echo ""
	@echo "Commands:"
	@echo "  make health     - Check system status"
	@echo "  make config     - View configuration"
	@echo "  make analyze    - Process PDFs"
	@echo "  make shell      - Interactive mode"

# Example workflow
demo: ## Run demo with sample data (if available)
	@if [ ! -d "./pdfs" ] || [ -z "$$(ls -A ./pdfs 2>/dev/null)" ]; then \
		echo "❌ No PDF files found in ./pdfs directory"; \
		echo "📝 Please add PDF files to ./pdfs directory first"; \
		exit 1; \
	fi
	@echo "🚀 Running demo analysis..."
	$(DOCKER_COMPOSE) exec docs2app python main.py batch /app/pdfs --project-name "demo-project"

# Debug commands
debug: ## Enter debug mode with verbose logging
	$(DOCKER_COMPOSE) exec -e LOG_LEVEL=DEBUG docs2app python main.py health-check --verbose

inspect: ## Inspect Docker containers
	@echo "=== Container Status ==="
	$(DOCKER_COMPOSE) ps
	@echo ""
	@echo "=== Network Info ==="
	docker network ls | grep docs2app
	@echo ""
	@echo "=== Volume Info ==="
	docker volume ls | grep docs2app

# CI/CD helpers
ci-build: ## Build for CI/CD
	$(DOCKER_COMPOSE) build --no-cache

ci-test: ## Run tests for CI/CD
	$(DOCKER_COMPOSE) up -d
	sleep 30
	$(DOCKER_COMPOSE) exec -T docs2app python main.py health-check
	$(DOCKER_COMPOSE) down
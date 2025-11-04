.PHONY: help build up down logs restart health test clean

.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "Sigma Validator Service - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Build Docker image
	@echo "Building sigma-validator Docker image..."
	docker-compose build

up: ## Start validator service
	@echo "Starting sigma-validator service..."
	docker-compose up -d
	@echo ""
	@echo "Waiting for service to be ready..."
	@sleep 5
	@$(MAKE) health

down: ## Stop validator service
	@echo "Stopping sigma-validator service..."
	docker-compose down

logs: ## View service logs (follow mode)
	docker-compose logs -f sigma-validator

restart: ## Restart validator service
	@echo "Restarting sigma-validator service..."
	docker-compose restart
	@sleep 3
	@$(MAKE) health

health: ## Check service health
	@echo "Checking validator service health..."
	@curl -sf http://localhost:8080/health | python3 -m json.tool || echo "❌ Service not healthy"

test: ## Test validation endpoint with a sample rule
	@echo "Testing validation endpoint..."
	@curl -X POST http://localhost:8080/validate \
		-H "Content-Type: application/json" \
		-d '{"sigma_rule": "title: Test Rule\nid: test-001\nstatus: experimental\nlogsource:\n  category: process_creation\n  product: windows\ndetection:\n  selection:\n    CommandLine|contains: \"test\"\n  condition: selection"}' \
		| python3 -m json.tool

status: ## Show container status
	docker-compose ps

clean: ## Remove container and image
	@echo "Cleaning up..."
	docker-compose down -v
	docker rmi sigma-validator-service-sigma-validator 2>/dev/null || true
	@echo "Cleanup complete"

rebuild: clean build up ## Clean, rebuild, and start service

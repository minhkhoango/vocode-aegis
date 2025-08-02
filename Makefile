# Makefile for Vocode Analytics Dashboard
# Usage: make <target>

# Default target
.DEFAULT_GOAL := help

# Variables
DASHBOARD_PORT ?= 3001
REDIS_PORT ?= 6379

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
BLUE := \033[0;34m
NC := \033[0m # No Color

.PHONY: help start start-no-build stop restart logs clean

help: ## Show this help message. Use 'make <command>'
	@echo "$(BLUE)Vocode Analytics Dashboard - Essential Commands:$(NC)"
	@echo "  $(GREEN)start$(NC)        - Build & start the dashboard."
	@echo "  $(GREEN)start-no-build$(NC) - Start without rebuilding."
	@echo "  $(GREEN)stop$(NC)         - Stop the dashboard containers."
	@echo "  $(GREEN)restart$(NC)      - Restart the dashboard."
	@echo "  $(GREEN)logs$(NC)         - View real-time logs."
	@echo "  $(GREEN)clean$(NC)        - Stop, remove containers/volumes/network."

start: ## Build & start the dashboard.
	@echo "$(BLUE)🚀 Building & starting dashboard...$(NC)"
	docker compose up -d --build --wait
	@echo "$(GREEN)✅ Dashboard running at http://localhost:3001$(NC)"

start-no-build: ## Start dashboard (skip build).
	@echo "$(BLUE)🚀 Starting dashboard (no build)...$(NC)"
	docker compose up -d --wait
	@echo "$(GREEN)✅ Dashboard running at http://localhost:3001$(NC)"

stop: ## Stop dashboard containers.
	@echo "$(BLUE)🛑 Stopping dashboard...$(NC)"
	docker compose down
	@echo "$(GREEN)✅ Dashboard stopped.$(NC)"

restart: stop start-no-build ## Restart the dashboard.

logs: ## View real-time logs.
	@echo "$(BLUE)📋 Viewing logs...$(NC)"
	docker compose logs -f

clean: ## Stop and remove all Docker resources.
	@echo "$(BLUE)🧹 Cleaning up all Docker resources...$(NC)"
	docker compose down --volumes --remove-orphans
	docker network rm vocode-network 2>/dev/null || true
	docker images | grep vocode | awk '{print $$3}' | xargs -r docker rmi -f
	docker volume ls | grep vocode | awk '{print $$2}' | xargs -r docker volume rm
	docker system prune -f
	@echo "$(GREEN)✅ Cleanup complete!$(NC)" 
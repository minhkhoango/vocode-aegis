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

.PHONY: help start start-no-build stop restart build logs status health clean

# Help target
help: ## Show this help message
	@echo "$(BLUE)Vocode Analytics Dashboard - Available Commands:$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)Quick Start:$(NC)"
	@echo "  make start         - Start the dashboard (with build)"
	@echo "  make start-no-build - Start the dashboard (skip build)"
	@echo "  make stop          - Stop the dashboard"
	@echo "  make logs          - View logs"
	@echo "  make status        - Check service status"

# Pre-deployment checks
check-docker: ## Check if Docker is running
	@if ! docker info > /dev/null 2>&1; then \
		echo "$(RED)❌ Docker is not running. Please start Docker Desktop or the Docker daemon.$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✅ Docker daemon is running.$(NC)"

check-port: ## Check if dashboard port is available
	@if lsof -Pi :$(DASHBOARD_PORT) -sTCP:LISTEN -t >/dev/null 2>&1; then \
		echo "$(RED)❌ Port $(DASHBOARD_PORT) is already in use.$(NC)"; \
		echo "Please free the port or modify DASHBOARD_PORT in your .env file."; \
		exit 1; \
	fi
	@echo "$(GREEN)✅ Port $(DASHBOARD_PORT) is available.$(NC)"

check-env: ## Check for .env file
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)⚠️  .env file not found. Creating with default values.$(NC)"; \
		echo "DASHBOARD_PORT=$(DASHBOARD_PORT)" > .env; \
		echo "REDIS_HOST=redis" >> .env; \
		echo "REDIS_PORT=$(REDIS_PORT)" >> .env; \
	fi

# Main deployment targets
start: check-docker check-env check-port ## Start the Vocode Analytics Dashboard (with build)
	@echo "$(BLUE)🚀 Starting Vocode Analytics Dashboard...$(NC)"
	@echo "$(BLUE)📦 Building dashboard image...$(NC)"
	docker compose build --no-cache
	@echo "$(BLUE)🔧 Starting services...$(NC)"
	docker compose up -d
	@echo "$(GREEN)✅ Dashboard started!$(NC)"
	@echo "$(GREEN)🌐 Access at:$(NC) http://localhost:$(DASHBOARD_PORT)"

start-no-build: check-docker check-env check-port ## Start the Vocode Analytics Dashboard (skip build)
	@echo "$(BLUE)🚀 Starting Vocode Analytics Dashboard (no build)...$(NC)"
	@echo "$(BLUE)🔧 Starting services...$(NC)"
	docker compose up -d
	@echo "$(GREEN)✅ Dashboard started!$(NC)"
	@echo "$(GREEN)🌐 Access at:$(NC) http://localhost:$(DASHBOARD_PORT)"

stop: ## Stop the Vocode Analytics Dashboard
	@echo "$(BLUE)🛑 Stopping Vocode Analytics Dashboard...$(NC)"
	docker compose down
	@echo "$(GREEN)✅ Dashboard stopped.$(NC)"

restart: stop start-no-build ## Restart the Vocode Analytics Dashboard

# Build target
build: check-docker ## Build the dashboard image
	@echo "$(BLUE)📦 Building dashboard image...$(NC)"
	docker compose build --no-cache
	@echo "$(GREEN)✅ Build complete.$(NC)"

# Monitoring targets
logs: ## View real-time logs
	@echo "$(BLUE)📋 Viewing logs...$(NC)"
	docker compose logs -f

status: ## Check service status
	@echo "$(BLUE)📊 Service Status:$(NC)"
	docker compose ps

health: ## Test health endpoint
	@echo "$(BLUE)🏥 Testing health endpoint...$(NC)"
	@if curl -f http://localhost:$(DASHBOARD_PORT)/health > /dev/null 2>&1; then \
		echo "$(GREEN)✅ Health check passed!$(NC)"; \
		curl -s http://localhost:$(DASHBOARD_PORT)/health | jq . 2>/dev/null || curl -s http://localhost:$(DASHBOARD_PORT)/health; \
	else \
		echo "$(RED)❌ Health check failed!$(NC)"; \
		echo "Service might not be running. Try: make start"; \
	fi

# Cleanup target
clean: ## Stop and remove containers, networks, and volumes
	@echo "$(BLUE)🧹 Cleaning up...$(NC)"
	docker compose down --volumes --remove-orphans
	@echo "$(GREEN)✅ Cleanup complete.$(NC)" 
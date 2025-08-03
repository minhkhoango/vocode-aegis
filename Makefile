# Vocode Analytics Dashboard Makefile

.DEFAULT_GOAL := help

DASHBOARD_PORT ?= 3001
REDIS_PORT ?= 6379

GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
BLUE := \033[0;34m
NC := \033[0m

.PHONY: help start start-no-build stop restart logs clean tunnel install-cloudflared check-deps

check-deps:
	@if ! command -v docker >/dev/null 2>&1; then \
		echo "$(RED)❌ Docker not installed$(NC)"; exit 1; \
	fi
	@if ! docker info >/dev/null 2>&1; then \
		echo "$(RED)❌ Docker not running or no permission$(NC)"; exit 1; \
	fi
	@if ! command -v docker compose >/dev/null 2>&1; then \
		echo "$(RED)❌ Docker Compose not installed$(NC)"; exit 1; \
	fi

help:
	@echo "$(BLUE)Vocode Dashboard Commands:$(NC)"
	@echo "  $(GREEN)start$(NC)        - Build & start dashboard"
	@echo "  $(GREEN)start-no-build$(NC) - Start without rebuild"
	@echo "  $(GREEN)stop$(NC)         - Stop containers"
	@echo "  $(GREEN)restart$(NC)      - Restart dashboard"
	@echo "  $(GREEN)logs$(NC)         - View logs"
	@echo "  $(GREEN)clean$(NC)        - Remove all resources"
	@echo "  $(GREEN)tunnel$(NC)       - Create public tunnel"

start: check-deps
	@echo "$(BLUE)🚀 Starting dashboard...$(NC)"
	@docker compose up -d --build --wait || (echo "$(RED)❌ Failed to start$(NC)"; exit 1)
	@echo "$(GREEN)✅ Dashboard: http://localhost:$(DASHBOARD_PORT)$(NC)"

start-no-build: check-deps
	@echo "$(BLUE)🚀 Starting dashboard...$(NC)"
	@docker compose up -d --wait || (echo "$(RED)❌ Failed to start$(NC)"; exit 1)
	@echo "$(GREEN)✅ Dashboard: http://localhost:$(DASHBOARD_PORT)$(NC)"

stop:
	@echo "$(BLUE)🛑 Stopping...$(NC)"
	@docker compose down || true
	@echo "$(GREEN)✅ Stopped$(NC)"

restart: stop start-no-build

logs:
	@docker compose logs -f

clean:
	@echo "$(BLUE)🧹 Cleaning...$(NC)"
	@docker compose down --volumes --remove-orphans || true
	@docker network rm vocode-network 2>/dev/null || true
	@docker images | grep vocode | awk '{print $$3}' | xargs -r docker rmi -f || true
	@docker volume ls | grep vocode | awk '{print $$2}' | xargs -r docker volume rm || true
	@docker system prune -f
	@echo "$(GREEN)✅ Cleaned$(NC)"

install-cloudflared:
	@if command -v cloudflared >/dev/null 2>&1; then \
		echo "$(GREEN)✅ Cloudflared installed$(NC)"; \
	else \
		echo "$(YELLOW)📦 Installing cloudflared...$(NC)"; \
		curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb; \
		sudo dpkg -i cloudflared.deb; rm cloudflared.deb; \
		echo "$(GREEN)✅ Installed$(NC)"; \
	fi

tunnel: install-cloudflared
	@echo "$(BLUE)🌐 Creating tunnel...$(NC)"
	@echo "$(YELLOW)⚠️  Public access enabled$(NC)"
	@cloudflared tunnel --url http://localhost:$(DASHBOARD_PORT) 
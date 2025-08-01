#!/bin/bash
# deploy.sh - Zero-configuration deployment script

# Exit immediately if a command exits with a non-zero status.
set -e

echo "🚀 Starting Vocode Analytics Dashboard deployment..."

# --- Pre-deployment Checks ---

# 1. Check if Docker is running
echo "Verifying Docker daemon status..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop or the Docker daemon."
    exit 1
fi
echo "✅ Docker daemon is running."

# 2. Check for .env file
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example with default values."
    cp .env.example .env
fi

# Load environment variables from .env
set -a # Automatically export all variables subsequently defined
. ./.env
set +a # Stop automatically exporting variables

# 3. Check if the dashboard port is available
DASHBOARD_PORT=${DASHBOARD_PORT:-3001} # Use default if not set in .env
echo "Checking if port ${DASHBOARD_PORT} is available..."
if lsof -Pi :${DASHBOARD_PORT} -sTCP:LISTEN -t >/dev/null ; then
    echo "❌ Port ${DASHBOARD_PORT} is already in use on your host machine."
    echo "Please free the port or modify the DASHBOARD_PORT in your .env file"
    echo "and in docker-compose.yml (under vocode-analytics-dashboard -> ports)."
    exit 1
fi
echo "✅ Port ${DASHBOARD_PORT} is available."

# --- Deployment ---

echo "📦 Building dashboard image (this may take a few minutes)..."
# `--no-cache` can be removed for faster subsequent builds if dependencies haven't changed
docker compose build --no-cache

echo "🔧 Starting services..."
# `-d` runs containers in detached mode (background)
# `--wait` waits for services to be healthy (Docker Compose V2)
# Or use `sleep` as a fallback for older Docker Compose versions
docker compose up -d --wait

# Fallback for older Docker Compose versions that don't have --wait
# if [ $? -ne 0 ]; then
#   echo "Initial `docker compose up -d` failed. Checking logs..."
#   docker compose logs
#   exit 1
# fi
# echo "⏳ Giving services a few more seconds to become fully ready..."
# sleep 15 # Give it a little more buffer for full readiness

# --- Post-deployment Checks & Info ---

echo "📋 Checking deployed services health..."
# Check if services are reporting as healthy. `docker compose ps -q` gets container IDs.
# `xargs docker inspect` gets details, `jq` filters for health status.
# More robust health check would query the actual /health endpoint
HEALTHY_SERVICES=$(docker compose ps --filter "status=running" --format "{{.Name}}" | xargs -I {} docker inspect --format "{{json .State.Health.Status}}" {} | grep -c "healthy")
TOTAL_SERVICES=$(docker compose ps --format "{{.Name}}" | wc -l)

# Strip whitespace from counts
HEALTHY_SERVICES=$(echo ${HEALTHY_SERVICES})
TOTAL_SERVICES=$(echo ${TOTAL_SERVICES})

if [ "${HEALTHY_SERVICES}" -eq "${TOTAL_SERVICES}" ] && [ "${TOTAL_SERVICES}" -gt 0 ]; then
    echo "✅ Dashboard and all services deployed successfully and are healthy!"
    echo ""
    echo "🌐 **Access your Vocode Analytics Dashboard at:** http://localhost:${DASHBOARD_PORT}"
    echo ""
    echo "🔍 **To access Redis Commander (for debugging/inspection), run:**"
    echo "   docker compose --profile debug up -d"
    echo "   Then navigate to: http://localhost:8081"
    echo ""
    echo "Remember: Your Vocode application needs to be configured to publish data to the 'vocode-redis' service"
    echo "in the 'vocode-network' using stream names like 'vocode:conversations' and 'vocode:errors'."
else
    echo "❌ Deployment failed or some services are not healthy."
    echo "Please check the logs for details:"
    echo "  docker compose logs -f"
    exit 1
fi

echo ""
echo "--- Useful Commands ---"
echo "  • View real-time logs: docker compose logs -f"
echo "  • Stop dashboard: docker compose down"
echo "  • Restart dashboard: docker compose restart vocode-analytics-dashboard"
echo "  • Stop all services: docker compose down --volumes"
echo "  • Clean up images: docker rmi $(docker images -q 'vocode-analytics-dashboard-*')"
echo ""
echo "Go build something amazing. Don't waste time."
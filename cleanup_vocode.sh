#!/bin/bash
# cleanup_vocode.sh – Fully clean up all Docker resources related to Vocode

echo "🧹 Starting cleanup of Vocode Docker resources..."

# 1. Stop and remove all containers
echo "📦 Stopping and removing containers..."
docker compose down --volumes --remove-orphans
docker compose --profile debug down --volumes --remove-orphans

# 2. Remove network
echo "🌐 Removing network..."
docker network rm vocode-network 2>/dev/null || echo "Network 'vocode-network' does not exist or has already been removed"

# 3. Remove images
echo "🖼️ Removing images..."
docker images | grep vocode | awk '{print $3}' | xargs -r docker rmi -f

# 4. Remove volumes
echo "💾 Removing volumes..."
docker volume ls | grep vocode | awk '{print $2}' | xargs -r docker volume rm

# 5. Remove any leftover containers (if any)
echo "🗑️ Removing leftover containers..."
docker ps -a --filter "name=vocode" --format "{{.ID}}" | xargs -r docker rm -f
docker ps -a --filter "name=analytics" --format "{{.ID}}" | xargs -r docker rm -f

# 6. Prune unused resources
echo "🧽 Pruning unused resources..."
docker system prune -f

echo "✅ Cleanup complete!"
echo ""
echo "📋 Summary:"
echo "  • Containers: removed"
echo "  • Networks: removed"
echo "  • Images: removed"
echo "  • Volumes: removed"
echo "  • Unused resources: pruned"

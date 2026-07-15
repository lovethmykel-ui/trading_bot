#!/bin/bash
set -e

echo "🚀 Deploying Quantum Trading Bot..."

# Pull latest changes
git fetch origin main
git reset --hard origin/main

# Rebuild containers and restart
echo "🐳 Rebuilding and starting Docker containers..."
docker-compose down
docker-compose build
docker-compose up -d

echo "✅ Deployment successful. Bot is running in the background."

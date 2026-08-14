#!/bin/bash
# ==============================================================================
# MPSC AI — 1-Click Production Cloud Backend Deployment Script
# Free-Tier Deployment Script for Render / Railway / Fly.io / VPS
# ==============================================================================

set -e

echo "=================================================="
echo "🚀 MPSC AI — CLOUD BACKEND DEPLOYMENT"
echo "=================================================="

# 1. Check Docker & Environment
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
fi

echo "✅ Docker is installed."

# 2. Build & Launch Container
echo "📦 Building Production Docker Image..."
docker compose build

echo "⚡ Starting Cloud Service Container..."
docker compose up -d

echo "=================================================="
echo "🎉 DEPLOYMENT COMPLETE!"
echo "Health Check Endpoint: http://localhost:8000/api/health"
echo "=================================================="

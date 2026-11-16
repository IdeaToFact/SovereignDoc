#!/usr/bin/env bash
# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only
# ==============================================================================
# SovereignDoc Community Edition: Docker Launch Helper Script (Linux / macOS)
# Builds, pulls, and launches the air-gapped All-in-One Workstation container.
# ==============================================================================

set -euo pipefail

IMAGE_NAME="airgapaxis/sovereigndoc:1.1.0-community"
LOCAL_IMAGE="airgapaxis/sovereigndoc:latest"
PORT="${SOVEREIGNDOC_PORT:-8000}"
OLLAMA_URL="${OLLAMA_BASE_URL:-http://host.docker.internal:11434}"
DATA_DIR=""
DETACH=true
NO_BROWSER=false
BUILD_ONLY=false
REBUILD=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        --data-dir)
            DATA_DIR="$2"
            shift 2
            ;;
        --ollama-url)
            OLLAMA_URL="$2"
            shift 2
            ;;
        --no-browser)
            NO_BROWSER=true
            shift
            ;;
        --build-only)
            BUILD_ONLY=true
            shift
            ;;
        --rebuild)
            REBUILD=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: ./docker-run.sh [-p 8000] [--data-dir /path] [--no-browser] [--rebuild]"
            exit 1
            ;;
    esac
done

# 1. Verify Docker CLI and Daemon Availability
if ! command -v docker >/dev/null 2>&1; then
    echo "❌ Error: Docker is not installed or not available in PATH."
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo "❌ Error: Docker daemon is not running."
    exit 1
fi

# 2. Configure Volume Mount Path
if [ -n "$DATA_DIR" ] && [ -d "$DATA_DIR" ]; then
    DATA_ABS="$(cd "$DATA_DIR" && pwd)"
    VOLUME_MOUNT="$DATA_ABS:/root/.sovereigndoc"
    STORAGE_DISPLAY="$DATA_ABS"
else
    VOLUME_MOUNT="sovereigndoc_data:/root/.sovereigndoc"
    STORAGE_DISPLAY="Docker Named Volume (sovereigndoc_data)"
fi

echo "======================================================================"
echo "🎯 SovereignDoc Community Edition (v1.1.0-community)"
echo "  Platform:  AirGap Axis Zero-Telemetry AI Document Workstation"
echo "  Image:     $IMAGE_NAME"
echo "  Storage:   $STORAGE_DISPLAY"
echo "  Workstation: http://localhost:$PORT"
echo "  API Docs:    http://localhost:$PORT/docs"
echo "======================================================================"

# 3. Check Docker image (Use local if present, try pull, or build)
IMAGE_EXISTS=false
if docker image inspect "$IMAGE_NAME" >/dev/null 2>&1 || docker image inspect "$LOCAL_IMAGE" >/dev/null 2>&1; then
    IMAGE_EXISTS=true
fi

if [ "$REBUILD" = true ] || [ "$IMAGE_EXISTS" = false ]; then
    if [ "$REBUILD" = false ]; then
        echo "🔍 Checking Docker Hub for '$IMAGE_NAME'..."
        if docker pull "$IMAGE_NAME" >/dev/null 2>&1; then
            IMAGE_EXISTS=true
        fi
    fi
    if [ "$REBUILD" = true ] || [ "$IMAGE_EXISTS" = false ]; then
        echo "🔨 Building Docker image '$IMAGE_NAME' from source..."
        docker build -t "$IMAGE_NAME" -t "$LOCAL_IMAGE" -f Dockerfile .
    fi
fi

if [ "$BUILD_ONLY" = true ]; then
    echo "✅ Build complete (--build-only specified). Exiting."
    exit 0
fi

# 4. Remove any stale container instance from previous runs
docker rm -f sovereigndoc >/dev/null 2>&1 || true

# 5. Run the Container
echo "🚀 Launching SovereignDoc container..."

CONTAINER_ID=$(docker run -d \
    --name sovereigndoc \
    -p "127.0.0.1:$PORT:8000" \
    -v "$VOLUME_MOUNT" \
    -e "OLLAMA_BASE_URL=$OLLAMA_URL" \
    -e "SOVEREIGNDOC_OLLAMA_URL=$OLLAMA_URL" \
    -e "SOVEREIGNDOC_HOST=0.0.0.0" \
    -e "SOVEREIGNDOC_PORT=8000" \
    -e "ANONYMIZED_TELEMETRY=False" \
    -e "CHROMA_TELEMETRY_IMPL=none" \
    -e "DO_NOT_TRACK=1" \
    -e "HF_HUB_DISABLE_TELEMETRY=1" \
    -e "HF_HUB_OFFLINE=1" \
    --add-host host.docker.internal:host-gateway \
    --restart unless-stopped \
    "$IMAGE_NAME")

# 6. Wait for Healthy Status API
echo "⏳ Probing workstation readiness..."
TARGET_URL="http://localhost:$PORT"

for i in $(seq 1 12); do
    sleep 1
    if curl -s "http://127.0.0.1:$PORT/api/system/health" | grep -q '"app":"SovereignDoc"'; then
        break
    fi
done

echo ""
echo "✅ SovereignDoc Workstation is active!"
echo "   Container:    sovereigndoc ($CONTAINER_ID)"
echo "   Workstation:  $TARGET_URL"
echo "   Swagger Docs: ${TARGET_URL}/docs"
echo "   Stop Command: docker stop sovereigndoc"
echo "   View Logs:    docker logs -f sovereigndoc"
echo ""

if [ "$NO_BROWSER" = false ]; then
    if command -v xdg-open >/dev/null 2>&1; then
        xdg-open "$TARGET_URL" >/dev/null 2>&1 || true
    elif command -v open >/dev/null 2>&1; then
        open "$TARGET_URL" >/dev/null 2>&1 || true
    fi
fi

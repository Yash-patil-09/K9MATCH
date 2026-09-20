#!/usr/bin/env bash
# ==============================================================================
# K9Match Production Build Script for Cloud Platforms (Render, Railway, VPS)
# ==============================================================================

# Exit immediately if a command exits with a non-zero status
set -o errexit

echo "==> [1/3] Installing Python production dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "==> [2/3] Collecting and compressing static assets via WhiteNoise..."
python manage.py collectstatic --no-input

echo "==> [3/3] Running database migrations..."
python manage.py migrate

echo "==> Build complete! Ready to start gunicorn."

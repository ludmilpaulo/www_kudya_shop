#!/usr/bin/env bash
# Kudya super-app setup — run from www_kudya_shop with venv activated
set -e
cd "$(dirname "$0")/.."

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Creating migrations..."
python manage.py makemigrations contas services kudya_platform doctors accommodation properties wallets payments commissions rides deliveries rentals pricing support
python manage.py migrate

echo "Seeding platform data..."
python manage.py seed_superapp

echo "Done. Start API with: daphne -b 0.0.0.0 -p 8000 www_kudya_shop.asgi:application"
echo "API docs: http://127.0.0.1:8000/api/docs/"

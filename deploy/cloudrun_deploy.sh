#!/usr/bin/env bash
set -e

PROJECT_ID=${1:-"your-gcp-project-id"}
REGION="asia-south1"
SERVICE_NAME="cloud-rsvp-tracker"

echo "Building container image on Google Cloud Build..."
gcloud builds submit --tag gcr.io/${PROJECT_ID}/${SERVICE_NAME}

echo "Deploying to Google Cloud Run (Free Tier)..."
gcloud run deploy ${SERVICE_NAME} \
  --image gcr.io/${PROJECT_ID}/${SERVICE_NAME} \
  --region ${REGION} \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1

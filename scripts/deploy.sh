#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="jazari-coach"
REGION="us-central1"
SERVICE="jazari-agent"
GCS_BUCKET="jazari-media"

echo "=== Jazari Deploy Script ==="

# Step 1: Create GCS bucket if not exists
echo "[1/4] Checking GCS bucket..."
if ! gcloud storage buckets describe "gs://$GCS_BUCKET" --project="$PROJECT_ID" &>/dev/null; then
    echo "  Creating gs://$GCS_BUCKET..."
    gcloud storage buckets create "gs://$GCS_BUCKET" \
        --project="$PROJECT_ID" \
        --location="$REGION" \
        --uniform-bucket-level-access
else
    echo "  Bucket exists."
fi

# Step 2: Ensure Secret Manager has GOOGLE_API_KEY
echo "[2/4] Checking secrets..."
if ! gcloud secrets describe GOOGLE_API_KEY --project="$PROJECT_ID" &>/dev/null; then
    echo "  ERROR: GOOGLE_API_KEY secret not found in Secret Manager."
    echo "  Create it: gcloud secrets create GOOGLE_API_KEY --project=$PROJECT_ID"
    echo "  Add value: echo -n 'your-key' | gcloud secrets versions add GOOGLE_API_KEY --data-file=- --project=$PROJECT_ID"
    exit 1
else
    echo "  Secret exists."
fi

# Step 3: Build and deploy via Cloud Build
echo "[3/4] Submitting Cloud Build..."
gcloud builds submit \
    --project="$PROJECT_ID" \
    --config=cloudbuild.yaml

# Step 4: Get service URL
echo "[4/4] Getting service URL..."
URL=$(gcloud run services describe "$SERVICE" \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --format='value(status.url)')
echo ""
echo "=== Deploy Complete ==="
echo "URL: $URL"
echo "Health: $URL/health"

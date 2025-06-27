#!/bin/bash

# Google Cloud deployment script for Sales Order Entry System

set -e

# Configuration
PROJECT_ID="sales-order-system-dev"
REGION="us-central1"
ZONE="us-central1-a"
SERVICE_ACCOUNT_BACKEND="sales-order-backend-sa"
SERVICE_ACCOUNT_FRONTEND="sales-order-frontend-sa"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if gcloud CLI is installed
if ! command -v gcloud &> /dev/null; then
    log_error "Google Cloud CLI is not installed. Please install it first."
    exit 1
fi

# Check if authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    log_error "Not authenticated with Google Cloud. Please run 'gcloud auth login' first."
    exit 1
fi

log_info "Starting Google Cloud resource deployment..."

# Set project
log_step "Setting project to $PROJECT_ID"
gcloud config set project "$PROJECT_ID"

# Enable required APIs
log_step "Enabling required Google Cloud APIs..."
gcloud services enable \
    cloudsql.googleapis.com \
    storage.googleapis.com \
    secretmanager.googleapis.com \
    aiplatform.googleapis.com \
    discoveryengine.googleapis.com \
    run.googleapis.com \
    apigateway.googleapis.com \
    monitoring.googleapis.com \
    logging.googleapis.com \
    cloudbuild.googleapis.com

# Create service accounts
log_step "Creating service accounts..."
gcloud iam service-accounts create "$SERVICE_ACCOUNT_BACKEND" \
    --display-name="Sales Order Backend Service Account" \
    --description="Service account for the backend application" || true

gcloud iam service-accounts create "$SERVICE_ACCOUNT_FRONTEND" \
    --display-name="Sales Order Frontend Service Account" \
    --description="Service account for the frontend application" || true

# Grant IAM roles to backend service account
log_step "Granting IAM roles to backend service account..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SERVICE_ACCOUNT_BACKEND}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SERVICE_ACCOUNT_BACKEND}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SERVICE_ACCOUNT_BACKEND}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SERVICE_ACCOUNT_BACKEND}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SERVICE_ACCOUNT_BACKEND}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/discoveryengine.viewer"

# Create Cloud SQL instance
log_step "Creating Cloud SQL instance..."
gcloud sql instances create sales-order-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region="$REGION" \
    --storage-size=20GB \
    --storage-type=SSD \
    --backup \
    --enable-bin-log \
    --deletion-protection || true

# Create database
log_step "Creating database..."
gcloud sql databases create sales_orders \
    --instance=sales-order-db || true

# Set database password
log_step "Setting database password..."
DB_PASSWORD=$(openssl rand -base64 32)
gcloud sql users set-password postgres \
    --instance=sales-order-db \
    --password="$DB_PASSWORD"

# Create storage buckets
log_step "Creating Cloud Storage buckets..."
gsutil mb -p "$PROJECT_ID" -l "$REGION" "gs://sales-order-documents-${PROJECT_ID}" || true
gsutil mb -p "$PROJECT_ID" -l "$REGION" "gs://sales-order-parts-catalog-${PROJECT_ID}" || true
gsutil mb -p "$PROJECT_ID" -l "$REGION" "gs://sales-order-backups-${PROJECT_ID}" || true

# Create secrets
log_step "Creating secrets in Secret Manager..."
echo "sk-your-openai-key-here" | gcloud secrets create openai-api-key --data-file=- || true
echo "your-tenant-id" | gcloud secrets create dynamics-365-tenant-id --data-file=- || true
echo "your-client-id" | gcloud secrets create dynamics-365-client-id --data-file=- || true
echo "your-client-secret" | gcloud secrets create dynamics-365-client-secret --data-file=- || true
echo "https://your-org.crm.dynamics.com" | gcloud secrets create dynamics-365-resource-url --data-file=- || true

# Get Cloud SQL connection name
SQL_CONNECTION_NAME=$(gcloud sql instances describe sales-order-db --format="value(connectionName)")

# Create .env file
log_step "Creating .env file with Google Cloud configuration..."
cat > ../.env << EOF
# Google Cloud Services (Generated from deployment)
GOOGLE_CLOUD_PROJECT=$PROJECT_ID
GOOGLE_CLOUD_REGION=$REGION

# Cloud SQL
CLOUD_SQL_CONNECTION_NAME=$SQL_CONNECTION_NAME
CLOUD_SQL_DATABASE_NAME=sales_orders
CLOUD_SQL_USER=postgres
CLOUD_SQL_PASSWORD=$DB_PASSWORD

# Cloud Storage
GCS_DOCUMENTS_BUCKET=sales-order-documents-$PROJECT_ID
GCS_PARTS_CATALOG_BUCKET=sales-order-parts-catalog-$PROJECT_ID
GCS_BACKUP_BUCKET=sales-order-backups-$PROJECT_ID

# Vertex AI
VERTEX_AI_LOCATION=us-central1
VERTEX_SEARCH_APP_ID=sales-order-search
VERTEX_SEARCH_DATASTORE_ID=parts-catalog-datastore

# Secret Manager (use gcloud to access)
OPENAI_API_KEY_SECRET=projects/$PROJECT_ID/secrets/openai-api-key/versions/latest
DYNAMICS_365_TENANT_ID_SECRET=projects/$PROJECT_ID/secrets/dynamics-365-tenant-id/versions/latest
DYNAMICS_365_CLIENT_ID_SECRET=projects/$PROJECT_ID/secrets/dynamics-365-client-id/versions/latest
DYNAMICS_365_CLIENT_SECRET_SECRET=projects/$PROJECT_ID/secrets/dynamics-365-client-secret/versions/latest
DYNAMICS_365_RESOURCE_URL_SECRET=projects/$PROJECT_ID/secrets/dynamics-365-resource-url/versions/latest

# Service Accounts
BACKEND_SERVICE_ACCOUNT=${SERVICE_ACCOUNT_BACKEND}@${PROJECT_ID}.iam.gserviceaccount.com
FRONTEND_SERVICE_ACCOUNT=${SERVICE_ACCOUNT_FRONTEND}@${PROJECT_ID}.iam.gserviceaccount.com

# Frontend Environment Variables
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_BASE_URL=ws://localhost:8000
EOF

log_info "Environment file created at ../.env"

# Display summary
echo ""
log_info "=== Deployment Summary ==="
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo ""
echo "Key Resources Created:"
echo "- Cloud SQL Instance: sales-order-db"
echo "- Storage Buckets: sales-order-*-$PROJECT_ID"
echo "- Service Accounts: $SERVICE_ACCOUNT_BACKEND, $SERVICE_ACCOUNT_FRONTEND"
echo "- Secrets: openai-api-key, dynamics-365-*"
echo ""
log_info "Next steps:"
echo "1. Update secrets with actual values:"
echo "   gcloud secrets versions add openai-api-key --data-file=<your-key-file>"
echo "2. Create Vertex AI Search app (manual step in console)"
echo "3. Build and deploy containers:"
echo "   ./build-and-deploy.sh"
echo "4. Access the application at the Cloud Run service URL"

log_warn "Please update the secrets in Secret Manager with actual values!"
log_warn "OpenAI API key and Dynamics 365 credentials need to be configured manually."
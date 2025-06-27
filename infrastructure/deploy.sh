#!/bin/bash

# Deployment script for Sales Order System
# This script sets up the complete Google Cloud infrastructure and deploys the application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="$SCRIPT_DIR/terraform"

# Default values
ENVIRONMENT="production"
REGION="us-central1"
SKIP_TERRAFORM=false
SKIP_BUILD=false
SKIP_DEPLOY=false

# Usage function
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -p, --project PROJECT_ID    Google Cloud Project ID (required)"
    echo "  -e, --environment ENV        Environment (dev/staging/production, default: production)"
    echo "  -r, --region REGION         Google Cloud region (default: us-central1)"
    echo "  --skip-terraform            Skip Terraform infrastructure setup"
    echo "  --skip-build               Skip Docker image builds"
    echo "  --skip-deploy              Skip Cloud Run deployment"
    echo "  -h, --help                 Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -p my-project-id"
    echo "  $0 -p my-project-id -e staging --skip-terraform"
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--project)
            PROJECT_ID="$2"
            shift 2
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        --skip-terraform)
            SKIP_TERRAFORM=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --skip-deploy)
            SKIP_DEPLOY=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Validate required parameters
if [[ -z "$PROJECT_ID" ]]; then
    echo -e "${RED}Error: Project ID is required${NC}"
    usage
fi

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    # Check if gcloud is installed and authenticated
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        log_error "Not authenticated with gcloud. Please run 'gcloud auth login'"
        exit 1
    fi
    
    # Check if terraform is installed
    if [[ "$SKIP_TERRAFORM" == false ]] && ! command -v terraform &> /dev/null; then
        log_error "Terraform is not installed. Please install it first."
        exit 1
    fi
    
    # Check if docker is installed
    if [[ "$SKIP_BUILD" == false ]] && ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    log_success "All dependencies are available"
}

setup_gcloud() {
    log_info "Setting up Google Cloud configuration..."
    
    # Set the project
    gcloud config set project "$PROJECT_ID"
    
    # Enable required APIs
    log_info "Enabling required Google Cloud APIs..."
    gcloud services enable \
        run.googleapis.com \
        cloudbuild.googleapis.com \
        sqladmin.googleapis.com \
        storage.googleapis.com \
        secretmanager.googleapis.com \
        aiplatform.googleapis.com \
        vpcaccess.googleapis.com \
        monitoring.googleapis.com \
        logging.googleapis.com
    
    log_success "Google Cloud configuration complete"
}

setup_terraform() {
    if [[ "$SKIP_TERRAFORM" == true ]]; then
        log_warning "Skipping Terraform setup"
        return
    fi
    
    log_info "Setting up Terraform infrastructure..."
    
    cd "$TERRAFORM_DIR"
    
    # Check if terraform.tfvars exists
    if [[ ! -f "terraform.tfvars" ]]; then
        log_error "terraform.tfvars not found. Please copy terraform.tfvars.example to terraform.tfvars and configure it."
        exit 1
    fi
    
    # Initialize Terraform
    terraform init
    
    # Plan the infrastructure
    log_info "Planning Terraform infrastructure..."
    terraform plan -var="project_id=$PROJECT_ID" -var="region=$REGION"
    
    # Ask for confirmation
    echo ""
    read -p "Do you want to apply these Terraform changes? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_warning "Terraform deployment cancelled"
        exit 0
    fi
    
    # Apply the infrastructure
    log_info "Applying Terraform infrastructure..."
    terraform apply -var="project_id=$PROJECT_ID" -var="region=$REGION" -auto-approve
    
    log_success "Terraform infrastructure deployed"
    cd "$PROJECT_ROOT"
}

build_images() {
    if [[ "$SKIP_BUILD" == true ]]; then
        log_warning "Skipping Docker image builds"
        return
    fi
    
    log_info "Building and pushing Docker images..."
    
    # Build and push backend image
    log_info "Building backend image..."
    cd "$PROJECT_ROOT/backend"
    docker build --target production -t "gcr.io/$PROJECT_ID/sales-order-backend:latest" .
    docker push "gcr.io/$PROJECT_ID/sales-order-backend:latest"
    
    # Build and push frontend image
    log_info "Building frontend image..."
    cd "$PROJECT_ROOT/frontend"
    docker build --target production -t "gcr.io/$PROJECT_ID/sales-order-frontend:latest" .
    docker push "gcr.io/$PROJECT_ID/sales-order-frontend:latest"
    
    log_success "Docker images built and pushed"
    cd "$PROJECT_ROOT"
}

deploy_services() {
    if [[ "$SKIP_DEPLOY" == true ]]; then
        log_warning "Skipping Cloud Run deployment"
        return
    fi
    
    log_info "Deploying services to Cloud Run..."
    
    # Deploy backend service
    log_info "Deploying backend service..."
    gcloud run deploy sales-order-backend-$ENVIRONMENT \
        --image "gcr.io/$PROJECT_ID/sales-order-backend:latest" \
        --platform managed \
        --region "$REGION" \
        --allow-unauthenticated \
        --service-account "sales-order-backend-sa@$PROJECT_ID.iam.gserviceaccount.com" \
        --set-env-vars "ENVIRONMENT=$ENVIRONMENT,GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
        --add-cloudsql-instances "$PROJECT_ID:$REGION:sales-order-db" \
        --cpu 2 \
        --memory 4Gi \
        --min-instances 1 \
        --max-instances 20 \
        --port 8000 \
        --concurrency 80 \
        --timeout 300 \
        --execution-environment gen2
    
    # Get backend URL
    BACKEND_URL=$(gcloud run services describe sales-order-backend-$ENVIRONMENT --region=$REGION --format='value(status.url)')
    log_info "Backend deployed at: $BACKEND_URL"
    
    # Deploy frontend service
    log_info "Deploying frontend service..."
    gcloud run deploy sales-order-frontend-$ENVIRONMENT \
        --image "gcr.io/$PROJECT_ID/sales-order-frontend:latest" \
        --platform managed \
        --region "$REGION" \
        --allow-unauthenticated \
        --service-account "sales-order-frontend-sa@$PROJECT_ID.iam.gserviceaccount.com" \
        --set-env-vars "BACKEND_URL=$BACKEND_URL,ENVIRONMENT=$ENVIRONMENT" \
        --cpu 1 \
        --memory 2Gi \
        --min-instances 1 \
        --max-instances 10 \
        --port 8080 \
        --concurrency 1000 \
        --timeout 60 \
        --execution-environment gen2
    
    # Get frontend URL
    FRONTEND_URL=$(gcloud run services describe sales-order-frontend-$ENVIRONMENT --region=$REGION --format='value(status.url)')
    
    log_success "Services deployed successfully"
    log_success "Frontend URL: $FRONTEND_URL"
    log_success "Backend URL: $BACKEND_URL"
}

run_health_checks() {
    log_info "Running health checks..."
    
    # Get service URLs
    BACKEND_URL=$(gcloud run services describe sales-order-backend-$ENVIRONMENT --region=$REGION --format='value(status.url)' 2>/dev/null || echo "")
    FRONTEND_URL=$(gcloud run services describe sales-order-frontend-$ENVIRONMENT --region=$REGION --format='value(status.url)' 2>/dev/null || echo "")
    
    if [[ -n "$BACKEND_URL" ]]; then
        log_info "Testing backend health..."
        if curl -f "$BACKEND_URL/health" > /dev/null 2>&1; then
            log_success "Backend health check passed"
        else
            log_warning "Backend health check failed"
        fi
    fi
    
    if [[ -n "$FRONTEND_URL" ]]; then
        log_info "Testing frontend health..."
        if curl -f "$FRONTEND_URL/health" > /dev/null 2>&1; then
            log_success "Frontend health check passed"
        else
            log_warning "Frontend health check failed"
        fi
    fi
}

setup_secrets() {
    log_info "Setting up secrets (you'll need to add the actual values)..."
    
    # Create secret placeholders if they don't exist
    gcloud secrets create openai-api-key --data-file=<(echo "REPLACE_WITH_ACTUAL_OPENAI_API_KEY") || true
    gcloud secrets create database-url-$ENVIRONMENT --data-file=<(echo "REPLACE_WITH_ACTUAL_DATABASE_URL") || true
    gcloud secrets create dynamics-config --data-file=<(echo "REPLACE_WITH_ACTUAL_DYNAMICS_CONFIG") || true
    
    log_warning "Remember to update the secrets with actual values:"
    log_warning "  gcloud secrets versions add openai-api-key --data-file=path/to/openai-key"
    log_warning "  gcloud secrets versions add database-url-$ENVIRONMENT --data-file=path/to/db-url"
    log_warning "  gcloud secrets versions add dynamics-config --data-file=path/to/dynamics-config"
}

# Main execution
main() {
    log_info "Starting deployment for Sales Order System"
    log_info "Project ID: $PROJECT_ID"
    log_info "Environment: $ENVIRONMENT"
    log_info "Region: $REGION"
    echo ""
    
    check_dependencies
    setup_gcloud
    setup_secrets
    setup_terraform
    build_images
    deploy_services
    run_health_checks
    
    echo ""
    log_success "🎉 Deployment completed successfully!"
    
    if [[ -n "$FRONTEND_URL" ]]; then
        echo ""
        echo "🌐 Your Sales Order System is now available at:"
        echo "   $FRONTEND_URL"
        echo ""
    fi
    
    log_info "Next steps:"
    echo "  1. Update secrets with actual values (see warnings above)"
    echo "  2. Configure Dynamics 365 integration when ready"
    echo "  3. Set up monitoring dashboards in Google Cloud Console"
    echo "  4. Configure DNS and custom domain if needed"
}

# Run main function
main
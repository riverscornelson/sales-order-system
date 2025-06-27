# Sales Order System - Infrastructure Deployment

This directory contains all the infrastructure configurations and deployment scripts for the Sales Order System on Google Cloud Platform.

## Overview

The infrastructure is designed for production deployment with:
- **Cloud Run** for containerized applications
- **Cloud SQL** for PostgreSQL database
- **Cloud Storage** for document and vector storage
- **Vertex AI** for embeddings and ML capabilities
- **Secret Manager** for secure credential storage
- **VPC networking** for secure communication
- **Cloud Monitoring** for observability

## Quick Start

### Prerequisites

1. **Google Cloud CLI** - [Install gcloud](https://cloud.google.com/sdk/docs/install)
2. **Docker** - [Install Docker](https://docs.docker.com/get-docker/)
3. **Terraform** - [Install Terraform](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)

### Authentication

```bash
# Authenticate with Google Cloud
gcloud auth login
gcloud auth configure-docker

# Set your project (replace with your actual project ID)
gcloud config set project YOUR_PROJECT_ID
```

### One-Command Deployment

```bash
# Deploy everything (infrastructure + application)
./deploy.sh -p YOUR_PROJECT_ID

# Deploy to staging environment
./deploy.sh -p YOUR_PROJECT_ID -e staging

# Deploy to specific region
./deploy.sh -p YOUR_PROJECT_ID -r europe-west1
```

### Step-by-Step Deployment

If you prefer more control, you can deploy in steps:

```bash
# 1. Infrastructure only
./deploy.sh -p YOUR_PROJECT_ID --skip-build --skip-deploy

# 2. Build and push images only
./deploy.sh -p YOUR_PROJECT_ID --skip-terraform --skip-deploy

# 3. Deploy services only
./deploy.sh -p YOUR_PROJECT_ID --skip-terraform --skip-build
```

## File Structure

```
infrastructure/
├── deploy.sh                    # Main deployment script
├── cloudbuild.yaml             # CI/CD pipeline configuration
├── cloud-run-backend.yaml      # Backend Cloud Run service config
├── cloud-run-frontend.yaml     # Frontend Cloud Run service config
├── terraform/                  # Infrastructure as Code
│   ├── main.tf                 # Main Terraform configuration
│   ├── variables.tf            # Variable definitions
│   ├── outputs.tf              # Output values
│   └── terraform.tfvars.example # Example variables file
└── README.md                   # This file
```

## Configuration

### Terraform Variables

Copy the example variables file and customize:

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your values:

```hcl
project_id = "your-gcp-project-id"
region     = "us-central1"
environment = "production"

# Database configuration
db_tier     = "db-custom-2-4096"  # Adjust based on needs
db_password = "your-secure-password"

# Monitoring
alert_email = "admin@yourdomain.com"

# Resource allocation
backend_cpu           = "2"
backend_memory        = "4Gi"
backend_min_instances = 1
backend_max_instances = 20
```

### Environment Variables

The system uses Google Secret Manager for sensitive configuration. After deployment, update these secrets:

```bash
# OpenAI API Key
echo "sk-your-actual-openai-key" | gcloud secrets versions add openai-api-key --data-file=-

# Database URL (auto-generated, but you can override)
echo "postgresql://username:password@host:port/database" | gcloud secrets versions add database-url-production --data-file=-

# Dynamics 365 Configuration (JSON format)
echo '{"tenant_id":"...","client_id":"...","client_secret":"...","resource_url":"..."}' | gcloud secrets versions add dynamics-config --data-file=-
```

## Architecture

### Network Architecture

```
Internet → Cloud Load Balancer → Cloud Run Services
                                      ↓
                              VPC Access Connector
                                      ↓
                               Private VPC Network
                                      ↓
                    Cloud SQL (Private IP) + Cloud Storage
```

### Security Features

- **Private networking** for database access
- **IAM service accounts** with minimal required permissions
- **Secret Manager** for sensitive data
- **VPC Access Connector** for secure Cloud Run to Cloud SQL communication
- **SSL/TLS** encryption in transit
- **Container security** with non-root users and minimal base images

### Monitoring & Observability

- **Cloud Monitoring** dashboards and alerts
- **Cloud Logging** for centralized log management
- **Health checks** for service availability
- **Error rate and latency alerting**

## Scaling Configuration

### Backend (FastAPI)

- **CPU**: 1-4 cores per instance
- **Memory**: 2-8 GB per instance
- **Instances**: 0-50 (auto-scaling)
- **Concurrency**: 80 requests per instance

### Frontend (Nginx)

- **CPU**: 1 core per instance
- **Memory**: 1-2 GB per instance
- **Instances**: 0-10 (auto-scaling)
- **Concurrency**: 1000 requests per instance

### Database (Cloud SQL)

- **Tier**: db-custom-2-4096 (2 vCPU, 4 GB RAM) for production
- **Storage**: 20 GB SSD with auto-resize
- **Backup**: Daily backups with 7-day retention
- **High Availability**: Regional configuration

## CI/CD Pipeline

The `cloudbuild.yaml` file defines a comprehensive CI/CD pipeline:

### Pipeline Stages

1. **Testing**
   - Backend unit tests with pytest
   - Frontend unit tests with Vitest
   - Linting and type checking

2. **Security**
   - Container vulnerability scanning
   - Security policy validation

3. **Building**
   - Multi-stage Docker builds
   - Image optimization and caching

4. **Deployment**
   - Cloud Run service deployment
   - Environment-specific configuration
   - Smoke testing

5. **Monitoring**
   - Health checks
   - Performance validation

### Triggering Deployments

```bash
# Manual trigger
gcloud builds submit --config=cloudbuild.yaml

# Automated via Git (setup required)
gcloud builds triggers create github \
  --repo-name=your-repo \
  --repo-owner=your-org \
  --branch-pattern="^main$" \
  --build-config=infrastructure/cloudbuild.yaml
```

## Troubleshooting

### Common Issues

**1. Authentication Errors**
```bash
gcloud auth login
gcloud auth configure-docker
```

**2. Terraform State Issues**
```bash
cd terraform
terraform init -reconfigure
```

**3. Cloud Run Deployment Timeout**
- Check container health endpoints
- Verify environment variables
- Review Cloud SQL connection settings

**4. Database Connection Issues**
- Ensure VPC Access Connector is created
- Verify Cloud SQL instance is running
- Check service account permissions

### Viewing Logs

```bash
# Backend logs
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=sales-order-backend-production" --limit=50

# Frontend logs
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=sales-order-frontend-production" --limit=50

# Build logs
gcloud builds log BUILD_ID
```

### Health Checks

```bash
# Backend health
curl https://your-backend-url.run.app/health

# Frontend health
curl https://your-frontend-url.run.app/health
```

## Cost Optimization

### Development Environment

For development/testing, use smaller instances:

```hcl
# In terraform.tfvars
db_tier = "db-f1-micro"
backend_min_instances = 0
frontend_min_instances = 0
```

### Production Environment

For production, consider:

- **Sustained Use Discounts** (automatic)
- **Committed Use Discounts** for predictable workloads
- **Cloud SQL read replicas** for read-heavy workloads
- **Cloud Storage lifecycle policies** for document retention

## Security Checklist

- [ ] Secrets stored in Secret Manager (not in code)
- [ ] Service accounts follow principle of least privilege
- [ ] Database uses private IP only
- [ ] VPC networking configured properly
- [ ] SSL/TLS enabled for all communication
- [ ] Container images run as non-root user
- [ ] Monitoring and alerting configured
- [ ] Backup and disaster recovery tested

## Support

For deployment issues:

1. Check the logs using the commands above
2. Review the [Google Cloud documentation](https://cloud.google.com/docs)
3. Verify all prerequisites are met
4. Ensure proper IAM permissions

## Next Steps

After successful deployment:

1. **Configure DNS** for custom domain
2. **Set up SSL certificates** for HTTPS
3. **Configure Dynamics 365** integration
4. **Set up monitoring dashboards**
5. **Test disaster recovery procedures**
6. **Implement backup verification**
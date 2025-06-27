# Sales Order System - Complete Deployment Guide

This document provides a comprehensive guide for deploying the Sales Order Entry System to Google Cloud Platform.

## 🎯 Overview

The Sales Order System is a modern multi-agent architecture designed to process customer orders from emails and PDFs. It features:

- **LangGraph Multi-Agent Workflow** for intelligent document processing
- **Semantic Search** with vector embeddings for parts matching
- **ERP Integration** with Microsoft Dynamics 365 (mockable for development)
- **Perplexity-style Streaming UI** with real-time progress visualization
- **Production-ready deployment** on Google Cloud Platform

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Google Cloud  │
│   (React)       │    │   (FastAPI)     │    │   Services      │
│                 │    │                 │    │                 │
│ • React 19      │◄──►│ • FastAPI       │◄──►│ • Cloud SQL     │
│ • TypeScript    │    │ • LangGraph     │    │ • Cloud Storage │
│ • TailwindCSS   │    │ • Vertex AI     │    │ • Cloud Run     │
│ • Framer Motion │    │ • OpenAI        │    │ • Monitoring    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

1. **Google Cloud Account** with billing enabled
2. **Google Cloud CLI** - [Install gcloud](https://cloud.google.com/sdk/docs/install)
3. **Docker** - [Install Docker](https://docs.docker.com/get-docker/)
4. **Terraform** - [Install Terraform](https://developer.hashicorp.com/terraform/install)

### 1. Authentication

```bash
# Authenticate with Google Cloud
gcloud auth login
gcloud auth configure-docker

# Set your project
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID
```

### 2. One-Command Deployment

```bash
# Clone and navigate to the project
git clone <repository-url>
cd sales-order-system

# Deploy everything
./infrastructure/deploy.sh -p $PROJECT_ID

# Set up monitoring
./infrastructure/setup-monitoring.sh -p $PROJECT_ID -e admin@yourcompany.com
```

That's it! 🎉 Your system should be live in ~15-20 minutes.

## 📋 Step-by-Step Deployment

If you prefer more control over the deployment process:

### Step 1: Infrastructure Setup

```bash
cd infrastructure/terraform

# Copy and configure variables
cp terraform.tfvars.example terraform.tfvars
vim terraform.tfvars  # Edit with your values

# Deploy infrastructure
terraform init
terraform plan
terraform apply
```

### Step 2: Build and Push Images

```bash
# Build backend
cd ../backend
docker build --target production -t gcr.io/$PROJECT_ID/sales-order-backend:latest .
docker push gcr.io/$PROJECT_ID/sales-order-backend:latest

# Build frontend
cd ../frontend
docker build --target production -t gcr.io/$PROJECT_ID/sales-order-frontend:latest .
docker push gcr.io/$PROJECT_ID/sales-order-frontend:latest
```

### Step 3: Deploy Services

```bash
# Deploy backend
gcloud run deploy sales-order-backend-production \
  --image gcr.io/$PROJECT_ID/sales-order-backend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

# Deploy frontend  
gcloud run deploy sales-order-frontend-production \
  --image gcr.io/$PROJECT_ID/sales-order-frontend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Step 4: Configure Secrets

```bash
# Add OpenAI API Key
echo "sk-your-openai-key" | gcloud secrets versions add openai-api-key --data-file=-

# Add database URL
echo "postgresql://user:pass@host:port/db" | gcloud secrets versions add database-url-production --data-file=-

# Add Dynamics 365 config (when ready)
echo '{"tenant_id":"...","client_id":"..."}' | gcloud secrets versions add dynamics-config --data-file=-
```

## 🔧 Configuration

### Environment Variables

The system uses Google Secret Manager for sensitive configuration:

| Secret Name | Description | Required |
|------------|-------------|----------|
| `openai-api-key` | OpenAI API key for embeddings and LLM | Yes |
| `database-url-production` | PostgreSQL connection string | Auto-generated |
| `dynamics-config` | Dynamics 365 configuration JSON | Optional |

### Application Settings

Key settings are configured via environment variables:

```bash
# Backend settings
ENVIRONMENT=production
GOOGLE_CLOUD_PROJECT=your-project-id
LOG_LEVEL=INFO
ERP_PROVIDER=mock  # Change to 'dynamics' when ready
EMBEDDING_PROVIDER=vertex
```

## 📊 Monitoring & Observability

The system includes comprehensive monitoring:

### Dashboards

- **Application Overview** - Request rates, latency, errors
- **Business Metrics** - Document processing, orders, ERP integration
- **Infrastructure** - Cloud Run, database, resource utilization
- **Error Tracking** - Error rates, types, service health

### Alerts

Pre-configured alerts for:

- High error rates (>5%)
- High latency (>5 seconds)
- Service outages
- Database connection issues
- Memory/CPU usage
- Security events

### Logs

Structured logging with:

- **Request tracing** with correlation IDs
- **Performance monitoring** with detailed metrics
- **Security logging** for suspicious activity
- **Business event tracking** for orders and documents

Access logs via:

```bash
# View backend logs
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=sales-order-backend-production" --limit=50

# View error logs only
gcloud logs read "resource.type=cloud_run_revision AND severity>=ERROR" --limit=20
```

## 🔒 Security

The deployment includes comprehensive security measures:

### Infrastructure Security

- **Private networking** for database access
- **VPC Access Connector** for secure Cloud Run to Cloud SQL communication
- **IAM service accounts** with minimal required permissions
- **Secret Manager** for sensitive data storage

### Application Security

- **Container security** with non-root users
- **Input validation** and sanitization
- **Rate limiting** on API endpoints
- **Security headers** in HTTP responses
- **Vulnerability scanning** in CI/CD pipeline

### Monitoring Security

- **Authentication failure tracking**
- **Suspicious activity detection**
- **Rate limiting breach alerts**
- **Security event logging**

## 🔄 CI/CD Pipeline

The system includes a comprehensive CI/CD pipeline via Cloud Build:

### Pipeline Stages

1. **Testing** - Unit tests, integration tests, linting
2. **Security** - Vulnerability scanning, security checks
3. **Building** - Multi-stage Docker builds with optimization
4. **Deployment** - Environment-specific deployments
5. **Verification** - Smoke tests and health checks

### Trigger Deployment

```bash
# Manual deployment
gcloud builds submit --config=infrastructure/cloudbuild.yaml

# Set up automatic triggers
gcloud builds triggers create github \
  --repo-name=sales-order-system \
  --repo-owner=your-org \
  --branch-pattern="^main$" \
  --build-config=infrastructure/cloudbuild.yaml
```

## 🧪 Testing

### Running Tests Locally

```bash
# Backend tests
cd backend
python -m pytest tests/ -v --cov=app

# Frontend tests
cd frontend
npm test
npm run test:e2e
```

### Production Testing

```bash
# Health checks
curl https://your-backend-url.run.app/health
curl https://your-frontend-url.run.app/health

# Load testing
ab -n 1000 -c 10 https://your-backend-url.run.app/api/v1/health
```

## 💰 Cost Optimization

### Development Environment

For cost-effective development:

```hcl
# In terraform.tfvars
db_tier = "db-f1-micro"
backend_min_instances = 0
frontend_min_instances = 0
```

### Production Environment

For production optimization:

- **Sustained Use Discounts** - Automatic for consistent usage
- **Committed Use Discounts** - For predictable workloads
- **Auto-scaling** - Scale to zero when not in use
- **Efficient resource allocation** - Right-sized instances

## 🚨 Troubleshooting

### Common Issues

**1. Authentication Errors**
```bash
gcloud auth login
gcloud auth configure-docker
```

**2. Database Connection Issues**
- Check VPC Access Connector configuration
- Verify Cloud SQL instance is running
- Check service account permissions

**3. Build Failures**
- Verify Docker is running
- Check image registry permissions
- Review Cloud Build logs

**4. High Memory Usage**
- Check for memory leaks in processing
- Consider increasing memory limits
- Review document processing efficiency

### Debug Commands

```bash
# Check service status
gcloud run services list

# View service details
gcloud run services describe sales-order-backend-production --region=us-central1

# Check logs
gcloud logs read "resource.type=cloud_run_revision" --limit=50

# Monitor metrics
gcloud monitoring metrics list --filter="metric.type:custom.googleapis.com/sales_order"
```

## 📈 Scaling

### Horizontal Scaling

The system auto-scales based on:

- **Request volume** - Automatic instance scaling
- **CPU utilization** - Additional instances when needed
- **Memory usage** - Scale up for memory-intensive operations

### Vertical Scaling

Adjust resources in `terraform.tfvars`:

```hcl
# For high-volume production
backend_cpu = "4"
backend_memory = "8Gi"
backend_max_instances = 50

# Database scaling
db_tier = "db-custom-4-8192"
```

## 🔄 Updates & Maintenance

### Application Updates

```bash
# Update via CI/CD
git push origin main

# Manual update
./infrastructure/deploy.sh -p $PROJECT_ID --skip-terraform
```

### Infrastructure Updates

```bash
# Update Terraform
cd infrastructure/terraform
terraform plan
terraform apply

# Update monitoring
./setup-monitoring.sh -p $PROJECT_ID -e admin@company.com
```

### Database Maintenance

- **Automated backups** - Daily with 7-day retention
- **Point-in-time recovery** - Available for last 7 days
- **High availability** - Regional configuration
- **Monitoring** - Performance and connection tracking

## 🎓 Next Steps

After successful deployment:

1. **Configure Custom Domain** - Set up DNS and SSL certificates
2. **Set Up Dynamics 365** - Replace mock ERP with real integration
3. **Configure User Authentication** - Add user management if needed
4. **Customize Business Rules** - Adjust processing logic for your needs
5. **Set Up Backup Verification** - Test disaster recovery procedures
6. **Performance Tuning** - Optimize based on actual usage patterns

## 📞 Support

For issues and questions:

1. **Check the logs** using the commands above
2. **Review monitoring dashboards** for system health
3. **Consult the troubleshooting section**
4. **Review Google Cloud documentation**

## 🎉 Success!

Your Sales Order Entry System should now be running in production with:

- ✅ **Multi-agent document processing**
- ✅ **Real-time streaming UI**
- ✅ **Comprehensive monitoring**
- ✅ **Production-grade security**
- ✅ **Auto-scaling infrastructure**
- ✅ **Automated CI/CD pipeline**

Welcome to the future of order processing! 🚀
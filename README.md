# 🚀 Sales Order Entry System

A modern multi-agent system for processing customer orders from emails and PDFs using LangGraph, OpenAI, and Google Cloud Platform.

![Sales Order System](https://img.shields.io/badge/Status-Production%20Ready-green?style=for-the-badge)
[![Deploy to Google Cloud](https://img.shields.io/badge/Deploy%20to-Google%20Cloud-4285F4?style=for-the-badge&logo=google-cloud)](./DEPLOYMENT.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

## ✨ Features

- **🤖 Multi-Agent Architecture** - LangGraph orchestration with specialized agents
- **🔍 Semantic Search** - Vector embeddings for intelligent parts matching
- **📧 Document Processing** - Email and PDF parsing with OCR capabilities
- **🔗 ERP Integration** - Microsoft Dynamics 365 with adapter pattern
- **⚡ Real-time UI** - Perplexity-style streaming interface
- **☁️ Cloud Native** - Production-ready deployment on Google Cloud
- **📊 Monitoring** - Comprehensive observability and alerting
- **🔒 Security** - Enterprise-grade security and compliance

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

- [Google Cloud CLI](https://cloud.google.com/sdk/docs/install)
- [Docker](https://docs.docker.com/get-docker/)
- [Terraform](https://developer.hashicorp.com/terraform/install)
- OpenAI API Key

### One-Command Deployment

```bash
# Clone the repository
git clone https://github.com/riverscornelson/sales-order-system.git
cd sales-order-system

# Deploy to Google Cloud
./infrastructure/deploy.sh -p YOUR_PROJECT_ID

# Set up monitoring
./infrastructure/setup-monitoring.sh -p YOUR_PROJECT_ID -e admin@yourcompany.com
```

### Local Development

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## 📋 System Components

### Backend (Python/FastAPI)
- **Supervisor Agent** - Workflow orchestration
- **Document Parser** - Email/PDF processing
- **Order Extractor** - Line item extraction
- **Semantic Search** - Parts matching
- **ERP Integration** - Dynamics 365 connector
- **Review Preparer** - Order validation

### Frontend (React/TypeScript)
- **Upload Component** - File upload interface
- **Processing Cards** - Real-time progress visualization
- **WebSocket Integration** - Live updates
- **Responsive Design** - Mobile-first approach

### Infrastructure (Google Cloud)
- **Cloud Run** - Containerized services
- **Cloud SQL** - PostgreSQL database
- **Cloud Storage** - Document storage
- **Vertex AI** - Embeddings and ML
- **Secret Manager** - Secure credentials
- **Cloud Monitoring** - Observability

## 🔧 Configuration

### Environment Variables

```bash
# OpenAI
OPENAI_API_KEY=sk-your-openai-key

# Google Cloud
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# ERP (Optional)
DYNAMICS_365_TENANT_ID=your-tenant-id
DYNAMICS_365_CLIENT_ID=your-client-id
DYNAMICS_365_CLIENT_SECRET=your-secret
```

### Terraform Configuration

```bash
cd infrastructure/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app

# Frontend tests
cd frontend
npm test
npm run test:e2e

# Integration tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 📊 Monitoring

The system includes comprehensive monitoring:

- **Application Dashboards** - Request rates, latency, errors
- **Business Metrics** - Order processing, document analysis
- **Infrastructure Monitoring** - Resource utilization, health
- **Alert Policies** - Automated incident response

## 🔒 Security

- **Private networking** for database access
- **IAM service accounts** with minimal permissions
- **Secret Manager** for sensitive data
- **Container security** with non-root users
- **Input validation** and rate limiting

## 📚 Documentation

- [**Deployment Guide**](DEPLOYMENT.md) - Complete deployment instructions
- [**Infrastructure Guide**](infrastructure/README.md) - Infrastructure details
- [**API Documentation**](http://localhost:8000/docs) - Interactive API docs

## Development Progress

- ✅ **Phase 1**: Project Foundation & Architecture Setup
- ✅ **Phase 2**: Core Agent Development (LangGraph Multi-Agent)
- ✅ **Phase 3**: Semantic Search Implementation (Vector Embeddings)
- ✅ **Phase 4**: ERP Integration Layer (Dynamics 365 Adapter)
- ✅ **Phase 5**: Perplexity-Style Frontend (Streaming UI)
- ✅ **Phase 6**: System Integration & Testing (Full Test Suite)
- ✅ **Phase 7**: Deployment & Monitoring (Production Ready)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Built with ❤️ for modern sales order processing**
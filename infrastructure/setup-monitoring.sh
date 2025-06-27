#!/bin/bash

# Setup monitoring and alerting for Sales Order System
# This script creates monitoring dashboards, alert policies, and notification channels

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITORING_DIR="$SCRIPT_DIR/monitoring"

# Default values
PROJECT_ID=""
ALERT_EMAIL=""
ALERT_SMS=""

# Usage function
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -p, --project PROJECT_ID    Google Cloud Project ID (required)"
    echo "  -e, --email EMAIL           Alert email address (required)"
    echo "  -s, --sms PHONE            Alert SMS phone number (optional)"
    echo "  -h, --help                 Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -p my-project-id -e admin@company.com"
    echo "  $0 -p my-project-id -e admin@company.com -s +1234567890"
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--project)
            PROJECT_ID="$2"
            shift 2
            ;;
        -e|--email)
            ALERT_EMAIL="$2"
            shift 2
            ;;
        -s|--sms)
            ALERT_SMS="$2"
            shift 2
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

if [[ -z "$ALERT_EMAIL" ]]; then
    echo -e "${RED}Error: Alert email is required${NC}"
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

# Check dependencies
check_dependencies() {
    log_info "Checking dependencies..."
    
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI is not installed. Please install it first."
        exit 1
    fi
    
    if ! command -v jq &> /dev/null; then
        log_error "jq is not installed. Please install it first."
        exit 1
    fi
    
    # Check authentication
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        log_error "Not authenticated with gcloud. Please run 'gcloud auth login'"
        exit 1
    fi
    
    log_success "All dependencies are available"
}

# Set up project
setup_project() {
    log_info "Setting up project configuration..."
    
    gcloud config set project "$PROJECT_ID"
    
    # Enable required APIs
    log_info "Enabling monitoring API..."
    gcloud services enable monitoring.googleapis.com
    
    log_success "Project configuration complete"
}

# Create notification channels
create_notification_channels() {
    log_info "Creating notification channels..."
    
    # Create email notification channel
    EMAIL_CHANNEL_CONFIG=$(cat <<EOF
{
  "type": "email",
  "displayName": "Sales Order System - Email Alerts",
  "description": "Email notifications for Sales Order System alerts",
  "labels": {
    "email_address": "$ALERT_EMAIL"
  },
  "enabled": true
}
EOF
)
    
    EMAIL_CHANNEL_ID=$(echo "$EMAIL_CHANNEL_CONFIG" | gcloud alpha monitoring channels create --format="value(name)" || true)
    log_success "Email notification channel created: $EMAIL_CHANNEL_ID"
    
    # Create SMS notification channel if phone number provided
    SMS_CHANNEL_ID=""
    if [[ -n "$ALERT_SMS" ]]; then
        SMS_CHANNEL_CONFIG=$(cat <<EOF
{
  "type": "sms",
  "displayName": "Sales Order System - SMS Alerts",
  "description": "SMS notifications for critical Sales Order System alerts",
  "labels": {
    "number": "$ALERT_SMS"
  },
  "enabled": true
}
EOF
)
        
        SMS_CHANNEL_ID=$(echo "$SMS_CHANNEL_CONFIG" | gcloud alpha monitoring channels create --format="value(name)" || true)
        log_success "SMS notification channel created: $SMS_CHANNEL_ID"
    fi
    
    # Export channel IDs for alert creation
    export EMAIL_CHANNEL_ID
    export SMS_CHANNEL_ID
}

# Create alert policies
create_alert_policies() {
    log_info "Creating alert policies..."
    
    # High Error Rate Alert
    log_info "Creating high error rate alert..."
    cat <<EOF | gcloud alpha monitoring policies create --policy-from-file=-
displayName: "Sales Order System - High Error Rate"
documentation:
  content: |
    This alert triggers when the error rate exceeds 5% over a 5-minute window.
    
    ## Immediate Actions:
    1. Check application logs for recent errors
    2. Verify service health status
    3. Check Cloud Run instance health
  mimeType: "text/markdown"

conditions:
  - displayName: "HTTP Error Rate > 5%"
    conditionThreshold:
      filter: |
        metric.type="custom.googleapis.com/sales_order/counter/http_requests_errors_total"
        resource.type="cloud_run_revision"
      aggregations:
        - alignmentPeriod: "300s"
          perSeriesAligner: "ALIGN_RATE"
          crossSeriesReducer: "REDUCE_SUM"
      comparison: "COMPARISON_GREATER_THAN"
      thresholdValue: 0.05
      duration: "300s"
      trigger:
        count: 1

combiner: "OR"
enabled: true

notificationChannels:
  - "$EMAIL_CHANNEL_ID"

alertStrategy:
  autoClose: "1800s"
  notificationRateLimit:
    period: "900s"
EOF

    # High Latency Alert
    log_info "Creating high latency alert..."
    cat <<EOF | gcloud alpha monitoring policies create --policy-from-file=-
displayName: "Sales Order System - High Response Time"
documentation:
  content: |
    This alert triggers when average response time exceeds 5 seconds.
    
    ## Immediate Actions:
    1. Check if services are under high load
    2. Verify database performance
    3. Check for stuck requests
  mimeType: "text/markdown"

conditions:
  - displayName: "Average Response Time > 5s"
    conditionThreshold:
      filter: |
        metric.type="custom.googleapis.com/sales_order/histogram/http_request_duration_seconds"
        resource.type="cloud_run_revision"
      aggregations:
        - alignmentPeriod: "300s"
          perSeriesAligner: "ALIGN_MEAN"
          crossSeriesReducer: "REDUCE_MEAN"
      comparison: "COMPARISON_GREATER_THAN"
      thresholdValue: 5.0
      duration: "600s"
      trigger:
        count: 1

combiner: "OR"
enabled: true

notificationChannels:
  - "$EMAIL_CHANNEL_ID"
EOF

    # Service Down Alert
    log_info "Creating service down alert..."
    NOTIFICATION_CHANNELS="[\"$EMAIL_CHANNEL_ID\"]"
    if [[ -n "$SMS_CHANNEL_ID" ]]; then
        NOTIFICATION_CHANNELS="[\"$EMAIL_CHANNEL_ID\", \"$SMS_CHANNEL_ID\"]"
    fi
    
    cat <<EOF | gcloud alpha monitoring policies create --policy-from-file=-
displayName: "Sales Order System - Service Down"
documentation:
  content: |
    This alert triggers when the service health check fails.
    
    ## Immediate Actions:
    1. Check Cloud Run service status
    2. Verify deployment status
    3. Check for infrastructure issues
  mimeType: "text/markdown"

conditions:
  - displayName: "Application Health Check Failed"
    conditionThreshold:
      filter: |
        metric.type="custom.googleapis.com/sales_order/gauge/application_health"
      aggregations:
        - alignmentPeriod: "60s"
          perSeriesAligner: "ALIGN_MEAN"
          crossSeriesReducer: "REDUCE_MEAN"
      comparison: "COMPARISON_LESS_THAN"
      thresholdValue: 1.0
      duration: "180s"
      trigger:
        count: 1

combiner: "OR"
enabled: true

notificationChannels: $NOTIFICATION_CHANNELS

alertStrategy:
  autoClose: "600s"
EOF

    # Database Issues Alert
    log_info "Creating database issues alert..."
    cat <<EOF | gcloud alpha monitoring policies create --policy-from-file=-
displayName: "Sales Order System - Database Connection Issues"
documentation:
  content: |
    This alert triggers when database operations have high error rates.
    
    ## Immediate Actions:
    1. Check Cloud SQL instance status
    2. Verify connection pool settings
    3. Check for connection leaks
  mimeType: "text/markdown"

conditions:
  - displayName: "Database Error Rate > 10%"
    conditionThreshold:
      filter: |
        metric.type="custom.googleapis.com/sales_order/counter/database_operations_errors_total"
      aggregations:
        - alignmentPeriod: "300s"
          perSeriesAligner: "ALIGN_RATE"
          crossSeriesReducer: "REDUCE_SUM"
      comparison: "COMPARISON_GREATER_THAN"
      thresholdValue: 0.1
      duration: "300s"
      trigger:
        count: 1

combiner: "OR"
enabled: true

notificationChannels:
  - "$EMAIL_CHANNEL_ID"
EOF

    log_success "Alert policies created"
}

# Create custom metrics (metadata only)
create_custom_metrics() {
    log_info "Creating custom metric descriptors..."
    
    # This creates the metric descriptors so they appear in the monitoring console
    # The actual metrics will be sent by the application
    
    local metrics=(
        "counter/http_requests_total"
        "counter/http_requests_errors_total"
        "histogram/http_request_duration_seconds"
        "counter/agent_operations_total"
        "counter/agent_operations_errors_total"
        "histogram/agent_operation_duration_seconds"
        "counter/documents_processed_total"
        "counter/document_processing_errors_total"
        "counter/orders_processed_total"
        "counter/erp_operations_total"
        "counter/erp_operations_errors_total"
        "gauge/application_health"
        "counter/database_operations_total"
        "counter/database_operations_errors_total"
    )
    
    for metric in "${metrics[@]}"; do
        log_info "Creating metric descriptor: $metric"
        
        # Determine metric kind and value type based on prefix
        case $metric in
            counter/*)
                METRIC_KIND="CUMULATIVE"
                VALUE_TYPE="INT64"
                ;;
            histogram/*)
                METRIC_KIND="CUMULATIVE"
                VALUE_TYPE="DISTRIBUTION"
                ;;
            gauge/*)
                METRIC_KIND="GAUGE"
                VALUE_TYPE="DOUBLE"
                ;;
        esac
        
        cat <<EOF | gcloud logging metrics create "${metric//\//_}" --config-from-file=- || true
filter: "jsonPayload.metric_type=\"$metric\""
description: "Custom metric for Sales Order System: $metric"
labelExtractors:
  service_name: "EXTRACT(resource.labels.service_name)"
metricDescriptor:
  metricKind: "$METRIC_KIND"
  valueType: "$VALUE_TYPE"
  displayName: "Sales Order - ${metric//\// }"
EOF
    done
    
    log_success "Custom metric descriptors created"
}

# Create monitoring dashboard
create_dashboard() {
    log_info "Creating monitoring dashboard..."
    
    # Create a comprehensive dashboard
    cat <<EOF | gcloud monitoring dashboards create --config-from-file=-
displayName: "Sales Order System - Overview"
mosaicLayout:
  tiles:
    - width: 6
      height: 4
      widget:
        title: "Request Rate (requests/min)"
        scorecard:
          timeSeriesQuery:
            timeSeriesFilter:
              filter: 'resource.type="cloud_run_revision" AND resource.labels.service_name=~"sales-order-.*"'
              aggregation:
                alignmentPeriod: "60s"
                perSeriesAligner: "ALIGN_RATE"
                crossSeriesReducer: "REDUCE_SUM"
          sparkChartView:
            sparkChartType: "SPARK_LINE"
    
    - width: 6
      height: 4
      xPos: 6
      widget:
        title: "Error Rate (%)"
        scorecard:
          timeSeriesQuery:
            timeSeriesFilter:
              filter: 'resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/request_count" AND resource.labels.service_name=~"sales-order-.*"'
              aggregation:
                alignmentPeriod: "60s"
                perSeriesAligner: "ALIGN_RATE"
                crossSeriesReducer: "REDUCE_SUM"
                groupByFields: ["metric.label.response_code_class"]
          sparkChartView:
            sparkChartType: "SPARK_BAR"
    
    - width: 12
      height: 4
      yPos: 4
      widget:
        title: "Response Time (ms)"
        xyChart:
          dataSets:
            - timeSeriesQuery:
                timeSeriesFilter:
                  filter: 'resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/request_latencies" AND resource.labels.service_name=~"sales-order-.*"'
                  aggregation:
                    alignmentPeriod: "60s"
                    perSeriesAligner: "ALIGN_MEAN"
                    crossSeriesReducer: "REDUCE_MEAN"
                    groupByFields: ["resource.label.service_name"]
              plotType: "LINE"
          yAxis:
            label: "Latency (ms)"
    
    - width: 6
      height: 4
      yPos: 8
      widget:
        title: "Container CPU Utilization"
        xyChart:
          dataSets:
            - timeSeriesQuery:
                timeSeriesFilter:
                  filter: 'resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/container/cpu/utilizations" AND resource.labels.service_name=~"sales-order-.*"'
                  aggregation:
                    alignmentPeriod: "60s"
                    perSeriesAligner: "ALIGN_MEAN"
                    crossSeriesReducer: "REDUCE_MEAN"
                    groupByFields: ["resource.label.service_name"]
              plotType: "LINE"
          yAxis:
            label: "CPU %"
    
    - width: 6
      height: 4
      xPos: 6
      yPos: 8
      widget:
        title: "Container Memory Utilization"
        xyChart:
          dataSets:
            - timeSeriesQuery:
                timeSeriesFilter:
                  filter: 'resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/container/memory/utilizations" AND resource.labels.service_name=~"sales-order-.*"'
                  aggregation:
                    alignmentPeriod: "60s"
                    perSeriesAligner: "ALIGN_MEAN"
                    crossSeriesReducer: "REDUCE_MEAN"
                    groupByFields: ["resource.label.service_name"]
              plotType: "LINE"
          yAxis:
            label: "Memory %"
EOF
    
    log_success "Monitoring dashboard created"
}

# Create log-based metrics
create_log_metrics() {
    log_info "Creating log-based metrics..."
    
    # Create metrics based on structured logs
    gcloud logging metrics create error_log_count \
        --description="Count of error logs from Sales Order System" \
        --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name=~"sales-order-.*" AND severity="ERROR"' || true
    
    gcloud logging metrics create security_events \
        --description="Security-related events from Sales Order System" \
        --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name=~"sales-order-.*" AND jsonPayload.logger_name="security"' || true
    
    log_success "Log-based metrics created"
}

# Main execution
main() {
    log_info "Setting up monitoring for Sales Order System"
    log_info "Project ID: $PROJECT_ID"
    log_info "Alert Email: $ALERT_EMAIL"
    if [[ -n "$ALERT_SMS" ]]; then
        log_info "Alert SMS: $ALERT_SMS"
    fi
    echo ""
    
    check_dependencies
    setup_project
    create_notification_channels
    create_custom_metrics
    create_log_metrics
    create_alert_policies
    create_dashboard
    
    echo ""
    log_success "🎉 Monitoring setup completed successfully!"
    echo ""
    log_info "Next steps:"
    echo "  1. Visit the Google Cloud Console Monitoring section"
    echo "  2. Review the created dashboards and alerts"
    echo "  3. Test alert notifications"
    echo "  4. Customize thresholds as needed"
    echo ""
    log_info "Dashboard URL:"
    echo "  https://console.cloud.google.com/monitoring/dashboards?project=$PROJECT_ID"
    echo ""
    log_info "Alert Policies URL:"
    echo "  https://console.cloud.google.com/monitoring/alerting/policies?project=$PROJECT_ID"
}

# Run main function
main
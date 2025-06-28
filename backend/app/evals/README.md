# Sales Order Intelligence Evaluation System

## Overview

This evaluation framework provides comprehensive assessment of the Sales Order Intelligence system with a focus on **ERP JSON accuracy as the primary objective** (40% of total score). The system is compatible with OpenAI's Evals API structure for consistency and integration with analysis tools.

## Scoring Breakdown

- **ERP Accuracy: 40%** (PRIMARY) - How accurately the system generates ERP-compatible JSON
- **Reasoning Quality: 20%** - Quality of AI reasoning chains and decision-making
- **Compliance: 20%** - Adherence to business rules and standards
- **Performance: 20%** - Processing speed and resource efficiency

## Key Features

- ✅ OpenAI Evals API compatibility
- ✅ Comprehensive ERP JSON accuracy scoring
- ✅ Standardized JSONL input/output format
- ✅ Detailed error handling and logging
- ✅ Flexible configuration management
- ✅ Human-readable and machine-readable reports
- ✅ Single sample and batch evaluation support

## Quick Start

### Basic Usage

```python
from app.evals import run_evaluation, EvaluationConfig

# Run evaluation with default configuration
metrics = run_evaluation(
    jsonl_path="data/evaluation/test_samples.jsonl",
    evaluation_id="production_test_v1"
)

print(f"ERP Accuracy: {metrics.mean_accuracy:.3f}")
print(f"Overall Score: {metrics.mean_score:.3f}")
```

### Custom Configuration

```python
from app.evals import run_evaluation, EvaluationConfig

# Create custom configuration with higher ERP focus
config = EvaluationConfig(
    erp_accuracy_weight=0.50,  # Increase ERP weight
    min_erp_accuracy_threshold=0.80,
    target_erp_accuracy=0.95
)

metrics = run_evaluation(
    jsonl_path="data/evaluation/test_samples.jsonl",
    config=config,
    evaluation_id="high_erp_focus_test"
)
```

## Input Data Format

Evaluation data should be in JSONL format with the following structure:

```json
{
  "input": {
    "document_content": "PURCHASE ORDER\nAcme Corp\nPart: 12345-ABC\nDescription: Widget Assembly\nQuantity: 10\nUnit Price: $25.00",
    "document_type": "pdf",
    "additional_context": {
      "customer_priority": "standard"
    }
  },
  "expected_output": {
    "erp_json": {
      "customer_company_name": "Acme Corp",
      "customer_contact_name": "Unknown",
      "customer_email": "unknown@example.com",
      "customer_phone": "Unknown",
      "customer_id": "ACME001",
      "item1_number": 1,
      "item1_description": "Widget Assembly",
      "item1_quantity": 10,
      "item1_material": "Unknown",
      "item1_unit_price": 25.00,
      "item1_specifications": "Part: 12345-ABC",
      "item2_number": 0,
      "item2_description": "None",
      "item2_quantity": 0,
      "item2_material": "None",
      "item2_unit_price": 0.0,
      "item2_specifications": "None",
      "item3_number": 0,
      "item3_description": "None",
      "item3_quantity": 0,
      "item3_material": "None",
      "item3_unit_price": 0.0,
      "item3_specifications": "None",
      "order_date": "2024-06-28",
      "delivery_date": "Unknown",
      "priority": "MEDIUM",
      "payment_terms": "Unknown",
      "special_instructions": "None",
      "total_amount": 250.00,
      "order_id": "ORD-2024-001",
      "total_line_items": 1
    },
    "reasoning": [
      "Identified customer as 'Acme Corp'",
      "Extracted part number '12345-ABC'",
      "Parsed quantity as 10 units"
    ]
  }
}
```

## ERP Accuracy Components

The ERP accuracy score (40% of total) includes:

### Structural Accuracy (20%)
- JSON schema compliance
- Required field presence
- Data type correctness

### Business Logic Accuracy (60%)
- Line items parsing with flat structure (25%)
- Material field consistency (15%)
- Pricing calculations (10%)
- Quantity parsing (10%)

### ERP Integration (20%)
- Field mapping correctness
- Business rules compliance

## Configuration

### Environment Variables

```bash
# Evaluation weights
EVAL_ERP_WEIGHT=0.40
EVAL_REASONING_WEIGHT=0.20
EVAL_COMPLIANCE_WEIGHT=0.20
EVAL_PERFORMANCE_WEIGHT=0.20

# Thresholds
EVAL_MIN_ERP_THRESHOLD=0.70
EVAL_TARGET_ERP_ACCURACY=0.90
EVAL_MAX_PROCESSING_TIME=2000
EVAL_TARGET_PROCESSING_TIME=500

# Model settings
EVAL_MODEL=gpt-4.1
EVAL_API_TYPE=responses_api
EVAL_USE_FLAT_MODELS=true
EVAL_DETAILED_LOGGING=true
```

### Configuration Files

Create configuration templates:

```python
from app.evals import create_config_template

# Create a template configuration file
template_path = create_config_template("production")
# Edit the file and load it:
config = EvaluationConfig.from_file(template_path)
```

## Detailed Usage

### EvaluationRunner for Advanced Control

```python
from app.evals import EvaluationRunner, EvaluationConfig

# Create configuration
config = EvaluationConfig(
    erp_accuracy_weight=0.45,
    detailed_logging=True
)

# Create runner with custom output directory
runner = EvaluationRunner(
    config=config,
    output_dir="results/detailed_evaluation"
)

# Validate data first
validation_result = runner.validate_evaluation_data("data/test.jsonl")
print(f"Valid samples: {validation_result['valid_samples']}")

# Run evaluation
metrics = runner.run_evaluation_from_jsonl(
    jsonl_path="data/test.jsonl",
    evaluation_id="detailed_test"
)
```

### Single Sample Evaluation

```python
from app.evals import EvaluationRunner

runner = EvaluationRunner()

sample = {
    "input": {
        "document_content": "Order details...",
        "document_type": "pdf"
    },
    "expected_output": {
        "erp_json": {...},
        "reasoning": [...]
    }
}

result = runner.run_single_sample_evaluation(
    sample=sample,
    sample_id="test_001"
)

print(f"Score: {result.score:.3f}")
print(f"ERP Accuracy: {result.accuracy:.3f}")
```

## Output Structure

### Metrics Object

```python
{
    "total_samples": 100,
    "successful_samples": 95,
    "failed_samples": 5,
    "success_rate": 0.95,
    "mean_score": 0.842,
    "mean_accuracy": 0.876,  # ERP accuracy (primary metric)
    "component_metrics": {
        "erp_accuracy_mean": 0.876,
        "reasoning_quality_mean": 0.823,
        "compliance_mean": 0.891,
        "performance_mean": 0.745
    },
    "mean_duration_ms": 1247.3
}
```

### Generated Reports

- `{evaluation_id}_results.jsonl` - Detailed results for each sample
- `{evaluation_id}_metrics.json` - Aggregate metrics
- `evaluation_report.json` - Comprehensive analysis
- `evaluation_summary.md` - Human-readable summary

## Error Handling

The system provides comprehensive error handling:

- **Input validation** - Validates JSONL structure and required fields
- **Processing errors** - Captures and reports processing failures
- **Configuration errors** - Validates configuration parameters
- **Graceful degradation** - Continues evaluation even with some failed samples

## Integration Notes

### OpenAI Evals Compatibility

This system follows OpenAI's Evals API structure:

- `eval_sample()` method for individual sample evaluation
- `get_metrics()` for aggregate metrics calculation
- JSONL input/output format
- Standardized result structure

### Performance Considerations

- Evaluations can be resource-intensive
- Consider batching large datasets
- Monitor memory usage for large evaluation runs
- Use `detailed_logging=False` for production runs

## Examples

See `example_evaluation.py` for comprehensive usage examples including:

- Basic evaluation workflow
- Custom configuration
- Single sample evaluation
- Data validation
- Configuration templates

## Directory Structure

```
app/evals/
├── __init__.py           # Main module exports
├── base_eval.py          # OpenAI Evals compatible base class
├── sales_order_eval.py   # Main evaluation implementation
├── data_structures.py    # Score components and configuration
├── config.py            # Configuration management
├── runner.py            # High-level evaluation runner
└── README.md            # This documentation
```

## Contributing

When extending the evaluation system:

1. Maintain OpenAI Evals compatibility
2. Keep ERP accuracy as the primary focus (40% weight)
3. Add comprehensive error handling
4. Include detailed logging
5. Update documentation and examples

## Troubleshooting

### Common Issues

1. **Configuration validation errors** - Check weight sum equals 1.0
2. **JSONL format errors** - Validate input file format
3. **Missing expected_output** - Ensure reference data is complete
4. **Processing timeouts** - Adjust timeout thresholds in configuration

### Debugging

Enable detailed logging:

```python
config = EvaluationConfig(detailed_logging=True)
```

Check evaluation logs in the output directory: `evaluation.log`
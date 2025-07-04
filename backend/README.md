# Sales Order Processing System

**Multi-Agent AI Workflow for Processing Customer Orders with OpenAI Responses API**

This system uses AI agents with OpenAI's latest Responses API and gpt-4.1 to automatically extract, search, and match line items from customer order documents (emails, PDFs, text files) against a parts catalog using flat structured outputs for maximum compatibility.

## 🚀 Quick Start

```bash
# 1. Set up environment
export OPENAI_API_KEY='your-key-here'

# 2. Process a single order
python sales_cli.py examples/sample_order_1.txt

# 3. Run tests
python test_workflow.py --all
```

## 📁 Project Structure

```
sales-order-system/backend/
├── sales_cli.py              # Main CLI tool
├── test_workflow.py          # Consolidated test runner
├── app/                      # Core AI agents and services
│   ├── agents/              # Multi-agent workflow components
│   ├── services/            # Parts catalog, vector search, etc.
│   └── models/              # Data schemas
├── examples/                # Sample order files
├── data/                    # Parts catalog and vectors
└── archived/                # Previous versions and experiments
```

## 🤖 How It Works

The system processes orders through 5 AI-powered stages using OpenAI Responses API:

1. **Document Analysis** - Parses input text/files
2. **Order Extraction** - gpt-4.1 extracts customer info and line items using flat structured outputs
3. **Parts Search** - Semantic search through parts catalog
4. **Part Matching** - gpt-4.1 selects best matches with reasoning using flat models
5. **Order Assembly** - Compiles final order with confidence scoring, ready for ERP conversion

## 💻 Usage

### Process Single File
```bash
python sales_cli.py path/to/order.txt
```

### Test All Examples
```bash
python test_workflow.py --all
```

### Health Check
```bash
python test_workflow.py --health
```

### View Results
After processing, check the `test_results/` directory for detailed JSON outputs at each stage.

## 🎯 Output Files

Each processed order creates structured outputs using flat models:
- `00_input.txt` - Original input
- `01_document_analysis.json` - Document metadata
- `02_extracted_order.json` - Flat structured order data (FlatOrderData)
- `03_search_results.json` - Search results for each line item
- `04_part_matches.json` - AI part matching results (FlatPartMatch)
- `05_assembled_order.json` - Final ERP-ready order (FlatERPOrder)
- `06_final_results.json` - Complete workflow summary with gpt-4.1 metadata

## 🔧 Configuration

### Environment Variables
- `OPENAI_API_KEY` - Required for gpt-4.1 and Responses API functionality
- `DATABASE_URL` - SQLite database path (optional)

### Files
- `.env` - Environment configuration
- `data/parts_catalog.csv` - Parts database
- `data/vectors/` - Vector embeddings for search

## 📊 Example Results

```json
{
  "total_line_items": 3,
  "successful_matches": 2,
  "confidence_score": 0.75,
  "approval_required": true,
  "model": "gpt-4.1",
  "api": "responses_api",
  "flat_models_used": true
}
```

## 🧪 Testing

Working test results are preserved in `examples/test_results/working_examples/`

For debugging, check:
- Console output during processing
- JSON files in output directories
- Previous working results in examples

## 🗂️ Archived Components

Non-essential components have been moved to `archived/`:
- Frontend React application
- Cloud deployment infrastructure  
- Experimental test scripts
- Old documentation

## 📝 Notes

- **OpenAI API key required** for gpt-4.1 and Responses API functionality
- **Flat structured outputs** ensure maximum compatibility with Responses API requirements
- **ERP-ready format** - outputs can be post-processed for any ERP system
- Processing time varies with document complexity (typically 30-120 seconds)
- All intermediate results are saved for debugging and refinement

## 🔄 Migration to Flat Models

This system has been updated to use flat Pydantic models for compatibility with OpenAI's Responses API:
- **FlatERPOrder** - ERP-ready order structure
- **FlatOrderAnalysis** - Customer and emergency analysis
- **FlatPartMatch** - Part matching results
- **FlatOrderData** - Order extraction results

All complex nested models have been replaced with flat alternatives that avoid `allOf` JSON Schema constructs.
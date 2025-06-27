# Enhanced Multi-Agent Sales Order Processing System
## Design Document v2.0

### Overview
This document outlines the enhanced agent flow that processes sales orders at the individual line item level, providing more accurate part matching and better visibility into the processing pipeline.

---

## Current vs. Enhanced Flow

### Current Flow (Simplified)
```
Document → Order Extractor → Semantic Search → ERP → Review
```

### Enhanced Flow (Line Item Focused)
```
Document → Order Extractor → Line Item Processor → Matching Agent → Assembly Agent → ERP → Review
                    ↓
            [Line Item 1, 2, 3...]
                    ↓
            Semantic Search (per item)
                    ↓
            Part Candidates (per item)
```

---

## Agent Flow Design

### 1. Document Parser Agent (Unchanged)
**Purpose**: Extract and analyze document structure
**Input**: Raw document content
**Output**: Document metadata and structured text

### 2. Order Extractor Agent (Enhanced)
**Purpose**: Extract customer info and individual line items with exact text
**Input**: Parsed document
**Output**: Structured order with line items

```json
{
  "order_metadata": {
    "customer": "TechManufacturing Solutions",
    "contact_person": "Mike Thompson", 
    "email": "m.thompson@techmanufacturing.com",
    "po_number": "P-2024-001",
    "priority": "HIGH",
    "delivery_date": "2024-03-15",
    "projects": ["PROJECT PHOENIX", "PROJECT TITAN"]
  },
  "line_items": [
    {
      "line_id": "L001",
      "project": "PROJECT PHOENIX",
      "raw_text": "Titanium Grade 5 (6Al-4V) sheets - Thickness: 0.125\" (±0.005\") - Dimensions: 24\" x 36\" - Quantity: 12 pieces - Surface finish: Mill finish acceptable - Material cert required (DFARS compliant)",
      "extracted_specs": {
        "material_grade": "Titanium Grade 5 (6Al-4V)",
        "form": "sheets",
        "thickness": "0.125",
        "thickness_tolerance": "±0.005",
        "length": "24",
        "width": "36", 
        "quantity": 12,
        "units": "inches",
        "surface_finish": "Mill finish",
        "certifications": ["DFARS compliant", "Material cert required"]
      },
      "urgency": "HIGH",
      "special_requirements": ["DFARS compliant", "Material cert required"]
    },
    {
      "line_id": "L002", 
      "project": "PROJECT PHOENIX",
      "raw_text": "Aluminum 7075-T651 rectangular bars - Cross section: 2.5\" x 4.0\" - Length: 72\" each - Qty: 8 bars - Need material certs and test reports",
      "extracted_specs": {
        "material_grade": "Aluminum 7075-T651",
        "form": "rectangular bars",
        "width": "2.5",
        "height": "4.0",
        "length": "72",
        "quantity": 8,
        "units": "inches",
        "certifications": ["material certs", "test reports"]
      },
      "urgency": "HIGH",
      "special_requirements": ["material certs", "test reports"]
    }
  ],
  "delivery_instructions": {
    "default_address": "TechManufacturing Solutions",
    "special_shipping": {
      "PROJECT TITAN": "Marine Systems Inc, 1500 Harbor Drive, Newport News, VA"
    }
  }
}
```

### 3. Line Item Processing Agent (New)
**Purpose**: Process each line item individually through the pipeline
**Input**: Order with line items
**Output**: Line items with processing status

**Process Flow**:
1. Takes each line item from order
2. Initiates parallel processing for each item
3. Tracks progress and status of each item
4. Manages dependencies between line items

**State Tracking**:
```json
{
  "line_id": "L001",
  "status": "processing", // pending, processing, matched, failed, manual_review
  "current_stage": "semantic_search", // semantic_search, matching, completed
  "search_results": [...],
  "matched_part": {...},
  "confidence_score": 0.85,
  "issues": [],
  "processing_time": "2.3s"
}
```

### 4. Semantic Search Agent (Enhanced)
**Purpose**: Find potential part matches for each individual line item
**Input**: Single line item with extracted specs
**Output**: Ranked list of potential part matches

**Search Strategy**:
```python
def search_for_line_item(line_item):
    searches = []
    
    # Primary search: Full specification
    primary_query = f"{line_item.material_grade} {line_item.form} {line_item.dimensions}"
    searches.append(catalog.search(primary_query, top_k=5))
    
    # Secondary search: Material + form only  
    secondary_query = f"{line_item.material_grade} {line_item.form}"
    searches.append(catalog.search(secondary_query, top_k=3))
    
    # Fallback search: Material only
    fallback_query = f"{line_item.material_grade}"
    searches.append(catalog.search(fallback_query, top_k=2))
    
    return merge_and_rank_results(searches)
```

**Output Format**:
```json
{
  "line_id": "L001",
  "search_results": [
    {
      "rank": 1,
      "part_number": "TI-Grade5-SH-24x36x0125",
      "description": "Titanium Grade 5 Sheet, 24\" x 36\" x 0.125\" thick",
      "similarity_score": 0.92,
      "spec_match": {
        "material": "exact_match",
        "dimensions": "exact_match", 
        "form": "exact_match",
        "grade": "exact_match"
      },
      "availability": 25,
      "unit_price": 485.50,
      "supplier": "TitaniumPro",
      "match_confidence": "high"
    },
    {
      "rank": 2,
      "part_number": "TI-6AL4V-PL-24x36x0125", 
      "description": "Titanium 6Al-4V Plate, 24\" x 36\" x 0.125\"",
      "similarity_score": 0.88,
      "spec_match": {
        "material": "equivalent_grade",
        "dimensions": "exact_match",
        "form": "similar_form", 
        "grade": "equivalent"
      },
      "availability": 12,
      "unit_price": 510.75,
      "supplier": "AeroMetals Inc",
      "match_confidence": "medium-high"
    }
  ],
  "search_metadata": {
    "total_candidates": 47,
    "search_time": "1.2s",
    "queries_used": ["titanium grade 5 sheets 24x36x0.125", "titanium grade 5 sheets", "titanium grade 5"]
  }
}
```

### 5. Matching Agent (New)
**Purpose**: Intelligently select the best part match for each line item
**Input**: Line item + search results
**Output**: Selected part with reasoning

**AI Decision Process**:
```python
async def select_best_match(line_item, search_results):
    matching_prompt = f"""
    Analyze these search results for the line item and select the best match:
    
    Line Item: {line_item.raw_text}
    Extracted Specs: {line_item.extracted_specs}
    Special Requirements: {line_item.special_requirements}
    
    Search Results: {search_results}
    
    Consider:
    1. Specification accuracy (material, dimensions, grade)
    2. Form factor compatibility (sheet vs plate, etc.)
    3. Availability vs quantity needed
    4. Price reasonableness
    5. Special requirements (certs, compliance)
    6. Supplier reliability
    
    Select the best match and provide reasoning:
    {{
        "selected_part": "part_number",
        "confidence": "high/medium/low", 
        "reasoning": "explanation",
        "concerns": ["any concerns"],
        "alternatives": ["backup options"],
        "requires_approval": true/false
    }}
    """
    
    return await llm.invoke(matching_prompt)
```

**Output Format**:
```json
{
  "line_id": "L001",
  "selected_match": {
    "part_number": "TI-Grade5-SH-24x36x0125",
    "confidence": "high",
    "reasoning": "Exact match on material grade (Ti-6Al-4V), form (sheet), and dimensions (24\"x36\"x0.125\"). Sufficient availability (25 units vs 12 needed). Price within expected range for titanium.",
    "concerns": ["Lead time not specified", "DFARS compliance needs verification"],
    "alternatives": ["TI-6AL4V-PL-24x36x0125 (plate form, higher price)"],
    "requires_approval": false,
    "match_score": 0.94
  },
  "selection_metadata": {
    "alternatives_considered": 5,
    "decision_time": "0.8s",
    "ai_model": "gpt-4.1"
  }
}
```

### 6. Assembly Agent (New)
**Purpose**: Combine all matched parts into final order structure
**Input**: All processed line items with selections
**Output**: Complete order ready for ERP/Review

**Assembly Process**:
```python
def assemble_final_order(order_metadata, processed_line_items):
    final_order = {
        "order_info": order_metadata,
        "line_items": [],
        "totals": {},
        "issues": [],
        "approval_required": False
    }
    
    for item in processed_line_items:
        if item.status == "matched":
            final_order.line_items.append(create_order_line(item))
        elif item.status == "manual_review":
            final_order.issues.append(create_issue(item))
            final_order.approval_required = True
    
    final_order.totals = calculate_totals(final_order.line_items)
    return final_order
```

**Output Format**:
```json
{
  "order_summary": {
    "total_line_items": 8,
    "matched_items": 6,
    "manual_review_items": 2,
    "total_value": 15750.25,
    "currency": "USD"
  },
  "line_items": [
    {
      "line_id": "L001",
      "original_request": "Titanium Grade 5 sheets...",
      "matched_part": {
        "part_number": "TI-Grade5-SH-24x36x0125",
        "description": "Titanium Grade 5 Sheet, 24\" x 36\" x 0.125\"",
        "quantity": 12,
        "unit_price": 485.50,
        "line_total": 5826.00,
        "supplier": "TitaniumPro",
        "lead_time": "4-6 weeks"
      },
      "match_confidence": "high",
      "special_handling": ["DFARS compliance verification required"]
    }
  ],
  "issues_requiring_review": [
    {
      "line_id": "L007",
      "issue_type": "no_suitable_match",
      "description": "No exact match found for custom titanium alloy",
      "suggestions": ["Contact engineering for specification clarification"]
    }
  ],
  "next_steps": ["ERP validation", "Customer approval", "Procurement initiation"]
}
```

### 7. ERP Integration Agent (Enhanced)
**Purpose**: Validate order against ERP system
**Input**: Assembled order
**Output**: ERP-validated order with availability/pricing updates

### 8. Review Agent (Enhanced) 
**Purpose**: Final review and approval preparation
**Input**: ERP-validated order
**Output**: Review package with recommendations

---

## Frontend Design Changes

### Line Item Processing Interface

#### 1. Order Overview Card
```
📋 Order Processing: P-2024-001
Customer: TechManufacturing Solutions
Status: Processing Line Items (6/8 complete)
[████████░░] 75%
```

#### 2. Individual Line Item Cards
```
📦 Line Item L001 - PROJECT PHOENIX                    ✅ MATCHED (95%)
┌─────────────────────────────────────────────────────────────────┐
│ Request: Titanium Grade 5 sheets, 24"x36"x0.125", Qty: 12     │
│ Status: [Document] → [Extract] → [Search] → [Match] → [Ready]  │
│                                              ████               │
│ 🎯 Match: TI-Grade5-SH-24x36x0125                              │
│ 💰 Price: $485.50 ea × 12 = $5,826.00                         │
│ 📦 Available: 25 units (✓)                                     │
│ ⚠️  Verify: DFARS compliance                                   │
└─────────────────────────────────────────────────────────────────┘
```

#### 3. Processing Pipeline Visualization
```
Line Item Processing Pipeline:
┌─────┐    ┌────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ L001│ →  │🔍 Search│ →  │🤖 Match │ →  │✅ Ready │ →  │📤 ERP  │
└─────┘    └────────┘    └─────────┘    └─────────┘    └─────────┘
   ✅           ✅            ✅            ✅            ⏳

┌─────┐    ┌────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ L002│ →  │🔍 Search│ →  │🤖 Match │ →  │⚠️ Review│ →  │⏳ Hold │
└─────┘    └────────┘    └─────────┘    └─────────┘    └─────────┘
   ✅           ✅            ✅            ⚠️             ⏳
```

### Real-Time Updates via WebSocket

#### WebSocket Message Types:
```json
// Line item status update
{
  "type": "line_item_update",
  "data": {
    "line_id": "L001",
    "status": "searching",
    "stage": "semantic_search",
    "progress": 0.3,
    "message": "Searching for titanium sheets..."
  }
}

// Search results available
{
  "type": "search_results",
  "data": {
    "line_id": "L001", 
    "candidates_found": 5,
    "top_match": "TI-Grade5-SH-24x36x0125",
    "confidence": 0.92
  }
}

// Match selected
{
  "type": "match_selected",
  "data": {
    "line_id": "L001",
    "selected_part": {...},
    "confidence": "high",
    "requires_review": false
  }
}

// Order assembly complete
{
  "type": "order_assembled", 
  "data": {
    "total_items": 8,
    "matched": 6,
    "review_required": 2,
    "total_value": 15750.25
  }
}
```

---

## Backend Implementation Plan

### 1. Enhanced State Management
```python
class OrderProcessingState:
    def __init__(self, order_id: str):
        self.order_id = order_id
        self.metadata = {}
        self.line_items = {}  # line_id -> LineItemState
        self.overall_status = "pending"
        
class LineItemState:
    def __init__(self, line_id: str):
        self.line_id = line_id
        self.status = "pending"  # pending, searching, matching, matched, failed
        self.current_stage = None
        self.raw_text = ""
        self.extracted_specs = {}
        self.search_results = []
        self.selected_match = None
        self.issues = []
        self.processing_time = 0
```

### 2. Enhanced Supervisor Agent
```python
class EnhancedSupervisorAgent:
    async def process_document(self, session_id: str, client_id: str, content: str):
        # 1. Document parsing
        parsed_doc = await self.document_parser.parse(content)
        
        # 2. Order extraction with line items
        order_data = await self.order_extractor.extract_order(parsed_doc)
        
        # 3. Initialize state tracking
        state = OrderProcessingState(session_id)
        
        # 4. Process line items in parallel
        tasks = []
        for line_item in order_data.line_items:
            task = self.process_line_item(line_item, state, client_id)
            tasks.append(task)
        
        # 5. Wait for all line items to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 6. Assembly agent combines results
        final_order = await self.assembly_agent.assemble(state)
        
        # 7. ERP integration
        erp_result = await self.erp_agent.validate(final_order)
        
        # 8. Final review
        review = await self.review_agent.prepare_review(erp_result)
        
        return review
    
    async def process_line_item(self, line_item: dict, state: OrderProcessingState, client_id: str):
        line_state = LineItemState(line_item["line_id"])
        state.line_items[line_item["line_id"]] = line_state
        
        try:
            # Semantic search
            await self.send_line_item_update(client_id, line_item["line_id"], "searching")
            search_results = await self.search_agent.search_for_item(line_item)
            line_state.search_results = search_results
            
            # Matching
            await self.send_line_item_update(client_id, line_item["line_id"], "matching") 
            match_result = await self.matching_agent.select_match(line_item, search_results)
            line_state.selected_match = match_result
            
            # Update status
            if match_result.confidence == "high":
                line_state.status = "matched"
            else:
                line_state.status = "manual_review"
                
            await self.send_line_item_update(client_id, line_item["line_id"], line_state.status)
            
        except Exception as e:
            line_state.status = "failed"
            line_state.issues.append(str(e))
            await self.send_line_item_update(client_id, line_item["line_id"], "failed")
```

### 3. New Agent Classes
```python
class LineItemSearchAgent:
    async def search_for_item(self, line_item: dict) -> dict:
        # Implement multi-strategy search
        pass

class PartMatchingAgent:
    async def select_match(self, line_item: dict, search_results: list) -> dict:
        # AI-powered part selection
        pass
        
class OrderAssemblyAgent:
    async def assemble(self, processing_state: OrderProcessingState) -> dict:
        # Combine all line items into final order
        pass
```

---

## Benefits of Enhanced Design

### 1. **Improved Accuracy**
- Individual line item processing reduces cross-contamination
- Specialized matching agent makes better part selections
- Multiple search strategies increase match probability

### 2. **Better Visibility** 
- Real-time progress tracking for each line item
- Clear status indicators and confidence scores
- Detailed reasoning for part selections

### 3. **Enhanced User Experience**
- Interactive line item cards
- Progress visualization
- Clear action items for manual review

### 4. **Scalability**
- Parallel processing of line items
- Modular agent architecture
- State management for complex orders

### 5. **Quality Control**
- Confidence scoring for matches
- Automatic flagging of questionable matches
- Detailed audit trail for decisions

---

## Implementation Priority

### Phase 1: Core Infrastructure
1. Enhanced order extraction schema
2. Line item state management
3. Basic line item processing pipeline

### Phase 2: Intelligence Layer
1. Enhanced semantic search agent
2. AI-powered matching agent  
3. Assembly agent

### Phase 3: User Experience
1. Line item progress interface
2. Real-time WebSocket updates
3. Interactive review interface

### Phase 4: Advanced Features
1. Parallel processing optimization
2. Advanced confidence algorithms
3. Learning from user feedback

---

This enhanced design provides a much more sophisticated and accurate sales order processing system that handles the complexity of real-world orders while maintaining visibility and control throughout the process.
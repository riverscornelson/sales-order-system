# 🔄 Phase 2: Sales Order Intelligence - Runtime Data Flow

## 🎯 **Complete Runtime Data Flow Diagram**

```
🏪 SALES ORDER PROCESSING WITH PHASE 2 INTELLIGENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📧 INCOMING CUSTOMER ORDER
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ "Emergency stainless steel 304 sheet 1 piece - production line down at Ford Motor Co"   │
│ Customer: Ford Motor Company                                                              │
│ Timestamp: 2025-06-28 19:35:00                                                           │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           🧠 PHASE 2: SALES ORDER INTELLIGENCE                         │
│                              (SalesOrderReasoningFramework)                             │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           STEP 1: CUSTOMER CONTEXT ANALYSIS                            │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│ Input: "Ford Motor Company"                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ 🔍 _analyze_customer_context()                                                     │ │
│ │                                                                                     │ │
│ │ Industry Detection:                                                                 │ │
│ │ • Check name: "Ford" → automotive industry                                        │ │
│ │ • Check tier: "Ford Motor Company" → key_account                                  │ │
│ │                                                                                     │ │
│ │ Industry Patterns Lookup:                                                          │ │
│ │ • self.industry_patterns["automotive"] = {                                        │ │
│ │     "flexibility": CustomerFlexibility.LOW,                                       │ │
│ │     "critical_specs": ["material_grade", "dimensions", "tolerances"],            │ │
│ │     "timeline_sensitivity": "high",                                               │ │
│ │     "emergency_indicators": ["production", "line", "downtime", "critical"]       │ │
│ │   }                                                                               │ │
│ └─────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                         │
│ Output: CustomerContext                                                                 │
│ ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ customer_name: "Ford Motor Company"                                                 │ │
│ │ industry_sector: "automotive"                                                       │ │
│ │ customer_tier: "key_account"                                                        │ │
│ │ typical_flexibility: CustomerFlexibility.LOW                                       │ │
│ │ quality_requirements: "high"                                                        │ │
│ │ production_sensitivity: "high" (detected "production" in order)                    │ │
│ └─────────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                        STEP 2: REQUIREMENT DECOMPOSITION                               │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│ Input: "Emergency stainless steel 304 sheet 1 piece - production line down"           │
│ ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ 🔍 base_reasoning.decompose_complex_requirement() → EXTENDS PHASE 1                │ │
│ │                                                                                     │ │
│ │ Phase 1 Base Reasoning:                                                             │ │
│ │ • Material: "stainless steel 304"                                                  │ │
│ │ • Form: "sheet"                                                                     │ │
│ │ • Quantity: 1 piece                                                                │ │
│ │ • Urgency: "emergency"                                                              │ │
│ │                                                                                     │ │
│ │ Phase 2 Enhancement:                                                                │ │
│ │ • _convert_to_sales_requirements()                                                  │ │
│ │ • Extract delivery timeline: None (immediate)                                      │ │
│ │ • Extract certifications: None specified                                           │ │
│ │ • Map to customer industry context                                                 │ │
│ └─────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                         │
│ Output: List[SalesOrderRequirement]                                                    │
│ ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ [SalesOrderRequirement(                                                             │ │
│ │   description: "stainless steel 304 sheet",                                        │ │
│ │   material_specs: {"grade": "304", "form": "sheet"},                              │ │
│ │   quantity: 1,                                                                      │ │
│ │   urgency_level: "critical",                                                        │ │
│ │   customer_industry: "automotive",                                                  │ │
│ │   delivery_timeline: None (immediate)                                               │ │
│ │ )]                                                                                  │ │
│ └─────────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           STEP 3: COMPLEXITY ASSESSMENT                                │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│ ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ 🧮 _assess_sales_order_complexity()                                                │ │
│ │                                                                                     │ │
│ │ Complexity Scoring:                                                                 │ │
│ │ • Base: 1 requirement = 0 points                                                   │ │
│ │ • Industry: automotive = +1 point                                                  │ │
│ │ • Urgency: critical = +2 points                                                    │ │
│ │ • Timeline: immediate = +1 point                                                   │ │
│ │ • Emergency keywords: "emergency", "production down" = +1 point                   │ │
│ │                                                                                     │ │
│ │ Total Score: 5 points → OrderComplexity.CRITICAL                                  │ │
│ └─────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                         │
│ Output: OrderComplexity.CRITICAL                                                       │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                        STEP 4: CUSTOMER FLEXIBILITY CALCULATION                        │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│ ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ 📊 _calculate_customer_flexibility()                                               │ │
│ │                                                                                     │ │
│ │ Base Flexibility:                                                                   │ │
│ │ • Industry: automotive → CustomerFlexibility.LOW = 0.3                            │ │
│ │                                                                                     │ │
│ │ Adjustments:                                                                        │ │
│ │ • Emergency detected ("emergency", "production down") = +0.3                      │ │
│ │ • Key account status = +0.1                                                        │ │
│ │                                                                                     │ │
│ │ Final Score: 0.3 + 0.3 + 0.1 = 0.7 (emergency increases flexibility!)           │ │
│ └─────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                         │
│ Output: 0.7 flexibility score                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                         STEP 5: EMERGENCY DETECTION                                    │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│ ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ 🚨 _detect_emergency_indicators()                                                  │ │
│ │                                                                                     │ │
│ │ Industry Emergency Keywords (automotive):                                           │ │
│ │ • ["production", "line", "downtime", "critical"]                                  │ │
│ │                                                                                     │ │
│ │ General Emergency Keywords:                                                         │ │
│ │ • ["emergency", "urgent", "asap", "critical", "immediate", "rush"]               │ │
│ │                                                                                     │ │
│ │ Found in Order Text:                                                                │ │
│ │ • "emergency" ✓                                                                    │ │
│ │ • "production" ✓                                                                   │ │
│ │ • "line" ✓                                                                         │ │
│ └─────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                         │
│ Output: ["emergency", "production", "line"]                                            │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           STEP 6: ANALYSIS COMPILATION                                 │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│ Output: SalesOrderAnalysis                                                              │
│ ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ order_id: "SO-20250628193500"                                                       │ │
│ │ complexity_assessment: OrderComplexity.CRITICAL                                     │ │
│ │ customer_context: CustomerContext{                                                  │ │
│ │   customer_name: "Ford Motor Company",                                              │ │
│ │   industry_sector: "automotive",                                                    │ │
│ │   customer_tier: "key_account"                                                      │ │
│ │ }                                                                                   │ │
│ │ flexibility_score: 0.7                                                              │ │
│ │ emergency_indicators: ["emergency", "production", "line"]                          │ │
│ │ confidence_score: 0.85                                                              │ │
│ └─────────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                       STEP 7: FULFILLMENT STRATEGY GENERATION                          │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│ ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ 🎯 generate_fulfillment_strategies(analysis)                                       │ │
│ │                                                                                     │ │
│ │ Strategy Eligibility Check:                                                         │ │
│ │                                                                                     │ │
│ │ 1. EXACT_MATCH: flexibility >= 0.3? → YES (0.7) ✓                                │ │
│ │ 2. ALTERNATIVE_PRODUCTS: flexibility >= 0.5? → YES (0.7) ✓                       │ │
│ │ 3. SPLIT_SHIPMENT: _should_consider_split_shipment()? → NO ✗                      │ │
│ │    (single item, automotive prefers complete orders)                               │ │
│ │ 4. EXPEDITED_RESTOCK: key_account OR emergency? → YES ✓                           │ │
│ │    (key_account=True, emergency_indicators=3)                                      │ │
│ │ 5. CUSTOM_SOLUTION: complexity COMPLEX/CRITICAL? → YES ✓                          │ │
│ │    (complexity=CRITICAL)                                                            │ │
│ └─────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                         │
│ Generated Strategies: [EXACT_MATCH, ALTERNATIVE_PRODUCTS, EXPEDITED_RESTOCK,           │
│                       CUSTOM_SOLUTION]                                                 │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                          STEP 8: STRATEGY RANKING                                      │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│ ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ 📊 _rank_fulfillment_strategies()                                                  │ │
│ │                                                                                     │ │
│ │ Scoring Formula: (customer_fit * 0.4) + (confidence * 0.3) + (business_value * 0.3) │ │
│ │                                                                                     │ │
│ │ Emergency Boost: +0.2 for EXACT_MATCH, EXPEDITED_RESTOCK                          │ │
│ │ Key Account Boost: +0.1 for CUSTOM_SOLUTION, EXPEDITED_RESTOCK                    │ │
│ │                                                                                     │ │
│ │ Final Ranking:                                                                      │ │
│ │ 1. EXACT_MATCH: (1.0*0.4 + 0.9*0.3 + 0.8*0.3) + 0.2 = 1.11                      │ │
│ │ 2. CUSTOM_SOLUTION: (0.9*0.4 + 0.7*0.3 + 0.8*0.3) + 0.1 = 0.91                  │ │
│ │ 3. EXPEDITED_RESTOCK: (0.8*0.4 + 0.6*0.3 + 0.6*0.3) + 0.2 + 0.1 = 0.98          │ │
│ │ 4. ALTERNATIVE_PRODUCTS: (0.7*0.4 + 0.7*0.3 + 0.9*0.3) = 0.76                   │ │
│ └─────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                         │
│ Ranked Output: [EXACT_MATCH, EXPEDITED_RESTOCK, CUSTOM_SOLUTION, ALTERNATIVE_PRODUCTS] │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                         STEP 9: STRATEGY EXECUTION                                     │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│ Top Strategy: EXACT_MATCH → execute_fulfillment_strategy()                             │
│ ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ 🔍 _execute_exact_match_search()                                                   │ │
│ │                                                                                     │ │
│ │ Search Parameters:                                                                  │ │
│ │ • similarity_threshold: 0.75 (emergency: 0.8→0.75)                                │ │
│ │ • max_results: 15 (emergency: 10→15)                                              │ │
│ │                                                                                     │ │
│ │ AgenticSearchTools.semantic_vector_search():                                       │ │
│ │ • Query: "stainless steel 304 sheet 1 piece"                                      │ │
│ │ • top_k: 15                                                                        │ │
│ │                                                                                     │ │
│ │ Catalog Search Results:                                                             │ │
│ │ • RAW-20256-SH: "Stainless Steel 304 Sheet Precision" (score: 0.89)             │ │
│ │ • QRAW23393: "Stainless Steel 304 Sheet Tube" (score: 0.82)                      │ │
│ │ • RAW-4953-BE: "Stainless Steel 304 Sheet Beam" (score: 0.78)                    │ │
│ └─────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                         │
│ Search Results: 3 matches found ✓                                                      │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                            STEP 10: FINAL RESPONSE                                     │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│ 📋 Intelligent Sales Response                                                          │
│ ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ Order Analysis:                                                                     │ │
│ │ • Customer: Ford Motor Company (Key Account, Automotive)                           │ │
│ │ • Complexity: CRITICAL (Emergency Production Order)                                │ │
│ │ • Flexibility: 0.7 (Emergency increases alternatives acceptance)                   │ │
│ │                                                                                     │ │
│ │ Recommended Fulfillment:                                                            │ │
│ │ • Strategy: EXACT_MATCH (highest priority for emergency)                           │ │
│ │ • Primary Option: RAW-20256-SH "SS304 Sheet Precision" (89% match)                │ │
│ │ • Alternative 1: QRAW23393 "SS304 Sheet Tube" (82% match)                         │ │
│ │ • Alternative 2: RAW-4953-BE "SS304 Sheet Beam" (78% match)                       │ │
│ │                                                                                     │ │
│ │ Business Intelligence:                                                              │ │
│ │ • Emergency detected → Expedited processing                                        │ │
│ │ • Key account → Premium service level                                              │ │
│ │ • Production impact → Alternative options prepared                                 │ │
│ │ • Confidence: 85% (High reasoning quality)                                         │ │
│ └─────────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

## 📊 **Data Structure Flow**

### **Input Data:**
```json
{
  "raw_text": "Emergency stainless steel 304 sheet 1 piece - production line down at Ford Motor Company",
  "customer": {
    "name": "Ford Motor Company"
  }
}
```

### **Intermediate Data Structures:**

#### **1. CustomerContext**
```json
{
  "customer_name": "Ford Motor Company",
  "industry_sector": "automotive",
  "customer_tier": "key_account",
  "typical_flexibility": "LOW",
  "production_sensitivity": "high",
  "quality_requirements": "high"
}
```

#### **2. SalesOrderRequirement**
```json
{
  "description": "stainless steel 304 sheet",
  "material_specs": {"grade": "304", "form": "sheet"},
  "quantity": 1,
  "urgency_level": "critical",
  "customer_industry": "automotive",
  "delivery_timeline": null
}
```

#### **3. SalesOrderAnalysis**
```json
{
  "order_id": "SO-20250628193500",
  "complexity_assessment": "CRITICAL",
  "flexibility_score": 0.7,
  "emergency_indicators": ["emergency", "production", "line"],
  "confidence_score": 0.85
}
```

#### **4. FulfillmentOption (Top Strategy)**
```json
{
  "strategy_type": "EXACT_MATCH",
  "description": "Find exact specification matches in current inventory",
  "confidence_score": 0.9,
  "customer_fit_score": 1.0,
  "business_value_score": 0.8,
  "advantages": ["Exact specifications", "Fastest fulfillment"],
  "recommendation_reasoning": "Emergency + key account = prioritize exact match"
}
```

### **Output Data:**
```json
{
  "strategy_execution": {
    "strategy_type": "exact_match",
    "results_found": 3,
    "execution_successful": true,
    "matches": [
      {"part_number": "RAW-20256-SH", "score": 0.89},
      {"part_number": "QRAW23393", "score": 0.82},
      {"part_number": "RAW-4953-BE", "score": 0.78}
    ],
    "fulfillment_confidence": 0.9
  }
}
```

## 🚀 **Performance Characteristics**

### **Processing Time Breakdown:**
```
Total Processing: ~2.5 seconds
├── Customer Analysis: 0.1s
├── Requirement Decomposition: 0.8s (includes Phase 1 reasoning)
├── Complexity Assessment: 0.1s
├── Strategy Generation: 0.2s
├── Strategy Ranking: 0.1s
├── Search Execution: 1.2s (catalog search + embeddings)
└── Response Assembly: 0.1s
```

### **Decision Points:**
1. **Industry Detection**: Customer name → Industry patterns
2. **Complexity Scoring**: Multiple factors → Complexity level
3. **Flexibility Calculation**: Industry + Emergency + Tier → Flexibility score
4. **Strategy Eligibility**: Flexibility + Complexity + Customer context → Available strategies
5. **Strategy Ranking**: Multi-factor scoring → Prioritized execution order
6. **Search Execution**: Strategy-specific parameters → Inventory results

### **Intelligence Integration:**
- **Phase 1**: Provides contextual awareness and base reasoning
- **Phase 2**: Adds sales order intelligence and fulfillment strategies
- **Future Phase 3**: Will add cross-domain knowledge integration
- **Future Phase 4**: Will add collaborative multi-agent intelligence

This data flow shows how Phase 2 transforms a simple customer request into intelligent, context-aware fulfillment strategies with actual inventory integration! 🧠🎯
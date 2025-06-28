# 🧪 Phase 2 Sales Order Intelligence - Comprehensive Evaluation Framework Design

## 🎯 **Design Philosophy & OpenAI Evals Compatibility**

### **PRIMARY OBJECTIVE: Accurate ERP JSON Generation**

The evaluation framework prioritizes the correctness of JSON output for ERP import above all else. The system must accurately extract sales order lines from customer emails and generate properly structured JSON that can be directly imported into ERP systems.

#### **Critical ERP JSON Requirements:**
1. **Line Item Accuracy** - All requested items must be extracted with correct quantities
2. **Material Specification Precision** - Exact material grades, dimensions, and specifications
3. **Part Number Matching** - Correct selection from inventory catalog
4. **Customer Data Integrity** - Accurate customer identification and metadata
5. **Order Structure Validity** - JSON must conform to ERP schema requirements

### **Core Design Principles**

1. **OpenAI Evals Framework Compatibility**
   - Follow OpenAI's `evals` package structure and interfaces
   - Implement standardized `Eval` base class with `eval_sample()` method
   - Support JSONL input format for scalable test management
   - Generate standardized metrics compatible with OpenAI's analysis tools
   - Enable automated scoring with both rule-based and LLM-judge evaluation

2. **Domain-Specific Intelligence Testing**
   - Test sales order reasoning capabilities beyond simple Q&A
   - Evaluate multi-step reasoning chains (decomposition → analysis → strategy → execution)
   - Measure business intelligence quality (customer context, urgency detection, strategy appropriateness)
   - Assess real-world performance with industry-specific scenarios

3. **Comprehensive Coverage & Scalability**
   - Support 100+ test cases across diverse customer types and scenarios
   - Hierarchical test organization (by industry, complexity, customer type, scenario type)
   - Automated test case generation for edge cases and stress testing
   - Regression testing capabilities for system evolution

4. **Production-Ready Evaluation**
   - Integration with CI/CD pipelines for automated quality gates
   - Performance benchmarking (latency, throughput, resource usage)
   - A/B testing support for comparing different reasoning strategies
   - Real-time monitoring integration for production deployment

## 🏗️ **Architecture Overview**

```
🧪 SALES ORDER INTELLIGENCE EVALUATION FRAMEWORK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 OpenAI Evals Framework Integration
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           SalesOrderIntelligenceEval                               │
│                           (extends evals.Eval)                                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  📝 Standard OpenAI Evals Interface:                                              │
│  • eval_sample(sample: dict) -> EvalResult                                        │
│  • run(samples: List[dict]) -> EvalReport                                         │
│  • get_metrics() -> Dict[str, float]                                              │
│                                                                                     │
│  🧠 Sales Order Intelligence Extensions:                                          │
│  • evaluate_reasoning_chain(sample) -> ReasoningEvalResult                        │
│  • evaluate_customer_context(sample) -> ContextEvalResult                         │
│  • evaluate_strategy_generation(sample) -> StrategyEvalResult                     │
│  • evaluate_business_intelligence(sample) -> BusinessEvalResult                   │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        🎯 Multi-Dimensional Evaluation Engine                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  Dimension 1: 🧠 REASONING QUALITY                                                │
│  ┌───────────────────────────────────────────────────────────────────────────────┐ │
│  │ • Requirement Decomposition Accuracy                                         │ │
│  │ • Customer Context Recognition (Industry, Tier, Flexibility)                 │ │
│  │ • Complexity Assessment (Simple → Moderate → Complex → Critical)             │ │
│  │ │ Emergency Detection & Response                                              │ │
│  │ • Multi-Step Reasoning Chain Coherence                                       │ │
│  └───────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                     │
│  Dimension 2: 🎯 STRATEGY INTELLIGENCE                                            │
│  ┌───────────────────────────────────────────────────────────────────────────────┐ │
│  │ • Fulfillment Strategy Appropriateness                                       │ │
│  │ • Strategy Ranking Quality (Customer Fit + Confidence + Business Value)     │ │
│  │ • Alternative Discovery & Evaluation                                         │ │
│  │ • Risk Assessment & Trade-off Analysis                                       │ │
│  │ • Business Value Optimization                                                │ │
│  └───────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                     │
│  Dimension 3: 📊 BUSINESS INTELLIGENCE                                            │
│  ┌───────────────────────────────────────────────────────────────────────────────┐ │
│  │ • Industry-Specific Pattern Recognition                                      │ │
│  │ • Customer Tier & Relationship Intelligence                                  │ │
│  │ • Emergency Situation Response Quality                                       │ │
│  │ • Regulatory & Compliance Awareness                                          │ │
│  │ • Commercial Insights & Value Propositions                                   │ │
│  └───────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                     │
│  Dimension 4: ⚡ OPERATIONAL EXCELLENCE                                           │
│  ┌───────────────────────────────────────────────────────────────────────────────┐ │
│  │ • Processing Speed & Latency                                                 │ │
│  │ • Resource Utilization Efficiency                                            │ │
│  │ • Error Handling & Recovery                                                  │ │
│  │ • Scalability Under Load                                                     │ │
│  │ • Integration Reliability                                                    │ │
│  └───────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                      📋 Test Case Management & Generation                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  🗂️ Test Case Categories:                                                         │
│  ┌───────────────────────────────────────────────────────────────────────────────┐ │
│  │ Core Scenarios (100+ cases):                                                 │ │
│  │ • Industry Coverage: 15 industries × 4 complexity levels                    │ │
│  │ • Customer Types: 8 customer tiers × 5 relationship types                   │ │
│  │ • Emergency Situations: 12 emergency types × 3 severity levels              │ │
│  │ • Order Complexity: 20 complexity patterns × 4 requirement types            │ │
│  │                                                                               │ │
│  │ Edge Cases (50+ cases):                                                      │ │
│  │ • Language & Communication Barriers                                          │ │
│  │ • Unusual Customer Requirements                                              │ │
│  │ • System Boundary Conditions                                                 │ │
│  │ • Adversarial & Stress Testing                                               │ │
│  │                                                                               │ │
│  │ Regression Cases (30+ cases):                                                │ │
│  │ • Historical Failure Scenarios                                               │ │
│  │ • Performance Regression Detection                                           │ │
│  │ • Integration Compatibility Testing                                          │ │
│  └───────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                     │
│  🤖 Automated Test Generation:                                                    │
│  ┌───────────────────────────────────────────────────────────────────────────────┐ │
│  │ • LLM-Powered Scenario Generation                                            │ │
│  │ • Combinatorial Test Case Expansion                                          │ │
│  │ • Synthetic Customer Email Generation                                        │ │
│  │ • Dynamic Difficulty Scaling                                                 │ │
│  └───────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                       🔍 Advanced Scoring & Analysis Engine                        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  📊 Multi-Modal Scoring:                                                          │
│  ┌───────────────────────────────────────────────────────────────────────────────┐ │
│  │ Rule-Based Scoring (60%):                                                    │ │
│  │ • Exact Match: Industry, complexity, emergency detection                     │ │
│  │ • Fuzzy Match: Strategy appropriateness, reasoning quality                   │ │
│  │ • Performance Metrics: Latency, accuracy, throughput                         │ │
│  │                                                                               │ │
│  │ LLM Judge Scoring (40%):                                                     │ │
│  │ • GPT-4 Expert Evaluation of reasoning quality                               │ │
│  │ • Business intelligence assessment                                           │ │
│  │ • Customer satisfaction prediction                                           │ │
│  │ • Commercial viability analysis                                              │ │
│  └───────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                     │
│  📈 Advanced Analytics:                                                           │
│  ┌───────────────────────────────────────────────────────────────────────────────┐ │
│  │ • Statistical Significance Testing                                           │ │
│  │ • Performance Distribution Analysis                                          │ │
│  │ • Error Pattern Recognition                                                  │ │
│  │ • Improvement Opportunity Identification                                     │ │
│  │ • Competitive Benchmarking                                                   │ │
│  └───────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## 📝 **OpenAI Evals Integration Specification**

### **1. Standard Evals Framework Compliance**

```python
# evals/registry/eval_specs.yaml
sales_order_intelligence:
  id: sales_order_intelligence.v1
  description: "Comprehensive evaluation of Phase 2 Sales Order Intelligence reasoning capabilities"
  disclaimer: "This evaluation tests multi-step reasoning for sales order processing in metals industry"
  
  # Standard evals framework fields
  eval_type: "SalesOrderIntelligenceEval"
  samples_jsonl: "sales_order_samples.jsonl"
  
  # Custom evaluation parameters
  eval_params:
    reasoning_weights:
      customer_context: 0.25
      complexity_assessment: 0.20  
      emergency_detection: 0.20
      strategy_generation: 0.20
      business_intelligence: 0.15
    
    performance_thresholds:
      min_accuracy: 0.85
      max_latency_ms: 3000
      min_coverage: 0.95
    
    industry_coverage:
      - automotive
      - aerospace  
      - medical_device
      - research_development
      - general_manufacturing
      - defense
      - food_processing
      - marine
      - energy
      - mining
```

### **2. JSONL Sample Format**

```json
{
  "id": "automotive_emergency_001",
  "category": "emergency_production",
  "industry": "automotive",
  "customer_tier": "key_account",
  "complexity": "critical",
  "input": {
    "customer_email": "EMERGENCY REQUEST - PRODUCTION CRITICAL\n\nOur stamping line #3 is down due to hydraulic failure. Need immediate replacement:\n\n- Stainless Steel 316L seamless tubing\n- 2.5\" OD x 0.065\" wall thickness\n- Length: 48\" pieces (need 6 pieces minimum)\n- Pressure rating: 3000 PSI minimum\n- Mill cert required\n\nProduction impact: $85K per hour downtime\nNeed delivery by tomorrow 2PM latest",
    "customer_name": "Ford Motor Company - Dearborn Plant",
    "metadata": {
      "timestamp": "2024-06-28T19:30:00Z",
      "source": "email",
      "priority": "critical"
    }
  },
  "expected_erp_json": {
    "order_id": "ORD-FORD-20240628-001",
    "customer": {
      "name": "Ford Motor Company - Dearborn Plant",
      "customer_id": "FORD-001",
      "tier": "key_account"
    },
    "line_items": [
      {
        "line_id": "L001",
        "material": "316L",
        "form": "tube",
        "specifications": {
          "outer_diameter": 2.5,
          "wall_thickness": 0.065,
          "length": 48,
          "units": "inches",
          "pressure_rating": 3000,
          "pressure_units": "PSI",
          "seamless": true
        },
        "quantity": 6,
        "certifications": ["mill_cert"],
        "urgency": "critical",
        "matched_part": {
          "part_number": "SS316L-TUBE-2.5-0.065",
          "description": "316L Seamless Tube 2.5\" OD x 0.065\" Wall",
          "availability": "in_stock",
          "quantity_available": 12
        }
      }
    ],
    "order_metadata": {
      "priority": "emergency",
      "requested_delivery": "2024-06-29T14:00:00Z",
      "production_impact": "$85K/hour",
      "processing_strategy": "exact_match"
    }
  },
  "expected_reasoning": {
    "customer_context": {
      "industry_sector": "automotive",
      "customer_tier": "key_account",
      "flexibility_score": 0.7
    },
    "complexity_assessment": "critical",
    "emergency_detected": true,
    "emergency_indicators": ["line down", "production", "emergency"],
    "fulfillment_strategies": ["exact_match", "expedited_restock", "custom_solution"],
    "top_strategy": "exact_match",
    "business_reasoning": "Emergency production situation requires immediate exact match with expedited options as backup"
  },
  "scoring_criteria": {
    "erp_json_critical": ["line_items", "material", "quantity", "specifications"],
    "erp_json_important": ["customer.name", "order_metadata.priority", "matched_part.part_number"],
    "reasoning_validation": ["emergency_detected", "complexity_assessment"],
    "llm_judge_aspects": ["line_item_extraction_quality", "specification_accuracy", "business_appropriateness"]
  }
}
```

### **3. Evaluation Class Architecture**

```python
class SalesOrderIntelligenceEval(evals.Eval):
    """
    OpenAI Evals compatible evaluation for Phase 2 Sales Order Intelligence
    
    Inherits from evals.Eval to ensure compatibility with OpenAI's evaluation framework
    while providing specialized testing for sales order reasoning capabilities.
    """
    
    def __init__(self, eval_spec: dict, registry: evals.Registry):
        super().__init__(eval_spec, registry)
        
        # Initialize sales order intelligence components
        self.reasoning_framework = SalesOrderReasoningFramework()
        self.search_coordinator = SalesOrderSearchCoordinator()
        
        # Load evaluation parameters
        self.reasoning_weights = eval_spec.get("reasoning_weights", {})
        self.performance_thresholds = eval_spec.get("performance_thresholds", {})
        
        # Initialize scoring engines
        self.rule_based_scorer = RuleBasedScorer()
        self.llm_judge_scorer = LLMJudgeScorer()
        
        # Performance tracking
        self.performance_tracker = PerformanceTracker()
    
    def eval_sample(self, sample: dict) -> evals.EvalResult:
        """
        Standard OpenAI Evals interface - evaluate single sample
        
        This is the core method that OpenAI's framework calls for each test case.
        It coordinates the multi-dimensional evaluation of sales order intelligence.
        """
        
        # Extract input and expected output
        input_data = sample["input"]
        expected_output = sample["expected_output"]
        scoring_criteria = sample.get("scoring_criteria", {})
        
        # Performance tracking start
        start_time = time.time()
        
        try:
            # Execute sales order intelligence pipeline
            actual_output = await self._execute_sales_order_pipeline(input_data)
            
            # Multi-dimensional scoring
            score_result = self._comprehensive_scoring(
                actual_output, 
                expected_output, 
                scoring_criteria
            )
            
            # Performance metrics
            execution_time = time.time() - start_time
            performance_metrics = self.performance_tracker.record_execution(
                execution_time, 
                actual_output
            )
            
            # Generate OpenAI Evals compatible result
            eval_result = evals.EvalResult(
                run_id=self.run_id,
                sample_id=sample["id"],
                prompt=input_data.get("customer_email", ""),
                sampled=actual_output,
                expected=expected_output,
                score=score_result.overall_score,
                metadata={
                    "category": sample.get("category"),
                    "industry": sample.get("industry"),
                    "complexity": sample.get("complexity"),
                    "detailed_scores": score_result.detailed_scores,
                    "performance_metrics": performance_metrics,
                    "reasoning_chain": actual_output.get("reasoning_chain"),
                    "error_analysis": score_result.error_analysis
                }
            )
            
            return eval_result
            
        except Exception as e:
            # Error handling with detailed diagnostics
            return evals.EvalResult(
                run_id=self.run_id,
                sample_id=sample["id"],
                prompt=input_data.get("customer_email", ""),
                sampled={"error": str(e)},
                expected=expected_output,
                score=0.0,
                metadata={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "execution_time": time.time() - start_time
                }
            )
    
    def get_metrics(self) -> Dict[str, float]:
        """
        Standard OpenAI Evals interface - return aggregate metrics
        
        Returns comprehensive metrics compatible with OpenAI's analysis tools
        while providing detailed insights into sales order intelligence performance.
        """
        
        # Calculate standard OpenAI metrics
        base_metrics = super().get_metrics()
        
        # Add sales order intelligence specific metrics
        extended_metrics = {
            # PRIMARY METRIC: ERP JSON Accuracy
            "erp_json_accuracy": self._calculate_erp_json_accuracy(),
            "line_item_extraction_accuracy": self._calculate_line_item_accuracy(),
            "part_selection_accuracy": self._calculate_part_selection_accuracy(),
            "specification_accuracy": self._calculate_specification_accuracy(),
            "customer_data_accuracy": self._calculate_customer_data_accuracy(),
            "json_structure_validity": self._calculate_json_validity(),
            
            # Overall performance
            "overall_accuracy": self._calculate_overall_accuracy(),
            "customer_satisfaction_score": self._calculate_customer_satisfaction(),
            
            # Reasoning quality metrics
            "customer_context_accuracy": self._get_accuracy_by_dimension("customer_context"),
            "complexity_assessment_accuracy": self._get_accuracy_by_dimension("complexity"),
            "emergency_detection_accuracy": self._get_accuracy_by_dimension("emergency"),
            "strategy_appropriateness_score": self._get_accuracy_by_dimension("strategy"),
            
            # Business intelligence metrics
            "industry_recognition_rate": self._calculate_industry_accuracy(),
            "tier_classification_accuracy": self._calculate_tier_accuracy(),
            "flexibility_prediction_accuracy": self._calculate_flexibility_accuracy(),
            
            # Performance metrics
            "avg_processing_time_ms": self.performance_tracker.get_average_time(),
            "p95_processing_time_ms": self.performance_tracker.get_p95_time(),
            "throughput_requests_per_second": self.performance_tracker.get_throughput(),
            
            # Coverage metrics
            "industry_coverage": self._calculate_industry_coverage(),
            "complexity_coverage": self._calculate_complexity_coverage(),
            "edge_case_coverage": self._calculate_edge_case_coverage(),
            
            # Error analysis
            "error_rate": self._calculate_error_rate(),
            "critical_error_rate": self._calculate_critical_error_rate(),
            "recovery_success_rate": self._calculate_recovery_rate(),
        }
        
        # Combine base and extended metrics
        return {**base_metrics, **extended_metrics}
```

## 🎯 **Advanced Evaluation Dimensions**

### **1. ERP JSON Accuracy & Sales Order Line Creation (40% of score) - PRIMARY OBJECTIVE**

```python
class ERPJsonAccuracyEvaluator:
    """
    Evaluates the correctness of generated JSON for ERP import - the most critical metric
    """
    
    def evaluate_erp_json_accuracy(self, actual_json: dict, expected_json: dict, customer_email: str) -> ERPAccuracyScore:
        """
        Assess JSON accuracy for ERP import across critical dimensions
        """
        
        # Line item extraction accuracy (30%)
        line_item_score = self._evaluate_line_items(
            actual_json.get("line_items", []),
            expected_json.get("line_items", [])
        )
        
        # Part number selection accuracy (25%)
        part_selection_score = self._evaluate_part_selection(
            actual_json.get("matched_parts", {}),
            expected_json.get("matched_parts", {})
        )
        
        # Quantity and specifications accuracy (20%)
        specs_score = self._evaluate_specifications(
            actual_json.get("line_items", []),
            expected_json.get("line_items", []),
            customer_email
        )
        
        # Customer data accuracy (15%)
        customer_score = self._evaluate_customer_data(
            actual_json.get("customer", {}),
            expected_json.get("customer", {})
        )
        
        # Order metadata accuracy (10%)
        metadata_score = self._evaluate_order_metadata(
            actual_json.get("order_metadata", {}),
            expected_json.get("order_metadata", {})
        )
        
        return ERPAccuracyScore(
            line_items=line_item_score,
            part_selection=part_selection_score,
            specifications=specs_score,
            customer_data=customer_score,
            metadata=metadata_score,
            overall=self._weighted_average([
                (line_item_score, 0.30),
                (part_selection_score, 0.25),
                (specs_score, 0.20),
                (customer_score, 0.15),
                (metadata_score, 0.10)
            ]),
            json_valid=self._validate_json_structure(actual_json),
            missing_fields=self._identify_missing_fields(actual_json, expected_json),
            incorrect_fields=self._identify_incorrect_fields(actual_json, expected_json)
        )
    
    def _evaluate_line_items(self, actual_items: List[dict], expected_items: List[dict]) -> float:
        """
        Evaluate if all line items from customer email were correctly extracted
        """
        # Check count matches
        if len(actual_items) != len(expected_items):
            count_penalty = abs(len(actual_items) - len(expected_items)) * 0.1
        else:
            count_penalty = 0
        
        # Check each line item
        item_scores = []
        for expected in expected_items:
            best_match_score = 0
            for actual in actual_items:
                match_score = self._calculate_line_item_match(actual, expected)
                best_match_score = max(best_match_score, match_score)
            item_scores.append(best_match_score)
        
        avg_score = sum(item_scores) / len(item_scores) if item_scores else 0
        return max(0, avg_score - count_penalty)
    
    def _calculate_line_item_match(self, actual: dict, expected: dict) -> float:
        """
        Calculate match score for individual line item
        """
        score = 0.0
        
        # Material match (critical)
        if actual.get("material") == expected.get("material"):
            score += 0.3
        
        # Quantity match (critical)
        if actual.get("quantity") == expected.get("quantity"):
            score += 0.25
        
        # Dimensions match
        if self._dimensions_match(actual.get("dimensions", {}), expected.get("dimensions", {})):
            score += 0.2
        
        # Form/shape match
        if actual.get("form") == expected.get("form"):
            score += 0.15
        
        # Specifications match
        if self._specs_match(actual.get("specifications", {}), expected.get("specifications", {})):
            score += 0.1
        
        return score
```

### **2. Reasoning Quality Assessment (20% of score)**

```python
class ReasoningQualityEvaluator:
    """
    Evaluates the quality and coherence of multi-step reasoning chains
    """
    
    def evaluate_reasoning_chain(self, actual: ReasoningChain, expected: ReasoningChain) -> ReasoningScore:
        """
        Assess reasoning quality across multiple dimensions
        """
        
        # Decomposition quality (25%)
        decomposition_score = self._evaluate_decomposition(
            actual.requirement_components,
            expected.requirement_components
        )
        
        # Context recognition quality (25%)
        context_score = self._evaluate_context_recognition(
            actual.customer_context,
            expected.customer_context
        )
        
        # Complexity assessment quality (25%)
        complexity_score = self._evaluate_complexity_assessment(
            actual.complexity_assessment,
            expected.complexity_assessment
        )
        
        # Chain coherence quality (25%)
        coherence_score = self._evaluate_chain_coherence(
            actual.reasoning_path,
            expected.reasoning_path
        )
        
        return ReasoningScore(
            decomposition=decomposition_score,
            context=context_score,
            complexity=complexity_score,
            coherence=coherence_score,
            overall=self._weighted_average([
                (decomposition_score, 0.25),
                (context_score, 0.25),
                (complexity_score, 0.25),
                (coherence_score, 0.25)
            ])
        )
```

### **3. Business Intelligence Assessment (20% of score)**

```python
class BusinessIntelligenceEvaluator:
    """
    Evaluates business intelligence and commercial viability of reasoning
    """
    
    def evaluate_business_intelligence(self, actual: SalesOrderAnalysis, expected: SalesOrderAnalysis) -> BusinessScore:
        """
        Assess business intelligence across commercial dimensions
        """
        
        # Industry expertise demonstration (20%)
        industry_score = self._evaluate_industry_expertise(
            actual.customer_context.industry_sector,
            actual.reasoning_notes,
            expected.industry_insights
        )
        
        # Customer relationship intelligence (20%)
        relationship_score = self._evaluate_relationship_intelligence(
            actual.customer_context.customer_tier,
            actual.flexibility_score,
            expected.relationship_insights
        )
        
        # Emergency response appropriateness (20%)
        emergency_score = self._evaluate_emergency_response(
            actual.emergency_indicators,
            actual.complexity_assessment,
            expected.emergency_response
        )
        
        # Commercial value optimization (20%)
        commercial_score = self._evaluate_commercial_optimization(
            actual.fulfillment_strategies,
            expected.business_value_indicators
        )
        
        # Strategic thinking quality (20%)
        strategic_score = self._evaluate_strategic_thinking(
            actual.reasoning_notes,
            expected.strategic_insights
        )
        
        return BusinessScore(
            industry_expertise=industry_score,
            relationship_intelligence=relationship_score,
            emergency_response=emergency_score,
            commercial_optimization=commercial_score,
            strategic_thinking=strategic_score,
            overall=self._weighted_average([
                (industry_score, 0.20),
                (relationship_score, 0.20),
                (emergency_score, 0.20),
                (commercial_score, 0.20),
                (strategic_score, 0.20)
            ])
        )
```

### **4. LLM Judge Integration (10% of score)**

```python
class LLMJudgeScorer:
    """
    Uses GPT-4 as an expert judge for qualitative assessment
    """
    
    def __init__(self):
        self.judge_llm = ChatOpenAI(model="gpt-4", temperature=0.1)
        
    async def evaluate_with_llm_judge(self, sample: dict, actual_output: dict) -> LLMJudgeScore:
        """
        Use LLM judge for qualitative assessment of reasoning quality
        """
        
        judge_prompt = self._create_judge_prompt(sample, actual_output)
        
        judge_response = await self.judge_llm.ainvoke([
            {"role": "system", "content": self._get_judge_system_prompt()},
            {"role": "user", "content": judge_prompt}
        ])
        
        # Parse structured response
        judge_scores = self._parse_judge_response(judge_response.content)
        
        return LLMJudgeScore(
            reasoning_coherence=judge_scores.get("reasoning_coherence", 0.0),
            business_insight_quality=judge_scores.get("business_insight", 0.0),
            customer_satisfaction_prediction=judge_scores.get("customer_satisfaction", 0.0),
            commercial_viability=judge_scores.get("commercial_viability", 0.0),
            expert_assessment=judge_scores.get("expert_assessment", 0.0),
            qualitative_feedback=judge_scores.get("feedback", ""),
            overall=judge_scores.get("overall_score", 0.0)
        )
    
    def _get_judge_system_prompt(self) -> str:
        return """You are an expert sales engineer and procurement specialist evaluating AI-powered sales order intelligence.

Assess the quality of sales order analysis and fulfillment strategy generation across these dimensions:

1. **Reasoning Coherence** (0-10): How logical and well-structured is the reasoning chain?
2. **Business Insight Quality** (0-10): How well does the system understand business context and implications?
3. **Customer Satisfaction Prediction** (0-10): How likely is the customer to be satisfied with this response?
4. **Commercial Viability** (0-10): How commercially sound are the proposed strategies?
5. **Expert Assessment** (0-10): Overall quality from a domain expert perspective

Provide scores and detailed feedback in JSON format."""
```

### **5. Performance & Scalability Testing (10% of score)**

```python
class PerformanceEvaluator:
    """
    Evaluates operational performance characteristics
    """
    
    def evaluate_performance(self, execution_results: List[ExecutionResult]) -> PerformanceScore:
        """
        Assess operational performance across key metrics
        """
        
        # Latency analysis
        latency_score = self._evaluate_latency(execution_results)
        
        # Throughput analysis  
        throughput_score = self._evaluate_throughput(execution_results)
        
        # Resource utilization
        resource_score = self._evaluate_resource_usage(execution_results)
        
        # Error handling
        reliability_score = self._evaluate_reliability(execution_results)
        
        # Scalability characteristics
        scalability_score = self._evaluate_scalability(execution_results)
        
        return PerformanceScore(
            latency=latency_score,
            throughput=throughput_score,
            resource_efficiency=resource_score,
            reliability=reliability_score,
            scalability=scalability_score,
            overall=self._weighted_average([
                (latency_score, 0.25),
                (throughput_score, 0.20),
                (resource_score, 0.20),
                (reliability_score, 0.20),
                (scalability_score, 0.15)
            ])
        )
```

## 🚀 **Implementation Strategy**

### **Phase 1: Core Framework (Week 1)**
1. Implement OpenAI Evals compatible base classes
2. Create JSONL sample format and management system
3. Build rule-based scoring engine
4. Integrate with existing Phase 2 reasoning framework

### **Phase 2: Advanced Scoring (Week 2)**  
1. Implement LLM judge integration
2. Build business intelligence evaluator
3. Create performance tracking system
4. Add comprehensive metrics reporting

### **Phase 3: Test Expansion (Week 3)**
1. Generate 100+ diverse test cases
2. Implement automated test case generation
3. Add edge case and stress testing
4. Create industry-specific test suites

### **Phase 4: Production Integration (Week 4)**
1. CI/CD pipeline integration
2. Real-time monitoring capabilities
3. A/B testing framework
4. Regression testing automation

This evaluation framework provides comprehensive, production-ready testing that's fully compatible with OpenAI's evals system while addressing the specific needs of sales order intelligence evaluation. It enables both detailed analysis and automated quality gates for continuous improvement.
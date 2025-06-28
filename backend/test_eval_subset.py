#!/usr/bin/env python3
"""
Test subset of evaluation cases to validate fixes
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.mcp.reasoning_framework import SalesOrderReasoningFramework


# Import just the first 5 test cases
CUSTOMER_EMAILS = [
    {
        "test_id": "001",
        "category": "Emergency Production - Major Auto",
        "customer": "Ford Motor Company - Dearborn Plant",
        "subject": "URGENT: Production Line Down - Need SS316L Tubing ASAP",
        "email_body": """EMERGENCY REQUEST - PRODUCTION CRITICAL
        
Our stamping line #3 is down due to hydraulic failure. Need immediate replacement:

- Stainless Steel 316L seamless tubing
- 2.5" OD x 0.065" wall thickness 
- Length: 48" pieces (need 6 pieces minimum)
- Pressure rating: 3000 PSI minimum
- Mill cert required

Production impact: $85K per hour downtime
Need delivery by tomorrow 2PM latest

Contact: Mike Rodriguez, Production Manager
Direct: 313-555-0147
This is affecting F-150 production schedule.

Best regards,
Mike Rodriguez
Ford Motor Company - Dearborn Stamping Plant""",
        "expected_complexity": "CRITICAL",
        "expected_industry": "automotive", 
        "expected_emergency": True,
        "expected_strategies": ["exact_match", "expedited_restock", "custom_solution"]
    },
    
    {
        "test_id": "002", 
        "category": "Precision Aerospace - Small Supplier",
        "customer": "Precision Aerospace Components LLC",
        "subject": "RFQ: Ti-6Al-4V bars for Boeing subcontract",
        "email_body": """Dear Supplier,

We are a Tier 2 supplier to Boeing and require the following for aircraft landing gear components:

Material: Titanium 6Al-4V (Grade 5)
Form: Round bar stock
Diameter: 3.25" +/- 0.005"
Length: 12" lengths
Quantity: 15 pieces
Certifications Required:
- AS9100 Rev D compliant
- Material certs per AMS 4928
- Full traceability to heat lot

This is for 737 MAX landing gear assemblies. Boeing audit trail required.
Need quote by Friday, delivery in 3 weeks.

Project: BNG-LG-4472
PO will follow upon quote approval.

Thanks,
Jennifer Chen, Materials Manager
Precision Aerospace Components LLC
AS9100 Certified Facility
CAGE Code: 7H429""",
        "expected_complexity": "COMPLEX",
        "expected_industry": "aerospace",
        "expected_emergency": False,
        "expected_strategies": ["exact_match", "expedited_restock"]
    },

    {
        "test_id": "003",
        "category": "Research Institution - Informal",
        "customer": "MIT Materials Science Lab",
        "subject": "need some aluminum samples for testing",
        "email_body": """hey there,

prof johnson here from MIT materials lab. we're doing some fatigue testing and need aluminum samples. not sure exactly what grades yet but thinking:

- aluminum 6061-T6 
- aluminum 7075-T6
- maybe some 2024-T3 if you have it

sizes around 1" x 6" strips, thickness doesn't matter much, maybe 0.25" ish?
need like 20-30 pieces total, mixed grades ok

this is for NSF grant research on crack propagation. budget is tight but we can pay net 30 if that works.

student pickup ok? we're in cambridge.

thanks!
prof j
MIT materials lab
room 8-139""",
        "expected_complexity": "SIMPLE",
        "expected_industry": "research_development", 
        "expected_emergency": False,
        "expected_strategies": ["exact_match", "alternative_products", "split_shipment"]
    },

    {
        "test_id": "004",
        "category": "Medical Device - Regulatory Critical",
        "customer": "BioMed Implants Corporation",
        "subject": "URGENT: FDA submission deadline - 316LVM surgical steel",
        "email_body": """CRITICAL REQUEST - FDA SUBMISSION DEADLINE

We have an FDA 510(k) submission deadline of December 15th and require:

MATERIAL: 316LVM Stainless Steel (Vacuum Melted)
SPECIFICATIONS:
- Round bar: 0.375" diameter ± 0.001"
- Length: 6" pieces
- Quantity: 50 pieces
- Surface finish: 32 Ra max
- ASTM F138 compliant

CRITICAL REQUIREMENTS:
✓ Full biocompatibility testing certificates
✓ USP Class VI certification
✓ Material traceability to heat number
✓ ISO 13485 supplier qualification
✓ Endotoxin testing documentation

This material is for cardiac stent prototypes. FDA is expecting submission with material certs included.

DELIVERY NEEDED: By December 10th
BUDGET APPROVED: Up to $15K for expedited processing

Please confirm availability immediately.

Best regards,
Dr. Sarah Kim, VP Engineering
BioMed Implants Corporation
FDA Registered Facility #12345678
ISO 13485:2016 Certified""",
        "expected_complexity": "CRITICAL",
        "expected_industry": "medical_device",
        "expected_emergency": True,
        "expected_strategies": ["exact_match", "expedited_restock"]
    },

    {
        "test_id": "005",
        "category": "Small Machine Shop - Cost Conscious", 
        "customer": "Joe's Precision Machining",
        "subject": "Quote request - steel bar stock",
        "email_body": """Hi,

Small family shop here, been in business 35 years. Need some steel for a local job:

4140 steel round bar
- 2" diameter  
- 36" lengths
- Need 8 pieces

Customer is a local farm equipment manufacturer, nothing fancy. Standard mill tolerance fine.

What's your best price? We usually buy from local suppliers but they're out of stock. Need delivery next week.

Can pay COD or check on delivery.

Thanks,
Joe Kowalski  
Joe's Precision Machining
Family owned since 1988""",
        "expected_complexity": "SIMPLE",
        "expected_industry": "general_manufacturing",
        "expected_emergency": False,
        "expected_strategies": ["exact_match", "alternative_products"]
    }
]


async def evaluate_customer_email(test_case, framework):
    """Evaluate a single customer email with Phase 2 intelligence"""
    
    print(f"\n{'='*80}")
    print(f"🧪 TEST {test_case['test_id']}: {test_case['category']}")
    print(f"📧 Customer: {test_case['customer']}")
    print(f"{'='*80}")
    
    # Analyze with Phase 2 Sales Order Intelligence
    analysis = await framework.analyze_sales_order(
        test_case['email_body'], 
        test_case['customer']
    )
    
    # Generate fulfillment strategies
    strategies = await framework.generate_fulfillment_strategies(analysis)
    
    # Evaluation results
    results = {
        'test_id': test_case['test_id'],
        'complexity_detected': analysis.complexity_assessment.value,
        'industry_detected': analysis.customer_context.industry_sector,
        'emergency_detected': len(analysis.emergency_indicators) > 0,
        'top_strategy': strategies[0].strategy_type.value if strategies else 'none',
        
        # Expected vs Actual (case-insensitive comparison for complexity)
        'complexity_correct': analysis.complexity_assessment.value.upper() == test_case['expected_complexity'].upper(),
        'industry_correct': analysis.customer_context.industry_sector == test_case['expected_industry'],
        'emergency_correct': (len(analysis.emergency_indicators) > 0) == test_case['expected_emergency'],
        'strategies_appropriate': strategies[0].strategy_type.value in test_case['expected_strategies'] if strategies else False,
    }
    
    # Print results
    print(f"🧠 ANALYSIS RESULTS:")
    print(f"   Complexity: {results['complexity_detected']} (expected: {test_case['expected_complexity']}) {'✅' if results['complexity_correct'] else '❌'}")
    print(f"   Industry: {results['industry_detected']} (expected: {test_case['expected_industry']}) {'✅' if results['industry_correct'] else '❌'}")
    print(f"   Emergency: {results['emergency_detected']} (expected: {test_case['expected_emergency']}) {'✅' if results['emergency_correct'] else '❌'}")
    print(f"   Top Strategy: {results['top_strategy']} (expected: {test_case['expected_strategies']}) {'✅' if results['strategies_appropriate'] else '❌'}")
    
    overall_correct = (results['complexity_correct'] and results['industry_correct'] and 
                      results['emergency_correct'] and results['strategies_appropriate'])
    print(f"   📊 Overall: {'✅ PASS' if overall_correct else '❌ FAIL'}")
    
    return results


async def run_subset_evaluation():
    """Run evaluation on subset of test cases"""
    
    print("🧪 SUBSET EVALUATION - Phase 2 Sales Order Intelligence")
    print(f"Testing {len(CUSTOMER_EMAILS)} representative scenarios")
    print("="*80)
    
    framework = SalesOrderReasoningFramework()
    all_results = []
    
    for test_case in CUSTOMER_EMAILS:
        result = await evaluate_customer_email(test_case, framework)
        all_results.append(result)
    
    # Calculate accuracy
    total_tests = len(all_results)
    complexity_accuracy = sum(1 for r in all_results if r['complexity_correct']) / total_tests
    industry_accuracy = sum(1 for r in all_results if r['industry_correct']) / total_tests  
    emergency_accuracy = sum(1 for r in all_results if r['emergency_correct']) / total_tests
    strategy_accuracy = sum(1 for r in all_results if r['strategies_appropriate']) / total_tests
    overall_accuracy = sum(1 for r in all_results if (r['complexity_correct'] and r['industry_correct'] and r['emergency_correct'] and r['strategies_appropriate'])) / total_tests
    
    print(f"\n{'='*80}")
    print("📊 SUBSET EVALUATION RESULTS")
    print(f"{'='*80}")
    print(f"🎯 ACCURACY METRICS:")
    print(f"   Complexity Detection: {complexity_accuracy:.1%} ({sum(1 for r in all_results if r['complexity_correct'])}/{total_tests})")
    print(f"   Industry Recognition: {industry_accuracy:.1%} ({sum(1 for r in all_results if r['industry_correct'])}/{total_tests})")
    print(f"   Emergency Detection: {emergency_accuracy:.1%} ({sum(1 for r in all_results if r['emergency_correct'])}/{total_tests})")
    print(f"   Strategy Appropriateness: {strategy_accuracy:.1%} ({sum(1 for r in all_results if r['strategies_appropriate'])}/{total_tests})")
    print(f"   📈 OVERALL ACCURACY: {overall_accuracy:.1%}")
    
    if overall_accuracy >= 0.8:
        print(f"\n🎉 SUBSET EVALUATION: ✅ EXCELLENT PERFORMANCE")
        print(f"Ready to run full evaluation with all 20 test cases!")
    else:
        print(f"\n⚠️ SUBSET EVALUATION: NEEDS IMPROVEMENT")
        print(f"Fix issues before running full evaluation")
    
    return overall_accuracy >= 0.8


if __name__ == "__main__":
    success = asyncio.run(run_subset_evaluation())
    print(f"\nSubset evaluation {'PASSED' if success else 'FAILED'}")
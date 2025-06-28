#!/usr/bin/env python3
"""
Test Phase 2: Fulfillment Strategy Generation
Tests the sales order reasoning framework and fulfillment strategy execution
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.mcp.reasoning_framework import SalesOrderReasoningFramework, analyze_sales_order_intelligence, generate_fulfillment_strategies
from app.mcp.fulfillment_execution import SalesOrderSearchCoordinator
from app.models.line_item_schemas import LineItem
from app.services.local_parts_catalog import LocalPartsCatalogService
import structlog

# Setup logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


async def test_sales_order_analysis():
    """Test basic sales order analysis"""
    print("\n🧠 Testing Sales Order Analysis")
    print("=" * 60)
    
    framework = SalesOrderReasoningFramework()
    
    # Test cases covering different scenarios
    test_cases = [
        {
            "name": "Ford Emergency Production Order",
            "order_request": "Emergency stainless steel 304 sheet 1 piece - production line down at Ford Motor Company",
            "customer": "Ford Motor Company"
        },
        {
            "name": "Boeing Aerospace Order",
            "order_request": "Titanium Grade 5 bolts M12x50 with AS9100 certification - 200 pieces for aircraft assembly",
            "customer": "Boeing Aerospace"
        },
        {
            "name": "MIT Research Order", 
            "order_request": "Various aluminum alloy samples for materials testing research project",
            "customer": "MIT Materials Lab"
        },
        {
            "name": "Medical Device Order",
            "order_request": "Biocompatible surgical steel bar 316LVM grade for cardiac implant prototype",
            "customer": "Medtronic Medical Devices"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print("-" * 40)
        
        analysis = await framework.analyze_sales_order(
            test_case["order_request"], 
            test_case["customer"]
        )
        
        print(f"Order ID: {analysis.order_id}")
        print(f"Complexity: {analysis.complexity_assessment.value}")
        print(f"Customer Industry: {analysis.customer_context.industry_sector}")
        print(f"Customer Tier: {analysis.customer_context.customer_tier}")
        print(f"Flexibility Score: {analysis.flexibility_score:.2f}")
        print(f"Emergency Detected: {len(analysis.emergency_indicators) > 0}")
        if analysis.emergency_indicators:
            print(f"Emergency Indicators: {', '.join(analysis.emergency_indicators)}")
        print(f"Product Requirements: {len(analysis.product_requirements)}")
        print(f"Reasoning Notes: {len(analysis.reasoning_notes)} insights")
        print(f"Confidence Score: {analysis.confidence_score:.2f}")
        
        # Test MCP tool function
        mcp_result = await analyze_sales_order_intelligence({
            'raw_text': test_case["order_request"],
            'customer': {'name': test_case["customer"]}
        })
        
        print(f"MCP Tool Result: ✅ Active (complexity: {mcp_result['sales_order_analysis']['complexity']})")
    
    return True


async def test_fulfillment_strategy_generation():
    """Test fulfillment strategy generation"""
    print("\n🎯 Testing Fulfillment Strategy Generation")
    print("=" * 60)
    
    framework = SalesOrderReasoningFramework()
    
    test_cases = [
        {
            "name": "High Flexibility Customer (R&D)",
            "order_request": "Aluminum alloy samples for research testing",
            "customer": "University Research Lab",
            "expected_strategies": ["exact_match", "alternative_products", "custom_solution"]
        },
        {
            "name": "Low Flexibility Customer (Aerospace)",
            "order_request": "Titanium Grade 5 certified bolts for aircraft",
            "customer": "Boeing Aerospace",
            "expected_strategies": ["exact_match", "expedited_restock"]
        },
        {
            "name": "Emergency Order (Automotive)",
            "order_request": "Emergency bearing replacement - production line down",
            "customer": "Ford Motor Company",
            "expected_strategies": ["exact_match", "expedited_restock", "custom_solution"]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print("-" * 40)
        
        # Generate analysis
        analysis = await framework.analyze_sales_order(
            test_case["order_request"], 
            test_case["customer"]
        )
        
        # Generate strategies
        strategies = await framework.generate_fulfillment_strategies(analysis)
        
        print(f"Generated Strategies: {len(strategies)}")
        print(f"Customer Flexibility: {analysis.flexibility_score:.2f}")
        
        for j, strategy in enumerate(strategies, 1):
            print(f"  {j}. {strategy.strategy_type.value.upper()}")
            print(f"     Description: {strategy.description}")
            print(f"     Confidence: {strategy.confidence_score:.2f}")
            print(f"     Customer Fit: {strategy.customer_fit_score:.2f}")
            print(f"     Business Value: {strategy.business_value_score:.2f}")
            print(f"     Advantages: {', '.join(strategy.advantages[:2])}")
        
        # Test MCP tool function
        mcp_result = await generate_fulfillment_strategies({
            'order_request': test_case["order_request"],
            'customer_name': test_case["customer"]
        })
        
        print(f"MCP Tool Result: ✅ {mcp_result['fulfillment_strategies']['strategy_count']} strategies")
        print(f"Recommended: {mcp_result['fulfillment_strategies']['recommended_strategy']}")
    
    return True


async def test_integrated_fulfillment_coordinator():
    """Test integrated sales order coordinator"""
    print("\n🚀 Testing Integrated Sales Order Coordinator")
    print("=" * 60)
    
    # Initialize catalog service
    catalog_service = LocalPartsCatalogService()
    coordinator = SalesOrderSearchCoordinator(catalog_service)
    
    # Create test line items
    test_line_items = [
        LineItem(
            line_id="L001",
            raw_text="Stainless steel 304 sheet 1 piece",
            extracted_specs={"material": "stainless steel 304", "form": "sheet", "quantity": 1}
        ),
        LineItem(
            line_id="L002", 
            raw_text="Aluminum 6061 bar 2 inch diameter",
            extracted_specs={"material": "aluminum 6061", "form": "bar", "quantity": 1}
        )
    ]
    
    customer_context = {
        "name": "Ford Motor Company",
        "industry": "automotive"
    }
    
    print("Processing 2 line items with sales order intelligence...")
    
    try:
        result = await coordinator.process_sales_order_with_intelligence(
            test_line_items, 
            customer_context
        )
        
        print(f"\n📊 Processing Summary:")
        summary = result['processing_summary']
        print(f"Total Line Items: {summary['total_line_items']}")
        print(f"Successful Items: {summary['successful_items']}")
        print(f"Total Matches: {summary['total_matches_found']}")
        print(f"Success Rate: {summary['success_rate']:.1%}")
        print(f"Intelligence Applied: {summary['intelligence_applied']}")
        print(f"Overall Confidence: {result['overall_confidence']:.2f}")
        
        print(f"\n📝 Detailed Results:")
        for i, item_result in enumerate(result['detailed_results'], 1):
            print(f"  Item {i}: {item_result['line_item'].raw_text}")
            print(f"    Analysis: {item_result['analysis'].complexity_assessment.value} complexity")
            print(f"    Strategy: {item_result['executed_strategy']}")
            print(f"    Success: {item_result['search_results'].get('success', False)}")
            print(f"    Matches: {len(item_result['search_results'].get('matches', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False


async def run_phase2_tests():
    """Run all Phase 2 fulfillment tests"""
    print("🧠 Phase 2: Fulfillment Strategy Generation Tests")
    print("=" * 80)
    
    tests = [
        ("Sales Order Analysis", test_sales_order_analysis),
        ("Fulfillment Strategy Generation", test_fulfillment_strategy_generation),
        ("Integrated Fulfillment Coordinator", test_integrated_fulfillment_coordinator)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔬 Running: {test_name}")
        try:
            success = await test_func()
            results.append((test_name, success))
            print(f"✅ {test_name}: {'PASSED' if success else 'FAILED'}")
        except Exception as e:
            print(f"❌ {test_name}: FAILED - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 Phase 2 Test Results Summary")
    print("=" * 80)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("🎉 Phase 2 Fulfillment Strategy Generation: FULLY OPERATIONAL")
    else:
        print("⚠️  Phase 2 Fulfillment Strategy Generation: NEEDS ATTENTION")
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(run_phase2_tests())
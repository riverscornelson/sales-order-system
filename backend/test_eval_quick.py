#!/usr/bin/env python3
"""
Quick validation of eval fixes
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.mcp.reasoning_framework import SalesOrderReasoningFramework


async def quick_test():
    framework = SalesOrderReasoningFramework()
    
    # Test case 1: Ford emergency
    analysis = await framework.analyze_sales_order(
        "Emergency stainless steel 304 sheet 1 piece - production line down at Ford Motor Company",
        "Ford Motor Company - Dearborn Plant"
    )
    
    print(f"Test 1 Results:")
    print(f"  Complexity: '{analysis.complexity_assessment.value}' (type: {type(analysis.complexity_assessment.value)})")
    print(f"  Expected: 'CRITICAL'")
    print(f"  Match (case-insensitive): {analysis.complexity_assessment.value.upper() == 'CRITICAL'}")
    print(f"  Industry: '{analysis.customer_context.industry_sector}'")
    print(f"  Emergency indicators: {len(analysis.emergency_indicators)} found")
    
    strategies = await framework.generate_fulfillment_strategies(analysis)
    print(f"  Strategies: {[s.strategy_type.value for s in strategies]}")
    print(f"  Top strategy: '{strategies[0].strategy_type.value if strategies else 'none'}'")
    print(f"  Expected strategies: ['exact_match', 'expedited_restock', 'custom_solution']")
    print(f"  Strategy match: {strategies[0].strategy_type.value in ['exact_match', 'expedited_restock', 'custom_solution'] if strategies else False}")

if __name__ == "__main__":
    asyncio.run(quick_test())
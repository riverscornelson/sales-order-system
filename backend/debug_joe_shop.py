#!/usr/bin/env python3
"""
Debug Joe's shop complexity
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.mcp.reasoning_framework import SalesOrderReasoningFramework


async def debug_joe_shop():
    framework = SalesOrderReasoningFramework()
    
    joe_request = """Hi,

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
Family owned since 1988"""
    
    print("Joe's Shop Analysis:")
    print("=" * 50)
    
    analysis = await framework.analyze_sales_order(joe_request, "Joe's Precision Machining")
    
    print(f"Requirements: {len(analysis.product_requirements)}")
    for i, req in enumerate(analysis.product_requirements, 1):
        print(f"  {i}. {req.description}")
    
    print(f"Customer industry: {analysis.customer_context.industry_sector}")
    print(f"Customer tier: {analysis.customer_context.customer_tier}")
    print(f"Complexity: {analysis.complexity_assessment.value}")


if __name__ == "__main__":
    asyncio.run(debug_joe_shop())
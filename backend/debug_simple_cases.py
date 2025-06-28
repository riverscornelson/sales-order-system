#!/usr/bin/env python3
"""
Debug why simple cases are getting moderate complexity
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.mcp.reasoning_framework import SalesOrderReasoningFramework


async def debug_simple_cases():
    framework = SalesOrderReasoningFramework()
    
    # Test MIT case (should be SIMPLE)
    mit_request = """hey there,

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
room 8-139"""
    
    print("MIT Case Analysis:")
    print("=" * 50)
    
    analysis = await framework.analyze_sales_order(mit_request, "MIT Materials Science Lab")
    
    print(f"Requirements: {len(analysis.product_requirements)}")
    for i, req in enumerate(analysis.product_requirements, 1):
        print(f"  {i}. {req.description}")
    
    print(f"Customer industry: {analysis.customer_context.industry_sector}")
    print(f"Complexity: {analysis.complexity_assessment.value}")
    
    # Manual complexity calculation
    complexity_score = 0
    
    # Base complexity (>5 requirements)
    if len(analysis.product_requirements) > 5:
        complexity_score += 1
        print(f"Base complexity (+1): {len(analysis.product_requirements)} requirements")
    
    # Industry complexity  
    if analysis.customer_context.industry_sector == "research_development":
        print("Industry complexity (+0): research_development")
    
    # Emergency indicators
    emergency_found = any(kw in mit_request.lower() for kw in ["emergency", "production down", "critical", "asap", "urgent"])
    if emergency_found:
        complexity_score += 1
        print("Emergency indicators (+1)")
    else:
        print("Emergency indicators (+0)")
    
    print(f"Total complexity score: {complexity_score}")
    
    # Expected mapping
    if complexity_score >= 5:
        expected = "CRITICAL"
    elif complexity_score >= 3:
        expected = "COMPLEX" 
    elif complexity_score >= 1:
        expected = "MODERATE"
    else:
        expected = "SIMPLE"
    
    print(f"Expected: {expected}")
    print(f"Actual: {analysis.complexity_assessment.value.upper()}")


if __name__ == "__main__":
    asyncio.run(debug_simple_cases())
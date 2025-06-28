#!/usr/bin/env python3
"""
Debug complexity scoring
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.mcp.reasoning_framework import SalesOrderReasoningFramework


async def debug_complexity():
    framework = SalesOrderReasoningFramework()
    
    order_request = "Emergency stainless steel 304 sheet 1 piece - production line down at Ford Motor Company"
    customer_name = "Ford Motor Company - Dearborn Plant"
    
    # Get the analysis
    analysis = await framework.analyze_sales_order(order_request, customer_name)
    
    print(f"Order Request: {order_request}")
    print(f"Customer: {customer_name}")
    print()
    print(f"Requirements count: {len(analysis.product_requirements)}")
    print(f"Customer industry: {analysis.customer_context.industry_sector}")
    print(f"Customer tier: {analysis.customer_context.customer_tier}")
    print()
    
    # Manual complexity calculation
    complexity_score = 0
    print("Complexity Scoring:")
    
    # Base complexity factors  
    if len(analysis.product_requirements) > 3:
        complexity_score += 1
        print(f"  Base complexity (>3 requirements): +1")
    else:
        print(f"  Base complexity ({len(analysis.product_requirements)} requirements): +0")
    
    # Customer industry complexity
    if analysis.customer_context.industry_sector in ["aerospace", "medical_device"]:
        complexity_score += 2
        print(f"  Industry complexity (aerospace/medical): +2")
    elif analysis.customer_context.industry_sector == "automotive":
        complexity_score += 1 
        print(f"  Industry complexity (automotive): +1")
    else:
        print(f"  Industry complexity (other): +0")
    
    # Urgency complexity
    critical_urgency = any(req.urgency_level == "critical" for req in analysis.product_requirements)
    if critical_urgency:
        complexity_score += 2
        print(f"  Urgency complexity (critical): +2")
    else:
        print(f"  Urgency complexity (not critical): +0")
        print(f"    Requirement urgency levels: {[req.urgency_level for req in analysis.product_requirements]}")
    
    # Timeline complexity - check if any requirements have urgent delivery
    from datetime import datetime, timedelta
    urgent_timeline = any(req.delivery_timeline and req.delivery_timeline < datetime.now() + timedelta(days=1) 
                         for req in analysis.product_requirements)
    if urgent_timeline:
        complexity_score += 1
        print(f"  Timeline complexity (urgent): +1")
    else:
        print(f"  Timeline complexity (not urgent): +0")
        print(f"    Delivery timelines: {[req.delivery_timeline for req in analysis.product_requirements]}")
    
    # Emergency indicators
    emergency_keywords = ["emergency", "production down", "critical", "asap", "urgent"]
    critical_emergency_keywords = ["production down", "line down", "plant shutdown", "production critical"]
    
    critical_emergency_found = any(keyword in order_request.lower() for keyword in critical_emergency_keywords)
    emergency_found = any(keyword in order_request.lower() for keyword in emergency_keywords)
    
    if critical_emergency_found:
        complexity_score += 2
        print(f"  Critical emergency indicators: +2")
        found_critical_keywords = [kw for kw in critical_emergency_keywords if kw in order_request.lower()]
        print(f"    Found critical keywords: {found_critical_keywords}")
    elif emergency_found:
        complexity_score += 1
        print(f"  Emergency indicators: +1")
        found_keywords = [kw for kw in emergency_keywords if kw in order_request.lower()]
        print(f"    Found keywords: {found_keywords}")
    else:
        print(f"  Emergency indicators: +0")
    
    print()
    print(f"Total Complexity Score: {complexity_score}")
    
    # Map to complexity levels
    if complexity_score >= 5:
        expected_complexity = "CRITICAL"
    elif complexity_score >= 3:
        expected_complexity = "COMPLEX"
    elif complexity_score >= 1:
        expected_complexity = "MODERATE"
    else:
        expected_complexity = "SIMPLE"
    
    print(f"Expected Complexity: {expected_complexity}")
    print(f"Actual Complexity: {analysis.complexity_assessment.value.upper()}")
    print(f"Match: {analysis.complexity_assessment.value.upper() == expected_complexity}")


if __name__ == "__main__":
    asyncio.run(debug_complexity())
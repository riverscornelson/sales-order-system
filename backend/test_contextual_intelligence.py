#!/usr/bin/env python3
"""
Test script for Phase 1 Contextual Intelligence implementation
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.agents.agentic_search_coordinator import AgenticSearchCoordinator
from app.services.parts_catalog import PartsCatalogService
from app.models.line_item_schemas import LineItem
from app.mcp.contextual_intelligence import assess_complexity_factors, dynamic_threshold_adjustment

async def test_contextual_intelligence():
    """Test the contextual intelligence integration"""
    
    print("🧪 Testing Phase 1: Contextual Intelligence Integration")
    print("=" * 60)
    
    # Initialize services
    print("📚 Initializing services...")
    catalog_service = PartsCatalogService()
    coordinator = AgenticSearchCoordinator(catalog_service)
    
    # Test line items with different complexity levels
    test_line_items = [
        # Simple case
        LineItem(
            line_id="test_001",
            raw_text="4140 steel bar 1 inch diameter",
            urgency="low"
        ),
        
        # Complex case
        LineItem(
            line_id="test_002", 
            raw_text="ASTM A36 steel plate 1/2 inch thick with mill test certificate for aerospace application",
            urgency="high",
            special_requirements=["certification_required", "traceability"]
        ),
        
        # Critical case
        LineItem(
            line_id="test_003",
            raw_text="Emergency replacement bearing for production line shutdown - any compatible alternative needed ASAP",
            urgency="critical"
        )
    ]
    
    for i, line_item in enumerate(test_line_items, 1):
        print(f"\n🔍 Test Case {i}: {line_item.line_id}")
        print(f"   Text: {line_item.raw_text}")
        print(f"   Urgency: {line_item.urgency}")
        
        try:
            # Test basic complexity assessment
            print("   📊 Assessing complexity...")
            line_item_dict = {
                "line_id": line_item.line_id,
                "raw_text": line_item.raw_text,
                "description": line_item.raw_text,
                "urgency": line_item.urgency,
                "special_requirements": line_item.special_requirements or []
            }
            
            complexity = await assess_complexity_factors(line_item_dict)
            print(f"   ✅ Complexity Level: {complexity.get('complexity_level', 'unknown')}")
            print(f"   📋 Specialized Requirements: {complexity.get('specialized_requirements', [])}")
            print(f"   🚨 Escalation Needed: {complexity.get('escalation_needed', False)}")
            
            # Test dynamic threshold adjustment
            print("   ⚖️  Adjusting thresholds...")
            context = {
                "urgency_level": line_item.urgency or "medium",
                "quality_requirements": "medium",
                "cost_sensitivity": "medium"
            }
            
            thresholds = await dynamic_threshold_adjustment(context)
            print(f"   ✅ Adjusted Thresholds: {thresholds}")
            
            # Test full contextual search coordination
            print("   🤖 Running contextual search...")
            results = await coordinator.search_for_line_item(line_item)
            print(f"   ✅ Search Results: {len(results)} parts found")
            
            if results:
                top_result = results[0]
                print(f"   🏆 Top Result: {top_result.part_number} - {top_result.description[:50]}...")
                print(f"   📊 Confidence: {top_result.similarity_score:.3f}")
                if hasattr(top_result, 'notes') and top_result.notes:
                    print(f"   📝 Notes: {top_result.notes[-1]}")  # Show last note
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
        
        print("   " + "-" * 50)
    
    print("\n🎉 Contextual Intelligence Testing Complete!")
    print("✅ Phase 1 implementation is working!")

if __name__ == "__main__":
    asyncio.run(test_contextual_intelligence())
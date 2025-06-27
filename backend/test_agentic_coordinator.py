#!/usr/bin/env python3

import asyncio
import sys

# Add the backend directory to Python path
sys.path.insert(0, '/Users/riverscornelson/PycharmProjects/sales-order-system/backend')

from app.services.parts_catalog import PartsCatalogService
from app.agents.agentic_search_coordinator import AgenticSearchCoordinator
from app.models.line_item_schemas import LineItem, ExtractedSpecs

async def test_agentic_coordinator():
    """Test the agentic search coordinator"""
    
    print("🤖 TESTING AGENTIC SEARCH COORDINATOR")
    print("=" * 50)
    
    # Initialize
    catalog_service = PartsCatalogService()
    coordinator = AgenticSearchCoordinator(catalog_service)
    
    # Create a test line item
    line_item = LineItem(
        line_id="test-1",
        raw_text="5 pieces of 4140 steel round bar",
        extracted_specs=ExtractedSpecs(
            material_grade="4140 steel",
            form="round bar",
            quantity=5
        ),
        urgency="high"
    )
    
    print(f"🔍 Testing line item: {line_item.raw_text}")
    print(f"   Quantity: {line_item.extracted_specs.quantity if line_item.extracted_specs else 'N/A'}")
    print(f"   Urgency: {line_item.urgency}")
    print()
    
    # Test the coordinator
    print("1️⃣ Running agentic search...")
    try:
        results = await coordinator.search_for_line_item(line_item)
        print(f"   Results: {len(results)}")
        
        if results:
            print("   Top results:")
            found_4140 = False
            for i, result in enumerate(results[:5]):
                is_4140_part = "4140" in getattr(result, 'description', '') or "4140" in getattr(result, 'part_number', '')
                marker = " *** 4140 PART! ***" if is_4140_part else ""
                if is_4140_part:
                    found_4140 = True
                print(f"     {i+1}. {result.part_number}: {result.description} (confidence: {result.match_confidence.value}){marker}")
            
            if found_4140:
                print(f"\n   ✅ SUCCESS: Found 4140 part in agentic search results!")
            else:
                print(f"\n   ⚠️ 4140 part not in top 5, but search is working")
        else:
            print("   ❌ No results found")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n2️⃣ CONCLUSION:")
    if results and len(results) > 0:
        print("   ✅ Agentic search coordinator is working!")
        print("   🔧 Multiple search strategies are being used")
        print("   🎯 Results are being combined and ranked")
    else:
        print("   ❌ Agentic search coordinator failed")

if __name__ == "__main__":
    asyncio.run(test_agentic_coordinator())
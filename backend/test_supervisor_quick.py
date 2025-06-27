#!/usr/bin/env python3

import asyncio
import sys

# Add the backend directory to Python path
sys.path.insert(0, '/Users/riverscornelson/PycharmProjects/sales-order-system/backend')

from app.agents.supervisor_local import LocalSupervisorAgent

async def test_supervisor_quick():
    """Quick test of the supervisor with the urgent order"""
    
    print("👨‍💼 TESTING LOCAL SUPERVISOR (QUICK)")
    print("=" * 50)
    
    # Initialize supervisor
    supervisor = LocalSupervisorAgent()
    
    # Test with the urgent order (simplified)
    urgent_order_text = """
    URGENT RUSH ORDER - NEEDED IMMEDIATELY
    
    Please quote and deliver ASAP:
    - 5 pieces of 4140 alloy steel round bar, 2" diameter x 12" length
    
    This is for a critical production line repair.
    """
    
    print(f"📄 Processing urgent order...")
    print(f"   Text length: {len(urgent_order_text)} characters")
    print()
    
    # Process the order
    print("1️⃣ Running supervisor...")
    try:
        result = await supervisor.process_sales_order(urgent_order_text)
        
        print(f"   Success: {result.get('success', False)}")
        print(f"   Line items found: {len(result.get('line_items', []))}")
        
        line_items = result.get('line_items', [])
        if line_items:
            print("   Line items:")
            for i, item in enumerate(line_items):
                status = item.get('status', 'unknown')
                raw_text = item.get('raw_text', 'No text')[:60] + "..."
                print(f"     {i+1}. {raw_text} (status: {status})")
                
                # Check if search found results
                search_results = item.get('search_results', [])
                if search_results:
                    print(f"        Found {len(search_results)} search results")
                    # Check if 4140 part was found
                    found_4140 = any("4140" in str(result) for result in search_results[:3])
                    if found_4140:
                        print(f"        ✅ Found 4140 part in search results!")
                else:
                    print(f"        ❌ No search results")
        
        if result.get('success') and line_items:
            print(f"\n   ✅ SUCCESS: Supervisor processed the order successfully!")
        else:
            print(f"\n   ⚠️ PARTIAL: Order processed but may have issues")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n2️⃣ CONCLUSION:")
    print("   Testing if the full pipeline works with our semantic search fix")

if __name__ == "__main__":
    asyncio.run(test_supervisor_quick())
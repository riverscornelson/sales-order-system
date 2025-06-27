#!/usr/bin/env python3
"""
Test script to verify the local parts database is working
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.database.connection import get_db_manager
from app.services.local_parts_catalog import LocalPartsCatalogService

async def test_database():
    """Test the local parts database functionality"""
    
    print("🔍 Testing Local Parts Database")
    print("=" * 50)
    
    try:
        # Test 1: Database connection
        print("\n1. Testing database connection...")
        db_manager = get_db_manager()
        stats = db_manager.get_database_stats()
        print(f"   ✅ Connected to database")
        print(f"   📊 Total parts: {stats['total_parts']:,}")
        
        # Test 2: Parts catalog service
        print("\n2. Testing parts catalog service...")
        catalog = LocalPartsCatalogService()
        health = await catalog.check_health()
        print(f"   ✅ Service status: {health['status']}")
        
        # Test 3: Search functionality
        print("\n3. Testing search functionality...")
        
        # Test searches
        test_queries = [
            "stainless steel",
            "aluminum 6061",
            "1/4 inch",
            "304 sheet",
            "bolt",
            "bearing"
        ]
        
        for query in test_queries:
            results = await catalog.search_parts(query, top_k=3)
            print(f"   🔍 '{query}': {len(results)} results")
            
            if results:
                best_match = results[0]
                score = best_match.get("scores", {}).get("combined_score", 0)
                print(f"      🎯 Best: {best_match.get('part_number')} (score: {score:.3f})")
                print(f"      📝 {best_match.get('description', '')[:80]}...")
        
        # Test 4: Category and material filters
        print("\n4. Testing filters...")
        categories = catalog.get_categories()
        materials = catalog.get_materials()
        
        print(f"   📂 Available categories: {len(categories)}")
        for cat in categories[:5]:  # Show first 5
            print(f"      - {cat['category']}: {cat['part_count']} parts")
        
        print(f"   🔬 Available materials: {len(materials)}")
        for mat in materials[:5]:  # Show first 5
            print(f"      - {mat}")
        
        # Test 5: Specific part lookup
        print("\n5. Testing specific part lookup...")
        
        # Get a sample part number from the first search result
        if results:
            sample_part_number = results[0].get("part_number")
            part_details = await catalog.get_part_details(sample_part_number)
            
            if part_details:
                print(f"   🔍 Found part: {sample_part_number}")
                print(f"   📝 Description: {part_details.get('description', 'N/A')}")
                print(f"   💰 Price: ${part_details.get('list_price', 0):.2f}")
                print(f"   📦 Availability: {part_details.get('availability_text', 'N/A')}")
        
        # Test 6: Performance test
        print("\n6. Testing search performance...")
        import time
        
        start_time = time.time()
        await catalog.search_parts("steel fastener", top_k=20)
        search_time = time.time() - start_time
        
        print(f"   ⚡ Search completed in {search_time:.3f} seconds")
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        print(f"📊 Database contains {stats['total_parts']:,} parts ready for use")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_database_sync():
    """Synchronous wrapper for the async test"""
    return asyncio.run(test_database())

if __name__ == "__main__":
    success = test_database_sync()
    sys.exit(0 if success else 1)
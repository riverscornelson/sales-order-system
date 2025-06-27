#!/usr/bin/env python3

import asyncio
import sys

# Add the backend directory to Python path
sys.path.insert(0, '/Users/riverscornelson/PycharmProjects/sales-order-system/backend')

from app.services.parts_catalog import PartsCatalogService
from app.mcp.search_tools import AgenticSearchTools

async def test_individual_search_tools():
    """Test each search tool individually"""
    
    print("🧪 TESTING INDIVIDUAL SEARCH TOOLS")
    print("="*50)
    
    # Initialize
    catalog_service = PartsCatalogService()
    search_tools = AgenticSearchTools(catalog_service)
    
    # Load the catalog
    print("📂 Loading catalog...")
    csv_path = "/Users/riverscornelson/PycharmProjects/sales-order-system/backend/data/parts_catalog_sample.csv"
    success = await catalog_service.load_catalog_from_csv(csv_path)
    print(f"   Catalog loaded: {success}")
    
    # Test each search tool individually
    query = "4140 steel round bar"
    
    print(f"\n🔍 TESTING QUERY: '{query}'")
    print("-" * 30)
    
    # Test 1: Fuzzy Text Search (this one worked in debug)
    print("1️⃣ Testing fuzzy_text_search...")
    try:
        fuzzy_results = await search_tools.fuzzy_text_search(["4140", "steel"], fuzzy_threshold=50)
        print(f"   Results: {len(fuzzy_results)}")
        for i, result in enumerate(fuzzy_results[:3]):
            print(f"     {i+1}. {result.part_number}: {result.description} (score: {result.similarity_score:.3f})")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Test 2: Material Category Search
    print("\n2️⃣ Testing material_category_search...")
    try:
        material_results = await search_tools.material_category_search("4140", form="bar")
        print(f"   Results: {len(material_results)}")
        for i, result in enumerate(material_results[:3]):
            print(f"     {i+1}. {result.part_number}: {result.description} (score: {result.similarity_score:.3f})")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Test 3: Alternative Materials Search
    print("\n3️⃣ Testing alternative_materials_search...")
    try:
        alt_results = await search_tools.alternative_materials_search("4140", application="urgent")
        print(f"   Results: {len(alt_results)}")
        for i, result in enumerate(alt_results[:3]):
            print(f"     {i+1}. {result.part_number}: {result.description} (score: {result.similarity_score:.3f})")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Test 4: Semantic Vector Search (the problematic one)
    print("\n4️⃣ Testing semantic_vector_search...")
    try:
        semantic_results = await search_tools.semantic_vector_search(query, top_k=5)
        print(f"   Results: {len(semantic_results)}")
        for i, result in enumerate(semantic_results[:3]):
            print(f"     {i+1}. {result.part_number}: {result.description} (score: {result.similarity_score:.3f})")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Test 5: Check if parts were actually loaded
    print("\n5️⃣ Checking loaded parts...")
    try:
        all_parts = await search_tools._get_all_catalog_parts()
        print(f"   Total parts available: {len(all_parts)}")
        
        # Look for 4140 specifically
        found_4140 = []
        for part in all_parts:
            if "4140" in str(part.get("description", "")) or "4140" in str(part.get("material", "")):
                found_4140.append(part)
        
        print(f"   Parts containing '4140': {len(found_4140)}")
        for part in found_4140[:2]:
            print(f"     - {part.get('part_number')}: {part.get('description')}")
            
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    print(f"\n🏁 Test completed!")

if __name__ == "__main__":
    asyncio.run(test_individual_search_tools())
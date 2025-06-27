#!/usr/bin/env python3

import asyncio
import sys

# Add the backend directory to Python path
sys.path.insert(0, '/Users/riverscornelson/PycharmProjects/sales-order-system/backend')

from app.services.parts_catalog import PartsCatalogService
from app.mcp.search_tools import AgenticSearchTools

async def test_fixed_semantic_search():
    """Test the fixed semantic search functionality"""
    
    print("🔧 TESTING FIXED SEMANTIC SEARCH")
    print("=" * 50)
    
    # Initialize (without reloading catalog)
    catalog_service = PartsCatalogService()
    search_tools = AgenticSearchTools(catalog_service)
    
    # Test query
    query = "4140 steel round bar"
    
    print(f"🔍 Testing query: '{query}'")
    print()
    
    # Test semantic vector search with the fix
    print("1️⃣ Testing semantic_vector_search...")
    try:
        semantic_results = await search_tools.semantic_vector_search(query, top_k=5)
        print(f"   Results: {len(semantic_results)}")
        
        if semantic_results:
            print("   Top results:")
            for i, result in enumerate(semantic_results[:3]):
                print(f"     {i+1}. {result.part_number}: {result.description} (score: {result.similarity_score:.3f})")
                
                # Check if this is the 4140 part we're looking for
                if "4140" in result.description:
                    print(f"       *** FOUND 4140 PART! ***")
        else:
            print("   ❌ No results found")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Also test catalog service directly
    print("\n2️⃣ Testing catalog service search_parts directly...")
    try:
        catalog_results = await catalog_service.search_parts(
            query=query,
            top_k=5
        )
        print(f"   Results: {len(catalog_results)}")
        
        if catalog_results:
            print("   Top results:")
            for i, result in enumerate(catalog_results[:3]):
                combined_score = result.get("scores", {}).get("combined_score", 0)
                print(f"     {i+1}. {result['part_number']}: {result['description']} (combined: {combined_score:.3f})")
                
                # Check if this is the 4140 part we're looking for
                if "4140" in result["description"]:
                    print(f"       *** FOUND 4140 PART! ***")
        else:
            print("   ❌ No results found")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    print("\n3️⃣ CONCLUSION:")
    if semantic_results and any("4140" in r.description for r in semantic_results):
        print("   ✅ SUCCESS: Semantic search now finds the 4140 part!")
    elif semantic_results:
        print("   ⚠️ PARTIAL SUCCESS: Semantic search returns results but may not include 4140")
    else:
        print("   ❌ FAILURE: Semantic search still returns no results")

if __name__ == "__main__":
    asyncio.run(test_fixed_semantic_search())
#!/usr/bin/env python3

import asyncio
import sys

# Add the backend directory to Python path
sys.path.insert(0, '/Users/riverscornelson/PycharmProjects/sales-order-system/backend')

from app.services.parts_catalog import PartsCatalogService

async def test_all_search_results():
    """Test to see all search results and find where 4140 ranks"""
    
    print("🔍 TESTING ALL SEARCH RESULTS TO FIND 4140")
    print("=" * 60)
    
    # Initialize
    catalog_service = PartsCatalogService()
    
    # Test query
    query = "4140 steel round bar"
    
    print(f"Query: '{query}'")
    print()
    
    # Get ALL results
    print("📊 Getting ALL search results...")
    try:
        catalog_results = await catalog_service.search_parts(
            query=query,
            top_k=100  # Get all results
        )
        print(f"   Total results: {len(catalog_results)}")
        
        if catalog_results:
            print("\n   ALL RESULTS:")
            found_4140_rank = None
            for i, result in enumerate(catalog_results):
                is_4140_part = "4140" in result["description"] or "4140" in result["part_number"]
                marker = " *** 4140 PART! ***" if is_4140_part else ""
                if is_4140_part:
                    found_4140_rank = i + 1
                scores = result.get("scores", {})
                combined = scores.get("combined_score", 0)
                vector = scores.get("vector_similarity", 0)
                text = scores.get("text_similarity", 0)
                spec = scores.get("spec_match", 0)
                print(f"     {i+1:2}. {result['part_number']}: {result['description'][:60]}... "
                      f"(C:{combined:.3f} V:{vector:.3f} T:{text:.3f} S:{spec:.3f}){marker}")
            
            if found_4140_rank:
                print(f"\n   ✅ FOUND: 4140 part ranked #{found_4140_rank}")
                
                # Show the 4140 part details
                result_4140 = next(r for r in catalog_results if "4140" in r["description"] or "4140" in r["part_number"])
                scores = result_4140.get("scores", {})
                print(f"\n   4140 PART DETAILS:")
                print(f"     Part: {result_4140['part_number']}")
                print(f"     Description: {result_4140['description']}")
                print(f"     Combined Score: {scores.get('combined_score', 0):.4f}")
                print(f"     Vector Similarity: {scores.get('vector_similarity', 0):.4f}")
                print(f"     Text Similarity: {scores.get('text_similarity', 0):.4f}")
                print(f"     Spec Match: {scores.get('spec_match', 0):.4f}")
                
                if found_4140_rank <= 10:
                    print(f"   ✅ EXCELLENT: 4140 part is in top 10!")
                elif found_4140_rank <= 20:
                    print(f"   ✅ GOOD: 4140 part is in top 20!")
                else:
                    print(f"   ⚠️ LOW RANKING: 4140 part ranked #{found_4140_rank}")
                    print(f"      This is due to low random vector similarity: {scores.get('vector_similarity', 0):.4f}")
            else:
                print(f"\n   ❌ 4140 part not found in any results!")
        else:
            print("   ❌ No results found")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_all_search_results())
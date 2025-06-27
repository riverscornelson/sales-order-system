#!/usr/bin/env python3

import asyncio
import sys
import structlog

# Add the backend directory to Python path
sys.path.insert(0, '/Users/riverscornelson/PycharmProjects/sales-order-system/backend')

from app.services.parts_catalog import PartsCatalogService
from app.mcp.search_tools import AgenticSearchTools

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

async def debug_catalog():
    """Debug the catalog loading and search functionality"""
    
    print("🔧 CATALOG DEBUG SESSION")
    print("="*50)
    
    # Initialize catalog service
    catalog_service = PartsCatalogService()
    search_tools = AgenticSearchTools(catalog_service)
    
    # Check mock data
    print(f"📦 Mock parts in catalog: {len(catalog_service.mock_parts)}")
    for i, part in enumerate(catalog_service.mock_parts[:3]):
        print(f"  {i+1}. {part['part_number']}: {part['description']}")
    
    # Check for 4140 steel specifically
    print(f"\n🔍 Looking for 4140 steel in mock data...")
    found_4140 = False
    for part in catalog_service.mock_parts:
        if "4140" in part.get("description", "") or "4140" in part.get("material", ""):
            print(f"  ✅ FOUND: {part['part_number']} - {part['description']}")
            found_4140 = True
    
    if not found_4140:
        print("  ❌ No 4140 steel found in mock data")
    
    # Try to load from CSV
    print(f"\n📂 Attempting to load from CSV...")
    try:
        import os
        csv_path = "/Users/riverscornelson/PycharmProjects/sales-order-system/backend/data/parts_catalog_sample.csv"
        if os.path.exists(csv_path):
            print(f"  📄 CSV file exists: {csv_path}")
            success = await catalog_service.load_catalog_from_csv(csv_path)
            print(f"  📊 CSV load success: {success}")
            
            # Check stats after CSV load
            stats = await catalog_service.get_catalog_stats()
            print(f"  📈 Catalog stats after CSV load:")
            print(f"    Total parts: {stats.get('total_parts', 0)}")
            print(f"    Vector store count: {stats.get('vector_store', {}).get('count', 0)}")
            print(f"    Materials: {len(stats.get('materials', []))}")
            
        else:
            print(f"  ❌ CSV file not found: {csv_path}")
    except Exception as e:
        print(f"  ❌ CSV load failed: {e}")
    
    # Test search tools directly
    print(f"\n🔍 Testing search tools directly...")
    
    # Test 1: Debug search pipeline
    print("  🔧 Running debug_search_pipeline...")
    debug_info = await search_tools.debug_search_pipeline("4140 steel round bar")
    print(f"    Catalog status: {debug_info.get('catalog_status', {})}")
    print(f"    Embedding test: {debug_info.get('embedding_test', {})}")
    print(f"    Text matches: {debug_info.get('text_matches', {})}")
    print(f"    Recommendations: {debug_info.get('recommendations', [])}")
    
    # Test 2: Semantic vector search
    print("  🎯 Testing semantic vector search...")
    try:
        semantic_results = await search_tools.semantic_vector_search("4140 steel", top_k=5)
        print(f"    Semantic results: {len(semantic_results)}")
        for result in semantic_results[:2]:
            print(f"      - {result.part_number}: {result.description} (score: {result.similarity_score:.3f})")
    except Exception as e:
        print(f"    ❌ Semantic search failed: {e}")
    
    # Test 3: Fuzzy text search
    print("  🔤 Testing fuzzy text search...")
    try:
        fuzzy_results = await search_tools.fuzzy_text_search(["4140", "steel"], fuzzy_threshold=50)
        print(f"    Fuzzy results: {len(fuzzy_results)}")
        for result in fuzzy_results[:2]:
            print(f"      - {result.part_number}: {result.description} (score: {result.similarity_score:.3f})")
    except Exception as e:
        print(f"    ❌ Fuzzy search failed: {e}")
    
    # Test 4: Material category search
    print("  🔧 Testing material category search...")
    try:
        material_results = await search_tools.material_category_search("4140")
        print(f"    Material results: {len(material_results)}")
        for result in material_results[:2]:
            print(f"      - {result.part_number}: {result.description} (score: {result.similarity_score:.3f})")
    except Exception as e:
        print(f"    ❌ Material search failed: {e}")
    
    # Test 5: Catalog exploration
    print("  🗺️ Testing catalog exploration...")
    try:
        overview = await search_tools.catalog_exploration("overview")
        print(f"    Overview: {overview}")
    except Exception as e:
        print(f"    ❌ Catalog exploration failed: {e}")
    
    print(f"\n🏁 Debug session completed!")

if __name__ == "__main__":
    asyncio.run(debug_catalog())
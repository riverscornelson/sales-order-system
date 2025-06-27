#!/usr/bin/env python3
"""
Test script for large parts catalog performance
"""

import asyncio
import time
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.parts_catalog import PartsCatalogService

async def test_catalog_performance():
    """Test the performance of the parts catalog with large datasets"""
    
    print("🧪 Testing Large Parts Catalog Performance")
    print("=" * 60)
    
    # Initialize service
    service = PartsCatalogService()
    
    # Test with different sized catalogs
    test_files = [
        ("Small (100 parts)", "data/parts_catalog_sample.csv"),
        ("Medium (10K parts)", "data/parts_catalog.csv"), 
        ("Large (50K parts)", "data/parts_catalog_large.csv")
    ]
    
    for name, file_path in test_files:
        full_path = backend_dir / file_path
        if not full_path.exists():
            print(f"⚠️  Skipping {name}: File {file_path} not found")
            continue
            
        print(f"\n📊 Testing {name}")
        print("-" * 40)
        
        # Test loading performance
        print("🔄 Loading catalog...")
        start_time = time.time()
        
        success = await service.load_catalog_from_csv(str(full_path), batch_size=500)
        
        load_time = time.time() - start_time
        
        if success:
            print(f"✅ Loaded successfully in {load_time:.2f} seconds")
        else:
            print(f"❌ Failed to load catalog")
            continue
        
        # Get catalog stats
        stats = await service.get_catalog_stats()
        total_parts = stats.get("total_parts", 0)
        
        if total_parts > 0:
            print(f"📈 Load rate: {total_parts/load_time:.0f} parts/second")
        
        print(f"📦 Total parts in catalog: {total_parts:,}")
        print(f"🏷️  Categories: {len(stats.get('categories', []))}")
        print(f"🧱 Materials: {len(stats.get('materials', []))}")
        print(f"💰 Total inventory value: ${stats.get('total_inventory_value', 0):,.2f}")
        
        # Test search performance
        search_queries = [
            "stainless steel",
            "aluminum 6061", 
            "titanium round",
            "sheet metal",
            "tube rectangular"
        ]
        
        print(f"\n🔍 Testing search performance...")
        total_search_time = 0
        
        for query in search_queries:
            start_time = time.time()
            results = await service.search_parts(query, top_k=10)
            search_time = time.time() - start_time
            total_search_time += search_time
            
            print(f"   '{query}': {len(results)} results in {search_time*1000:.1f}ms")
        
        avg_search_time = total_search_time / len(search_queries)
        print(f"📊 Average search time: {avg_search_time*1000:.1f}ms")
        
        # Sample some results
        print(f"\n📋 Sample search results for 'stainless steel sheet':")
        results = await service.search_parts("stainless steel sheet", top_k=3)
        for i, result in enumerate(results[:3], 1):
            score = result.get("scores", {}).get("combined_score", 0)
            print(f"   {i}. {result['part_number']} (score: {score:.3f})")
            print(f"      {result['description']}")
            print(f"      ${result['unit_price']} | {result['availability']} available")
    
    print(f"\n✅ Performance testing completed!")

if __name__ == "__main__":
    asyncio.run(test_catalog_performance())
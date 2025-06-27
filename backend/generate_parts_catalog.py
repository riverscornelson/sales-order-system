#!/usr/bin/env python3
"""
Generate large-scale parts catalog for testing
Usage: python generate_parts_catalog.py [--size SIZE] [--format FORMAT] [--output OUTPUT]
"""

import argparse
import sys
import os
import time
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.parts_generator import LargePartsGenerator

def main():
    parser = argparse.ArgumentParser(description='Generate large-scale parts catalog for testing')
    parser.add_argument('--size', type=int, default=1000, 
                       help='Number of parts to generate (default: 1000)')
    parser.add_argument('--format', choices=['json', 'csv', 'both'], default='both',
                       help='Output format (default: both)')
    parser.add_argument('--output', type=str, default='parts_catalog',
                       help='Output filename prefix (default: parts_catalog)')
    parser.add_argument('--quick', action='store_true',
                       help='Generate a quick sample (100 parts)')
    
    args = parser.parse_args()
    
    # Quick mode override
    if args.quick:
        args.size = 100
        args.output = 'parts_catalog_sample'
    
    print(f"🏭 Generating {args.size:,} parts catalog...")
    print(f"📁 Output format: {args.format}")
    print(f"📄 Output prefix: {args.output}")
    print()
    
    # Create data directory if it doesn't exist
    data_dir = backend_dir / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Generate the catalog
    generator = LargePartsGenerator()
    
    start_time = time.time()
    parts = generator.generate_parts_catalog(args.size)
    generation_time = time.time() - start_time
    
    print(f"✅ Generated {len(parts):,} parts in {generation_time:.2f} seconds")
    print(f"⚡ Rate: {len(parts)/generation_time:.0f} parts/second")
    print()
    
    # Save to files
    if args.format in ['json', 'both']:
        json_file = data_dir / f"{args.output}.json"
        start_time = time.time()
        generator.save_to_json(parts, str(json_file))
        save_time = time.time() - start_time
        file_size = json_file.stat().st_size / (1024 * 1024)  # MB
        print(f"💾 Saved JSON: {json_file}")
        print(f"   📊 Size: {file_size:.1f} MB")
        print(f"   ⏱️  Time: {save_time:.2f} seconds")
        print()
    
    if args.format in ['csv', 'both']:
        csv_file = data_dir / f"{args.output}.csv"
        start_time = time.time()
        generator.save_to_csv(parts, str(csv_file))
        save_time = time.time() - start_time
        file_size = csv_file.stat().st_size / (1024 * 1024)  # MB
        print(f"💾 Saved CSV: {csv_file}")
        print(f"   📊 Size: {file_size:.1f} MB")
        print(f"   ⏱️  Time: {save_time:.2f} seconds")
        print()
    
    # Show some sample parts
    print("📋 Sample parts generated:")
    print("-" * 100)
    for i, part in enumerate(parts[:5]):
        print(f"{i+1}. {part['part_number']}")
        print(f"   📝 {part['description']}")
        print(f"   💰 ${part['unit_price']} | 📦 {part['availability']} available | ⚖️  {part['weight_per_unit']} lbs")
        print(f"   🏢 {part['supplier']}")
        print()
    
    if len(parts) > 5:
        print(f"... and {len(parts) - 5:,} more parts")
    
    print("🎯 Catalog generation completed successfully!")
    print()
    print("📖 Usage examples:")
    print(f"   • Load in parts catalog service: PartsCatalogService().load_catalog_from_csv('{csv_file}')")
    print(f"   • Search for parts: service.search_parts('stainless steel sheet')")
    print(f"   • Filter by material: service.search_parts('aluminum', filters={{'material': 'Aluminum'}})")

if __name__ == "__main__":
    main()
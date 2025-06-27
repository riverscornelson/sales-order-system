#!/usr/bin/env python3
"""
Simple test runner for the sales order workflow
Consolidates all testing functionality into one script
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment
load_dotenv('.env')

sys.path.insert(0, os.path.dirname(__file__))

from sales_cli import SimpleWorkflowProcessor

async def test_single_file(file_path: str):
    """Test a single file through the workflow"""
    
    print(f"🚀 Testing: {Path(file_path).name}")
    print("=" * 60)
    
    processor = SimpleWorkflowProcessor(output_dir="test_results")
    
    try:
        result = await processor.process_file(file_path)
        
        print("✅ Processing completed!")
        print(f"Session: {result['session_id']}")
        
        if 'summary' in result:
            print(f"\nSummary:")
            print(f"  Total Line Items: {result['summary']['total_line_items']}")
            print(f"  Successful Matches: {result['summary']['successful_matches']}")
            print(f"  Confidence Score: {result['summary']['confidence_score']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

async def test_all_examples():
    """Test all example files"""
    
    print("🚀 Testing All Examples")
    print("=" * 80)
    
    examples_dir = Path("examples")
    if not examples_dir.exists():
        print("❌ Examples directory not found")
        return False
    
    test_files = list(examples_dir.glob("*.txt"))
    if not test_files:
        print("❌ No test files found in examples/")
        return False
    
    processor = SimpleWorkflowProcessor(output_dir="test_results")
    results = []
    
    for i, file_path in enumerate(test_files, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}/{len(test_files)}: {file_path.name}")
        print("="*60)
        
        try:
            result = await processor.process_file(str(file_path))
            
            summary = {
                "file": file_path.name,
                "status": "completed",
                "summary": result.get("summary", {})
            }
            results.append(summary)
            
            print(f"✅ Completed: {file_path.name}")
            
        except Exception as e:
            print(f"❌ Failed: {file_path.name} - {str(e)}")
            results.append({
                "file": file_path.name,
                "status": "failed",
                "error": str(e)
            })
    
    # Print summary
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for r in results if r["status"] == "completed")
    total = len(results)
    
    print(f"Total: {total} | Passed: {passed} ✅ | Failed: {total-passed} ❌")
    
    return passed == total

async def quick_health_check():
    """Quick health check of the system"""
    
    print("🏥 Quick Health Check")
    print("=" * 40)
    
    # Check environment
    api_key = "✅" if os.getenv("OPENAI_API_KEY") else "❌"
    print(f"OpenAI API Key: {api_key}")
    
    # Check database
    try:
        from app.services.local_parts_catalog import LocalPartsCatalogService
        catalog = LocalPartsCatalogService()
        stats = await catalog.get_catalog_stats()
        parts_count = stats.get('total_parts', 0)
        print(f"Parts Database: ✅ ({parts_count} parts)")
    except Exception as e:
        print(f"Parts Database: ❌ ({str(e)[:50]}...)")
    
    # Check core workflow
    try:
        processor = SimpleWorkflowProcessor(output_dir="health_check")
        print("Core Workflow: ✅")
    except Exception as e:
        print(f"Core Workflow: ❌ ({str(e)[:50]}...)")
    
    print("\n✅ Health check completed")

async def main():
    """Main entry point"""
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python test_workflow.py <file>        # Test single file")
        print("  python test_workflow.py --all         # Test all examples")
        print("  python test_workflow.py --health      # Health check")
        return 1
    
    arg = sys.argv[1]
    
    try:
        if arg == "--all":
            success = await test_all_examples()
        elif arg == "--health":
            await quick_health_check()
            success = True
        else:
            # Single file test
            if not Path(arg).exists():
                print(f"❌ File not found: {arg}")
                return 1
            success = await test_single_file(arg)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted")
        return 1
    except Exception as e:
        print(f"💥 Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
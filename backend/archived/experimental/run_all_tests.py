#!/usr/bin/env python3
"""
Run all workflow tests automatically
"""

import asyncio
import sys
import os
from pathlib import Path
import json
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from simple_cli import SimpleWorkflowProcessor

async def run_all_tests():
    """Run workflow tests on all sample orders"""
    
    print("🚀 Running All Workflow Tests")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Running without OpenAI API key - using fallback extraction")
        print()
    
    # Initialize processor
    processor = SimpleWorkflowProcessor(output_dir="test_outputs")
    
    # Test files to process
    test_files = [
        # Sample orders in test_orders directory
        "test_orders/sample_order_1.txt",
        "test_orders/sample_order_2.txt", 
        "test_orders/sample_order_3.txt",
        # The original test file
        "/Users/riverscornelson/PycharmProjects/sales-order-system/test_upload.txt",
        # Minimal test
        "test_minimal.txt"
    ]
    
    results_summary = []
    
    for i, test_file in enumerate(test_files, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}/{len(test_files)}: {Path(test_file).name}")
        print("="*80)
        
        if not Path(test_file).exists():
            print(f"❌ File not found: {test_file}")
            continue
        
        try:
            start_time = datetime.now()
            result = await processor.process_file(test_file)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            summary = {
                "file": Path(test_file).name,
                "status": result.get("status", "unknown"),
                "duration_seconds": round(duration, 2),
                "session_id": result["session_id"],
                "summary": result.get("summary", {})
            }
            results_summary.append(summary)
            
            print(f"\n✅ Test completed in {duration:.2f} seconds")
            print(f"   Session: {result['session_id']}")
            if 'summary' in result:
                print(f"   Line Items: {result['summary']['total_line_items']}")
                print(f"   Matches: {result['summary']['successful_matches']}")
                print(f"   Confidence: {result['summary']['confidence_score']}")
            
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            summary = {
                "file": Path(test_file).name,
                "status": "failed",
                "error": str(e),
                "duration_seconds": 0
            }
            results_summary.append(summary)
    
    # Print final summary
    print(f"\n{'='*80}")
    print("FINAL TEST SUMMARY")
    print("="*80)
    
    total_tests = len(results_summary)
    passed = sum(1 for r in results_summary if r["status"] == "completed")
    failed = sum(1 for r in results_summary if r["status"] == "failed")
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Save summary
    summary_file = Path("test_outputs/test_summary.json")
    summary_file.parent.mkdir(exist_ok=True)
    
    with open(summary_file, "w") as f:
        json.dump({
            "test_run": datetime.now().isoformat(),
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "results": results_summary
        }, f, indent=2)
    
    print(f"\nDetailed summary saved to: {summary_file}")
    print("\nIndividual test outputs are in: test_outputs/*/")
    
    # Show quick results overview
    print("\n📊 Quick Results Overview:")
    print("-" * 80)
    print(f"{'File':<30} {'Status':<12} {'Items':<8} {'Matches':<10} {'Time(s)':<8}")
    print("-" * 80)
    
    for result in results_summary:
        file_name = result['file'][:28] + '..' if len(result['file']) > 30 else result['file']
        status = "✅ Pass" if result['status'] == 'completed' else "❌ Fail"
        items = result.get('summary', {}).get('total_line_items', '-')
        matches = result.get('summary', {}).get('successful_matches', '-')
        duration = result.get('duration_seconds', '-')
        
        print(f"{file_name:<30} {status:<12} {items:<8} {matches:<10} {duration:<8}")
    
    print("-" * 80)
    
    return passed == total_tests

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
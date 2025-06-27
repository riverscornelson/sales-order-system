#!/usr/bin/env python3
"""
Run workflow tests with proper environment loading
"""

import asyncio
import sys
import os
from pathlib import Path
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded environment from: {env_path}")
else:
    print(f"⚠️  No .env file found at: {env_path}")

# Verify API key is loaded
if os.getenv("OPENAI_API_KEY"):
    print("✅ OpenAI API key loaded successfully")
else:
    print("❌ OpenAI API key not found in environment")

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from simple_cli import SimpleWorkflowProcessor

async def run_tests_with_progress():
    """Run tests with progress updates"""
    
    print("\n🚀 Running Workflow Tests with Full AI Capabilities")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize processor
    processor = SimpleWorkflowProcessor(output_dir="test_outputs_ai")
    
    # Test files
    test_files = [
        # Your specific test file
        "/Users/riverscornelson/PycharmProjects/sales-order-system/test_upload.txt",
        # Sample orders
        "test_orders/sample_order_1.txt",
        "test_orders/sample_order_2.txt",
        "test_orders/sample_order_3.txt",
    ]
    
    results_summary = []
    
    for i, test_file in enumerate(test_files, 1):
        if not Path(test_file).exists():
            print(f"\n❌ File not found: {test_file}")
            continue
            
        print(f"\n{'='*80}")
        print(f"📁 Test {i}/{len(test_files)}: {Path(test_file).name}")
        print("="*80)
        
        try:
            start_time = datetime.now()
            
            # Process with progress updates
            print("📝 Stage 1/4: Document Analysis...")
            result = await processor.process_file(test_file)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Summarize results
            if result.get("status") == "completed":
                print(f"\n✅ Test completed successfully in {duration:.1f} seconds")
                print(f"   Customer: {result['steps']['order_extraction']['customer']}")
                print(f"   Line Items: {result['summary']['total_line_items']}")
                print(f"   Matches: {result['summary']['successful_matches']}")
                print(f"   Confidence: {result['summary']['confidence_score']}")
            
            summary = {
                "file": Path(test_file).name,
                "status": result.get("status", "unknown"),
                "duration_seconds": round(duration, 2),
                "session_id": result["session_id"],
                "customer": result.get('steps', {}).get('order_extraction', {}).get('customer', 'Unknown'),
                "summary": result.get("summary", {})
            }
            results_summary.append(summary)
            
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)[:100]}...")
            summary = {
                "file": Path(test_file).name,
                "status": "failed",
                "error": str(e)[:200],
                "duration_seconds": 0
            }
            results_summary.append(summary)
    
    # Final summary
    print(f"\n{'='*80}")
    print("📊 TEST RESULTS SUMMARY")
    print("="*80)
    
    # Summary table
    print(f"\n{'File':<35} {'Customer':<25} {'Items':<8} {'Matches':<10} {'Time(s)':<8}")
    print("-" * 86)
    
    for result in results_summary:
        file_name = result['file']
        customer = result.get('customer', '-')[:23] + '..' if len(result.get('customer', '-')) > 25 else result.get('customer', '-')
        items = result.get('summary', {}).get('total_line_items', '-')
        matches = result.get('summary', {}).get('successful_matches', '-')
        duration = result.get('duration_seconds', '-')
        
        status_icon = "✅" if result['status'] == 'completed' else "❌"
        print(f"{status_icon} {file_name:<33} {customer:<25} {items:<8} {matches:<10} {duration:<8}")
    
    print("-" * 86)
    
    # Overall stats
    total = len(results_summary)
    passed = sum(1 for r in results_summary if r["status"] == "completed")
    failed = total - passed
    
    print(f"\nTotal: {total} | Passed: {passed} ✅ | Failed: {failed} ❌")
    print(f"\nAll outputs saved to: test_outputs_ai/")
    
    # Save summary
    summary_path = Path("test_outputs_ai/test_summary.json")
    summary_path.parent.mkdir(exist_ok=True)
    with open(summary_path, "w") as f:
        json.dump({
            "test_run": datetime.now().isoformat(),
            "environment": "with_ai",
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "results": results_summary
        }, f, indent=2)
    
    print(f"Summary saved to: {summary_path}")
    
    return passed == total

async def main():
    """Main entry point"""
    try:
        success = await run_tests_with_progress()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
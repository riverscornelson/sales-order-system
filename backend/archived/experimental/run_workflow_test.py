#!/usr/bin/env python3
"""
Test runner for the simplified workflow
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from simple_cli import SimpleWorkflowProcessor

async def run_tests():
    """Run workflow tests on sample orders"""
    
    print("🚀 Sales Order Workflow Test Runner")
    print("=" * 80)
    
    # Initialize processor
    processor = SimpleWorkflowProcessor(output_dir="test_outputs")
    
    # Find test order files
    test_dir = Path("test_orders")
    if not test_dir.exists():
        print(f"❌ Test directory not found: {test_dir}")
        return False
    
    test_files = list(test_dir.glob("*.txt"))
    if not test_files:
        print(f"❌ No test files found in: {test_dir}")
        return False
    
    print(f"\nFound {len(test_files)} test files to process")
    
    # Process each test file
    results = []
    for i, test_file in enumerate(test_files, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}/{len(test_files)}: {test_file.name}")
        print("="*80)
        
        try:
            result = await processor.process_file(str(test_file))
            results.append({
                "file": test_file.name,
                "status": result.get("status", "unknown"),
                "summary": result.get("summary", {})
            })
            print(f"✅ Test passed: {test_file.name}")
            
        except Exception as e:
            print(f"❌ Test failed: {test_file.name}")
            print(f"   Error: {str(e)}")
            results.append({
                "file": test_file.name,
                "status": "failed",
                "error": str(e)
            })
    
    # Print summary
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for r in results if r["status"] == "completed")
    failed = sum(1 for r in results if r["status"] == "failed")
    
    print(f"\nTotal Tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    print("\nDetailed Results:")
    for result in results:
        status_icon = "✅" if result["status"] == "completed" else "❌"
        print(f"\n{status_icon} {result['file']}:")
        print(f"   Status: {result['status']}")
        
        if "summary" in result and result["summary"]:
            print(f"   Line Items: {result['summary'].get('total_line_items', 0)}")
            print(f"   Matches: {result['summary'].get('successful_matches', 0)}")
            print(f"   Confidence: {result['summary'].get('confidence_score', 0)}")
        
        if "error" in result:
            print(f"   Error: {result['error']}")
    
    print(f"\n{'='*80}")
    print(f"All test outputs saved to: test_outputs/")
    print("="*80)
    
    return failed == 0

async def main():
    """Main entry point"""
    
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  WARNING: OPENAI_API_KEY not set!")
        print("   The workflow will run with limited functionality.")
        print("   To enable full AI capabilities, set your OpenAI API key:")
        print("   export OPENAI_API_KEY='your-key-here'")
        print()
        
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return 1
    
    try:
        success = await run_tests()
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
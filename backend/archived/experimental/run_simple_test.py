#!/usr/bin/env python3
"""
Simple test runner with real-time progress
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from simple_cli import SimpleWorkflowProcessor

async def main():
    """Run a simple test"""
    
    print("🚀 Simple Sales Order Workflow Test")
    print("=" * 60)
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  WARNING: OPENAI_API_KEY not set!")
        print("   The workflow will run with limited functionality.")
        print()
    
    # Initialize processor
    processor = SimpleWorkflowProcessor(output_dir="simple_test_output")
    
    # Get file path
    file_path = sys.argv[1] if len(sys.argv) > 1 else "/Users/riverscornelson/PycharmProjects/sales-order-system/test_upload.txt"
    
    print(f"Processing: {file_path}")
    print()
    
    try:
        # Process the file
        results = await processor.process_file(file_path)
        
        print("\n" + "=" * 60)
        print("✅ WORKFLOW COMPLETED")
        print("=" * 60)
        
        # Show summary
        if 'summary' in results:
            print(f"\nOrder Summary:")
            print(f"  Total Line Items: {results['summary']['total_line_items']}")
            print(f"  Successful Matches: {results['summary']['successful_matches']}")
            print(f"  Confidence Score: {results['summary']['confidence_score']}")
            print(f"  Approval Required: {results['summary']['approval_required']}")
        
        print(f"\nOutputs saved to: simple_test_output/{results['session_id']}/")
        
        # Show the assembled order
        import json
        output_dir = f"simple_test_output/{results['session_id']}"
        
        # Read and display key results
        if os.path.exists(f"{output_dir}/04_part_matches.json"):
            with open(f"{output_dir}/04_part_matches.json") as f:
                matches = json.load(f)
            
            print("\nPart Matches:")
            for line_id, match in matches.items():
                print(f"  {line_id}: {match['selected_part']} (confidence: {match['confidence']})")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted")
        return 1
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
#!/usr/bin/env python3
"""
Test a single file through the workflow
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import json

# Load environment
load_dotenv('.env')

sys.path.insert(0, os.path.dirname(__file__))

from simple_cli import SimpleWorkflowProcessor

async def test_single_file():
    """Test the specific upload file"""
    
    print("🚀 Testing Single File")
    print("=" * 60)
    
    file_path = "/Users/riverscornelson/PycharmProjects/sales-order-system/test_upload.txt"
    
    processor = SimpleWorkflowProcessor(output_dir="single_test_output")
    
    try:
        print(f"Processing: {file_path}")
        print(f"API Key Available: {'✅' if os.getenv('OPENAI_API_KEY') else '❌'}")
        print()
        
        result = await processor.process_file(file_path)
        
        print("\n✅ Processing completed!")
        print(f"Session: {result['session_id']}")
        
        if 'summary' in result:
            print(f"\nSummary:")
            print(f"  Total Line Items: {result['summary']['total_line_items']}")
            print(f"  Successful Matches: {result['summary']['successful_matches']}")
            print(f"  Confidence Score: {result['summary']['confidence_score']}")
            print(f"  Approval Required: {result['summary']['approval_required']}")
        
        # Show the matches
        output_dir = Path(f"single_test_output/{result['session_id']}")
        matches_file = output_dir / "04_part_matches.json"
        
        if matches_file.exists():
            with open(matches_file) as f:
                matches = json.load(f)
            
            print(f"\nPart Matches Found:")
            for line_id, match in matches.items():
                print(f"  {line_id}: {match['selected_part']} (confidence: {match['confidence']})")
                print(f"         Reasoning: {match['reasoning'][:100]}...")
        
        print(f"\nAll outputs saved to: {output_dir}")
        
        # Show final order
        final_file = output_dir / "05_assembled_order.json"
        if final_file.exists():
            with open(final_file) as f:
                final_order = json.load(f)
            
            print(f"\nFinal Order Assembly:")
            print(f"  Order Summary: {final_order['order_summary']}")
            print(f"  Confidence: {final_order['confidence_score']}")
            print(f"  Issues: {len(final_order['issues_requiring_review'])}")
            
            if final_order['issues_requiring_review']:
                print(f"\nIssues Requiring Review:")
                for issue in final_order['issues_requiring_review'][:3]:
                    print(f"  - {issue.get('description', 'Unknown issue')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_single_file())
    sys.exit(0 if success else 1)
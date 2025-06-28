#!/usr/bin/env python3
"""
Test OpenAI Responses API integration for evaluation system
Tests connection to OpenAI Responses API and basic evaluation functionality using gpt-4.1
"""

import asyncio
import json
import os
import sys
from typing import Dict, Any
import logging

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_openai_api_key():
    """Test if OpenAI API key is available"""
    print("🔑 Testing OpenAI API Key...")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OpenAI API Key: NOT SET")
        print("   Please set OPENAI_API_KEY environment variable")
        print("   Example: export OPENAI_API_KEY='your-api-key-here'")
        return False
    
    print(f"✅ OpenAI API Key: FOUND (length: {len(api_key)})")
    return True

async def test_responses_api_connection():
    """Test basic OpenAI Responses API connection"""
    print("\n🔗 Testing OpenAI Responses API Connection...")
    
    try:
        from openai import OpenAI
        
        client = OpenAI()
        
        # Test basic Responses API call with gpt-4.1
        response = client.responses.create(
            model="gpt-4.1",
            input=[
                {"role": "user", "content": "Test connection - respond with exactly 'RESPONSES_API_SUCCESS'"}
            ]
        )
        
        result = response.output_text.strip()
        if "RESPONSES_API_SUCCESS" in result:
            print("✅ OpenAI Responses API Connection: SUCCESS")
            print(f"   Model: gpt-4.1")
            print(f"   Response ID: {response.id}")
            print(f"   Response: {result}")
            return True
        else:
            print(f"❌ OpenAI Responses API Connection: Unexpected response '{result}'")
            return False
            
    except Exception as e:
        print(f"❌ OpenAI Responses API Connection: ERROR - {str(e)}")
        return False

async def test_structured_outputs():
    """Test structured outputs with Responses API"""
    print("\n📋 Testing Structured Outputs with Responses API...")
    
    try:
        from app.core.responses_client import ResponsesAPIClient
        
        client = ResponsesAPIClient()
        
        # Test structured output generation
        prompt = """
        Generate a test ERP order with the following details:
        - Customer: Test Company Inc.
        - One line item for 10 units of stainless steel sheet
        - Material should be specified correctly
        """
        
        result = await client.get_flat_structured_response(
            input_messages=prompt,
            flat_model_name="FlatERPOrder",
            system_message="You are an ERP data specialist. Generate valid ERP order data."
        )
        
        if result.success:
            print("✅ Structured Outputs: SUCCESS")
            print(f"   Model: gpt-4.1")
            print(f"   Response ID: {result.metadata.get('response_id', 'N/A')}")
            print(f"   Customer: {result.data.customer_company_name}")
            print(f"   Line Items: {result.data.total_line_items}")
            print(f"   First Item Material: {result.data.item1_material}")
            return True
        else:
            print(f"❌ Structured Outputs: FAILED")
            print(f"   Error: {result.error}")
            return False
            
    except Exception as e:
        print(f"❌ Structured Outputs: ERROR - {str(e)}")
        return False

async def test_sales_order_extraction():
    """Test sales order extraction with new Responses API client"""
    print("\n📄 Testing Sales Order Extraction...")
    
    try:
        from app.core.responses_client import create_sales_order_client
        
        analyzer = create_sales_order_client()
        
        # Test customer email
        test_email = """
        From: john@testcompany.com
        Subject: Urgent Steel Order Request
        
        Hi,
        
        We need the following materials ASAP for our construction project:
        - 50 sheets of stainless steel 304, 12"x8"x0.25"
        - 25 aluminum plates, 6061 grade
        
        Please confirm availability and pricing.
        
        Best regards,
        John Smith
        Test Company Inc.
        """
        
        # Use flat model for analysis
        result = await analyzer.client.get_flat_structured_response(
            input_messages=test_email,
            flat_model_name="FlatOrderAnalysis",
            system_message="Analyze this sales order for customer context, urgency, and complexity."
        )
        
        if result.success:
            print("✅ Sales Order Extraction: SUCCESS")
            print(f"   Customer Industry: {result.data.industry_sector}")
            print(f"   Urgency Level: {result.data.urgency_level}")
            print(f"   Complexity: {result.data.complexity_level}")
            return True
        else:
            print(f"❌ Sales Order Extraction: FAILED")
            print(f"   Error: {result.error}")
            return False
            
    except Exception as e:
        print(f"❌ Sales Order Extraction: ERROR - {str(e)}")
        return False

async def test_erp_json_generation():
    """Test ERP JSON generation with consistent field names"""
    print("\n🏭 Testing ERP JSON Generation...")
    
    try:
        from app.core.responses_client import create_sales_order_client
        
        generator = create_sales_order_client()
        
        # Test ERP JSON generation
        test_email = """
        Customer: Manufacturing Corp
        Contact: Sarah Johnson (sarah@mfgcorp.com)
        
        Order Request:
        - 100 units of carbon steel rod, 1/2" diameter, 12" length
        - 50 sheets of aluminum 6061, 24"x24"x0.125"
        
        Delivery: ASAP to warehouse facility
        """
        
        # Use flat model for ERP generation
        result = await generator.client.get_flat_structured_response(
            input_messages=test_email,
            flat_model_name="FlatERPOrder",
            system_message="Generate a complete ERP order. Use 'None' for unused item slots. Ensure material field is always specified."
        )
        
        if result.success:
            print("✅ ERP JSON Generation: SUCCESS")
            print(f"   Customer: {result.data.customer_company_name}")
            print(f"   Line Items: {result.data.total_line_items}")
            
            # Check for material field consistency (key evaluation metric)
            material_fields_correct = True
            if not result.data.item1_material or result.data.item1_material == "None":
                material_fields_correct = False
            
            if material_fields_correct:
                print("✅ Material Field Consistency: PASSED")
            else:
                print("❌ Material Field Consistency: FAILED")
                
            return True
        else:
            print(f"❌ ERP JSON Generation: FAILED")
            print(f"   Error: {result.error}")
            return False
            
    except Exception as e:
        print(f"❌ ERP JSON Generation: ERROR - {str(e)}")
        return False

async def test_order_extraction_agent():
    """Test the new order extraction agent with Responses API"""
    print("\n🤖 Testing Order Extraction Agent...")
    
    try:
        from app.agents.enhanced_order_extractor import EnhancedOrderExtractor
        
        agent = EnhancedOrderExtractor()
        
        # Test document
        test_document = """
        PURCHASE ORDER
        
        From: Tech Solutions LLC
        Contact: Mike Davis (mike@techsolutions.com)
        Phone: (555) 123-4567
        
        Items Requested:
        1. Steel plate - 304 stainless steel, 1/4" thick, 48"x24" - Qty: 10
        2. Aluminum bar - 6061-T6, 2" diameter, 12" length - Qty: 25
        3. Carbon steel sheet - hot rolled, 16 gauge, 36"x36" - Qty: 15
        
        Delivery Date: Next Friday
        Payment Terms: Net 30
        """
        
        result = await agent.extract_order_data(test_document)
        
        if result and result.get("line_items"):
            print("✅ Order Extraction Agent: SUCCESS")
            print(f"   Customer: {result.get('customer_info', {}).get('company', 'N/A')}")
            print(f"   Email: {result.get('customer_info', {}).get('email', 'N/A')}")
            print(f"   Line Items: {len(result.get('line_items', []))}")
            print(f"   Overall Confidence: {result.get('confidence', {}).get('overall', 0):.2f}")
            print(f"   API Used: {result.get('confidence', {}).get('api', 'N/A')}")
            return True
        else:
            print("❌ Order Extraction Agent: FAILED - No data extracted")
            return False
            
    except Exception as e:
        print(f"❌ Order Extraction Agent: ERROR - {str(e)}")
        return False

async def run_all_tests():
    """Run all integration tests"""
    print("🚀 Starting OpenAI Responses API Integration Tests")
    print("=" * 60)
    
    tests = [
        ("API Key Check", test_openai_api_key),
        ("Responses API Connection", test_responses_api_connection),
        ("Structured Outputs", test_structured_outputs),
        ("Sales Order Extraction", test_sales_order_extraction),
        ("ERP JSON Generation", test_erp_json_generation),
        ("Order Extraction Agent", test_order_extraction_agent),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}: CRITICAL ERROR - {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal Tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/len(results)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! OpenAI Responses API integration is working correctly.")
        print("   • gpt-4.1 model is functioning properly")
        print("   • Structured outputs are generating consistent JSON")
        print("   • Sales order processing pipeline is operational")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the errors above.")
        
    return failed == 0

if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(run_all_tests())
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
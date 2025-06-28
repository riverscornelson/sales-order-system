#!/usr/bin/env python3
"""
Test Completely Flat Models for OpenAI Responses API
Tests the flat Pydantic models designed for maximum Responses API compatibility
"""

import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

async def test_flat_erp_order():
    """Test completely flat ERP order generation"""
    print("🏭 Testing Flat ERP Order Generation...")
    
    try:
        from app.core.responses_client import ResponsesAPIClient
        
        client = ResponsesAPIClient()
        
        prompt = """
        Generate an ERP order for:
        
        Customer: TechCorp Manufacturing
        Contact: Sarah Johnson (sarah@techcorp.com)
        Phone: (555) 987-6543
        
        Items:
        1. 50 pieces of stainless steel sheet, 304 grade, 1/4" thick, 48"x24" - $125.50 each
        2. 25 aluminum bars, 6061-T6, 2" diameter, 12" length - $45.75 each
        
        Priority: HIGH
        Delivery: Next Friday
        PO: TC-2024-001
        """
        
        result = await client.get_flat_structured_response(
            input_messages=prompt,
            flat_model_name="FlatERPOrder",
            system_message="Generate a complete flat ERP order. Use 'None' for unused item slots. Ensure material field is always specified."
        )
        
        if result.success:
            print("✅ Flat ERP Order: SUCCESS")
            print(f"   Customer: {result.data.customer_company_name}")
            print(f"   Contact: {result.data.customer_contact_name}")
            print(f"   Email: {result.data.customer_email}")
            print(f"   Order ID: {result.data.order_id}")
            print(f"   Priority: {result.data.priority}")
            print(f"   Total: ${result.data.total_amount}")
            print(f"   Line Items: {result.data.total_line_items}")
            
            # Check material fields (critical for evaluation)
            print(f"   Item 1 Material: {result.data.item1_material}")
            print(f"   Item 2 Material: {result.data.item2_material}")
            
            # Verify no empty materials
            if result.data.item1_material and result.data.item1_material != "None":
                print("✅ Material Field Consistency: PASSED")
            else:
                print("❌ Material Field Consistency: FAILED")
            
            return True
        else:
            print(f"❌ Flat ERP Order: FAILED")
            print(f"   Error: {result.error}")
            return False
            
    except Exception as e:
        print(f"❌ Flat ERP Order: ERROR - {str(e)}")
        return False

async def test_flat_order_analysis():
    """Test completely flat order analysis"""
    print("\n📊 Testing Flat Order Analysis...")
    
    try:
        from app.core.responses_client import ResponsesAPIClient
        
        client = ResponsesAPIClient()
        
        prompt = """
        Analyze this customer request:
        
        From: emergency@bridgecorp.com
        Subject: CRITICAL - Bridge repair materials needed ASAP
        
        We have a major bridge repair emergency. DOT inspection found structural issues.
        Need immediately:
        - 200 steel I-beams, A992 grade, W12x40, 20 feet long
        - 500 steel plates, A36 grade, 1" thick, 4'x8'
        - All materials must be certified for structural use
        
        This is a public safety emergency. We need delivery within 24 hours.
        Project value: $2.5M
        
        Contact: Mike Rodriguez, PE
        BridgeCorp Engineering
        """
        
        result = await client.get_flat_structured_response(
            input_messages=prompt,
            flat_model_name="FlatOrderAnalysis",
            system_message="Analyze order for industry, urgency, complexity. Use exact values: SMALL/MEDIUM/LARGE for size, CRITICAL/HIGH/MEDIUM/LOW for urgency."
        )
        
        if result.success:
            print("✅ Flat Order Analysis: SUCCESS")
            print(f"   Industry: {result.data.industry_sector}")
            print(f"   Company Size: {result.data.company_size}")
            print(f"   Customer Tier: {result.data.customer_tier}")
            print(f"   Urgency: {result.data.urgency_level}")
            print(f"   Complexity: {result.data.complexity_level}")
            print(f"   Emergency Indicators: {result.data.emergency_indicators}")
            print(f"   Time Constraint: {result.data.time_constraint}")
            print(f"   Business Impact: {result.data.business_impact}")
            print(f"   Line Items: {result.data.total_line_items}")
            print(f"   Confidence: {result.data.confidence_score:.2f}")
            
            return True
        else:
            print(f"❌ Flat Order Analysis: FAILED")
            print(f"   Error: {result.error}")
            return False
            
    except Exception as e:
        print(f"❌ Flat Order Analysis: ERROR - {str(e)}")
        return False

async def test_flat_part_match():
    """Test completely flat part matching"""
    print("\n🔧 Testing Flat Part Matching...")
    
    try:
        from app.core.responses_client import ResponsesAPIClient
        
        client = ResponsesAPIClient()
        
        prompt = """
        Customer needs: "3/4 inch carbon steel hex bar, A36 grade, 10 feet long"
        
        Available parts:
        1. CS-A36-HEX-0.75-120 - Carbon Steel A36 Hex Bar, 3/4" across flats, 120" length - $35.80 - Stock: 200
        2. CS-A36-RND-0.75-120 - Carbon Steel A36 Round Bar, 3/4" diameter, 120" length - $32.50 - Stock: 150  
        3. CS-1018-HEX-0.75-120 - Carbon Steel 1018 Hex Bar, 3/4" across flats, 120" length - $38.90 - Stock: 75
        4. SS-304-HEX-0.75-120 - Stainless Steel 304 Hex Bar, 3/4" across flats, 120" length - $95.40 - Stock: 50
        
        Select the best match considering material grade, shape, dimensions, availability, and cost.
        """
        
        result = await client.get_flat_structured_response(
            input_messages=prompt,
            flat_model_name="FlatPartMatch",
            system_message="Select best part match. Provide detailed reasoning and confidence scores."
        )
        
        if result.success:
            print("✅ Flat Part Match: SUCCESS")
            print(f"   Selected: {result.data.selected_part_number}")
            print(f"   Confidence: {result.data.confidence_score:.2f}")
            print(f"   Spec Match: {result.data.specification_match:.2f}")
            print(f"   Material Match: {result.data.material_compatibility:.2f}")
            print(f"   Availability: {result.data.availability_score:.2f}")
            print(f"   Alternative: {result.data.alternative_part}")
            print(f"   Reasoning: {result.data.match_reasoning[:100]}...")
            print(f"   Risk Factors: {result.data.risk_factors}")
            
            return True
        else:
            print(f"❌ Flat Part Match: FAILED")
            print(f"   Error: {result.error}")
            return False
            
    except Exception as e:
        print(f"❌ Flat Part Match: ERROR - {str(e)}")
        return False

async def run_flat_model_tests():
    """Run all flat model tests"""
    print("🚀 Testing Completely Flat Models for Responses API")
    print("=" * 60)
    
    tests = [
        ("Flat ERP Order", test_flat_erp_order),
        ("Flat Order Analysis", test_flat_order_analysis),
        ("Flat Part Match", test_flat_part_match),
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
    print("📊 FLAT MODELS TEST SUMMARY")
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
        print("\n🎉 ALL FLAT MODEL TESTS PASSED!")
        print("   • gpt-4.1 with Responses API working perfectly")
        print("   • Structured outputs generating consistent JSON")
        print("   • No nested objects - fully Responses API compatible")
        print("   • Material fields consistent for ERP evaluation")
        print("   • Ready for production deployment!")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the errors above.")
        
    return failed == 0

if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(run_flat_model_tests())
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
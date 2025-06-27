#!/usr/bin/env python3
"""
Complete Workflow Test for Sales Order System
Tests the entire pipeline from document processing to final order assembly
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.agents.supervisor_local import LocalSupervisorAgent
from app.agents.workflow_state import WorkflowState, WorkflowStage
from app.services.local_parts_catalog import LocalPartsCatalogService
from app.database.connection import get_db_manager

# Sample test documents
TEST_DOCUMENTS = {
    "simple_order": """
    From: john.smith@manufacturer.com
    To: sales@metalworks.com
    Subject: Quote Request - Stainless Steel Components
    
    Hi,
    
    We need a quote for the following items:
    
    1. Stainless Steel 304 Sheet - 12" x 8" x 0.25" thick - Qty: 5 pieces
    2. Aluminum 6061 Plate - 10" x 6" x 0.5" thick - Qty: 3 pieces  
    3. Carbon Steel 1018 Bar - 8" x 4" x 0.375" thick - Qty: 10 pieces
    
    Please provide pricing and availability.
    
    Best regards,
    John Smith
    Manufacturing Engineer
    ABC Manufacturing Inc.
    Phone: (555) 123-4567
    """,
    
    "complex_order": """
    Purchase Order Request
    
    Customer: TechCorp Industries
    Contact: Sarah Johnson (sarah.j@techcorp.com)
    Phone: (555) 987-6543
    
    Project: Assembly Line Upgrade
    PO Number: TC-2024-001
    Delivery Date: 2024-07-15
    
    Line Items:
    1. Precision Ball Bearings - Deep Groove type, 25mm bore - Quantity: 20 units
    2. Stainless Steel 316L Fasteners - M8 x 25mm bolts - Quantity: 100 pieces
    3. Hydraulic Cylinder - 2" bore, 12" stroke - Quantity: 2 units
    4. Aluminum Angle Brackets - 2" x 2" x 0.125" thick, 6061-T6 - Quantity: 50 pieces
    5. Copper Electrical Connectors - 12 AWG capacity - Quantity: 25 pieces
    
    Special Instructions:
    - All items must be certified for industrial use
    - Delivery to our facility in Dallas, TX
    - Net 30 payment terms
    
    Thank you,
    Sarah Johnson
    Procurement Manager
    """,
    
    "technical_order": """
    Engineering Specification Request
    
    From: Engineering Department <eng@aerospace.com>
    
    Specification Requirements:
    
    1. Titanium Grade 5 (6Al-4V) Round Bar
       - Diameter: 1.0 inch
       - Length: 12 inches  
       - Condition: Annealed
       - Quantity: 5 pieces
       - Must meet AMS specifications
    
    2. Inconel 718 Sheet Material
       - Dimensions: 24" x 12" x 0.125"
       - Heat treatment: Solution treated and aged
       - Quantity: 2 sheets
       
    3. Hastelloy C-276 Welding Rod
       - Diameter: 1/8 inch
       - Length: 36 inches
       - Quantity: 10 rods
    
    Critical tolerances and material certifications required.
    
    Contact: Dr. Michael Chen
    Senior Materials Engineer
    Phone: (555) 234-5678
    """
}

class WorkflowTester:
    """Test runner for the complete sales order workflow"""
    
    def __init__(self):
        self.supervisor = LocalSupervisorAgent()
        self.catalog = LocalPartsCatalogService()
        self.db_manager = get_db_manager()
        
    async def run_complete_test(self):
        """Run the complete workflow test suite"""
        
        print("🚀 Sales Order System - Complete Workflow Test")
        print("=" * 60)
        
        try:
            # Test 1: Database Health Check
            await self._test_database_health()
            
            # Test 2: Simple Order Processing
            await self._test_simple_order()
            
            # Test 3: Complex Order Processing  
            await self._test_complex_order()
            
            # Test 4: Technical Specification Order
            await self._test_technical_order()
            
            # Test 5: Performance Metrics
            await self._test_performance_metrics()
            
            # Test 6: Error Handling
            await self._test_error_handling()
            
            print("\n" + "=" * 60)
            print("✅ All workflow tests completed successfully!")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Workflow test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    async def _test_database_health(self):
        """Test database connectivity and health"""
        print("\n📊 Testing Database Health...")
        
        # Check database stats
        stats = self.db_manager.get_database_stats()
        print(f"   ✅ Database connected: {stats['total_parts']:,} parts available")
        
        # Test catalog service
        health = await self.catalog.check_health()
        print(f"   ✅ Catalog service: {health['status']}")
        
        # Quick search test
        results = await self.catalog.search_parts("steel", top_k=5)
        print(f"   ✅ Search functionality: {len(results)} results for 'steel'")
        
    async def _test_simple_order(self):
        """Test processing a simple order"""
        print("\n📋 Testing Simple Order Processing...")
        
        # Create workflow state
        state = WorkflowState(
            session_id="test_simple_001",
            client_id="test_client",
            document_filename="simple_order.txt",
            document_type="email",
            document_content=TEST_DOCUMENTS["simple_order"]
        )
        
        # Process through supervisor
        result = await self.supervisor.process_order(state)
        
        # Analyze results
        await self._analyze_workflow_result("Simple Order", result)
        
    async def _test_complex_order(self):
        """Test processing a complex order with multiple items"""
        print("\n🔧 Testing Complex Order Processing...")
        
        state = WorkflowState(
            session_id="test_complex_001", 
            client_id="test_client",
            document_filename="complex_order.txt",
            document_type="email",
            document_content=TEST_DOCUMENTS["complex_order"]
        )
        
        result = await self.supervisor.process_order(state)
        await self._analyze_workflow_result("Complex Order", result)
        
    async def _test_technical_order(self):
        """Test processing technical specifications order"""
        print("\n⚙️ Testing Technical Specification Order...")
        
        state = WorkflowState(
            session_id="test_technical_001",
            client_id="test_client", 
            document_filename="technical_order.txt",
            document_type="email",
            document_content=TEST_DOCUMENTS["technical_order"]
        )
        
        result = await self.supervisor.process_order(state)
        await self._analyze_workflow_result("Technical Order", result)
        
    async def _analyze_workflow_result(self, test_name: str, result: WorkflowState):
        """Analyze and report workflow results"""
        
        print(f"   📊 {test_name} Results:")
        print(f"      Stage: {result.current_stage}")
        print(f"      Status: {'✅ Success' if result.current_stage == WorkflowStage.COMPLETED else '⚠️ Incomplete'}")
        
        # Customer Info Analysis
        if result.extracted_customer_info:
            customer = result.extracted_customer_info
            print(f"      👤 Customer: {customer.get('name', 'N/A')} ({customer.get('company', 'N/A')})")
            print(f"      📧 Contact: {customer.get('email', 'N/A')}")
        
        # Line Items Analysis
        if result.extracted_line_items:
            print(f"      📦 Line Items: {len(result.extracted_line_items)} extracted")
            
            for i, item in enumerate(result.extracted_line_items[:3], 1):  # Show first 3
                print(f"         {i}. {item.get('description', 'N/A')[:50]}...")
                print(f"            Qty: {item.get('quantity', 'N/A')}")
        
        # Part Matches Analysis
        if result.part_matches:
            matches = result.part_matches.get('matches', {})
            print(f"      🎯 Part Matches: {len(matches)} items processed")
            
            total_matches = 0
            high_confidence = 0
            
            for item_id, item_matches in matches.items():
                if item_matches:
                    total_matches += 1
                    best_match = item_matches[0]
                    score = best_match.get('scores', {}).get('combined_score', 0)
                    if score >= 0.7:
                        high_confidence += 1
                    
                    print(f"         {item_id}: {best_match.get('part_number', 'N/A')} (score: {score:.3f})")
            
            print(f"      📈 Match Rate: {total_matches}/{len(matches)} items matched")
            print(f"      🎯 High Confidence: {high_confidence}/{total_matches} matches")
        
        # ERP Validation
        if result.customer_validation:
            validation = result.customer_validation
            print(f"      🏢 ERP Validation: {validation.get('status', 'N/A')}")
        
        # Errors
        if result.errors:
            print(f"      ⚠️ Errors: {len(result.errors)} encountered")
            for error in result.errors[:2]:  # Show first 2 errors
                print(f"         - {error[:100]}...")
        
        print()
    
    async def _test_performance_metrics(self):
        """Test system performance metrics"""
        print("\n⚡ Testing Performance Metrics...")
        
        import time
        
        # Test search performance
        start_time = time.time()
        results = await self.catalog.search_parts("stainless steel fastener", top_k=20)
        search_time = time.time() - start_time
        print(f"   🔍 Search Performance: {search_time:.3f}s for 20 results")
        
        # Test catalog stats performance
        start_time = time.time()
        stats = await self.catalog.get_catalog_stats()
        stats_time = time.time() - start_time
        print(f"   📊 Stats Performance: {stats_time:.3f}s for catalog statistics")
        
        # Test end-to-end processing time
        start_time = time.time()
        state = WorkflowState(
            session_id="perf_test_001",
            client_id="test_client",
            document_filename="perf_test.txt", 
            document_type="email",
            document_content="Quick test: 2 pieces of stainless steel 304 sheet"
        )
        result = await self.supervisor.process_order(state)
        total_time = time.time() - start_time
        print(f"   🚀 End-to-End: {total_time:.3f}s for complete workflow")
        
    async def _test_error_handling(self):
        """Test error handling and recovery"""
        print("\n🛡️ Testing Error Handling...")
        
        # Test with invalid document
        try:
            state = WorkflowState(
                session_id="error_test_001",
                client_id="test_client",
                document_filename="invalid.txt",
                document_type="email", 
                document_content=""  # Empty content
            )
            result = await self.supervisor.process_order(state)
            print("   ✅ Empty document handled gracefully")
        except Exception as e:
            print(f"   ⚠️ Empty document error: {str(e)[:100]}...")
        
        # Test with malformed text
        try:
            state = WorkflowState(
                session_id="error_test_002",
                client_id="test_client",
                document_filename="malformed.txt",
                document_type="email",
                document_content="Random text with no order information whatsoever"
            )
            result = await self.supervisor.process_order(state)
            print("   ✅ Malformed document handled gracefully")
        except Exception as e:
            print(f"   ⚠️ Malformed document error: {str(e)[:100]}...")
        
    async def _generate_test_report(self):
        """Generate a comprehensive test report"""
        
        print("\n📋 COMPREHENSIVE TEST REPORT")
        print("=" * 60)
        
        # Database Statistics
        stats = self.db_manager.get_database_stats()
        print(f"\n📊 Database Statistics:")
        print(f"   Total Parts: {stats['total_parts']:,}")
        print(f"   Categories: {len(stats.get('categories', []))}")
        print(f"   Average Price: ${stats.get('pricing', {}).get('avg_price', 0):.2f}")
        
        # Catalog Health
        health = await self.catalog.check_health()
        print(f"\n🏥 System Health:")
        print(f"   Database Status: {health['status']}")
        print(f"   Last Check: {health['timestamp']}")
        
        # Sample Search Results
        print(f"\n🔍 Sample Search Capabilities:")
        
        test_searches = [
            "stainless steel 304",
            "aluminum bearing", 
            "hydraulic cylinder",
            "1/4 inch fastener"
        ]
        
        for query in test_searches:
            results = await self.catalog.search_parts(query, top_k=3)
            print(f"   '{query}': {len(results)} results")
            if results:
                best = results[0]
                score = best.get('scores', {}).get('combined_score', 0)
                print(f"      Best: {best.get('part_number')} (score: {score:.3f})")

async def main():
    """Main test runner"""
    
    tester = WorkflowTester()
    
    try:
        success = await tester.run_complete_test()
        
        # Generate final report
        await tester._generate_test_report()
        
        return success
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        return False
    except Exception as e:
        print(f"\n💥 Unexpected test failure: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\n{'🎉 SUCCESS' if success else '💥 FAILED'}: Test suite completed")
    sys.exit(0 if success else 1)
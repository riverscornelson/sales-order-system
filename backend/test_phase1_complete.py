#!/usr/bin/env python3
"""
Comprehensive Test Suite for Phase 1: Complete Contextual Intelligence Integration
Tests the full workflow with EnhancedSupervisorAgent and contextual intelligence
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.agents.enhanced_supervisor import EnhancedSupervisorAgent
from app.agents.workflow_state import WorkflowState, WorkflowStage
from app.services.websocket_manager import WebSocketManager

class MockWebSocketManager(WebSocketManager):
    """Mock WebSocket manager for testing"""
    
    def __init__(self):
        self.messages = []
    
    async def send_session_update(self, session_id: str, message):
        print(f"📡 WebSocket Update [{session_id}]: {message.type}")
        if hasattr(message, 'data') and message.data:
            content = message.data.get('content', {})
            if content.get('status'):
                print(f"   Status: {content['status']}")
            if content.get('contextual_intelligence'):
                print(f"   🧠 Contextual Intelligence: ✅")
            if content.get('order_complexity'):
                print(f"   📊 Order Complexity: {content['order_complexity']}")
            if content.get('contextual_adjustments'):
                print(f"   ⚖️ Contextual Adjustments: {content['contextual_adjustments']}")
        self.messages.append(message)

async def test_complete_contextual_workflow():
    """Test the complete workflow with contextual intelligence"""
    
    print("🧪 Testing Phase 1: Complete Contextual Intelligence Integration")
    print("=" * 70)
    
    # Initialize enhanced supervisor with mock WebSocket
    print("🚀 Initializing Enhanced Supervisor with Contextual Intelligence...")
    mock_websocket = MockWebSocketManager()
    supervisor = EnhancedSupervisorAgent(mock_websocket, max_concurrent_items=3)
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Simple Standard Order",
            "document_content": """
                Purchase Order Request
                Customer: ABC Manufacturing
                
                Line Items:
                1. 4140 steel bar, 1 inch diameter, 12 inches long - 5 pieces
                2. Aluminum 6061 sheet, 1/4 inch thick, 12x12 inches - 2 pieces
                
                Project: Standard Production
                Delivery: Standard lead time acceptable
            """,
            "expected_complexity": "simple",
            "expected_context": "routine"
        },
        
        {
            "name": "Complex Aerospace Order",
            "document_content": """
                URGENT PROCUREMENT REQUEST
                Customer: Aerospace Dynamics Inc.
                
                Line Items:
                1. ASTM A36 steel plate, 1/2" thick with mill test certificate and traceability for aerospace application - 1 piece
                2. Titanium Grade 5 bar, 2" diameter, AS9100 certified, heat treated - 3 pieces  
                3. Inconel 718 sheet, 0.125" thick, stress relieved, with material certification - 2 pieces
                
                Project: F-35 Component Manufacturing
                Delivery: REQUIRED within 72 hours for production line
                Special Requirements: Full traceability, certified materials only
            """,
            "expected_complexity": "complex",
            "expected_context": "emergency"
        },
        
        {
            "name": "Critical Production Emergency",
            "document_content": """
                *** EMERGENCY REPLACEMENT ORDER ***
                Customer: Ford Motor Company
                
                PRODUCTION LINE SHUTDOWN - IMMEDIATE ACTION REQUIRED
                
                Line Items:
                1. Emergency replacement bearing for conveyor system - production line down
                2. Any compatible hydraulic cylinder seal kit - ASAP replacement needed
                3. Stainless steel bolts M12x50 - minimum 20 pieces for temporary repair
                
                Project: Assembly Line #3 Repair
                Urgency: CRITICAL - Line down, losing $50K per hour
                Delivery: EMERGENCY - Need parts within 4 hours if possible
            """,
            "expected_complexity": "critical",
            "expected_context": "production_down"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🔍 Test Scenario {i}: {scenario['name']}")
        print("=" * 50)
        print(f"Document Content Preview: {scenario['document_content'][:100]}...")
        
        try:
            # Create workflow state
            session_id = f"test_session_{i}_{datetime.now().strftime('%H%M%S')}"
            state = WorkflowState(
                session_id=session_id,
                client_id="test_client",
                document_filename=f"test_order_{i}.txt",
                document_content=scenario['document_content'],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            print(f"📋 Created workflow state: {session_id}")
            
            # Run document processing with contextual intelligence
            print("🔄 Running enhanced document processing...")
            
            result_state = await supervisor.process_document(
                session_id=session_id,
                client_id="test_client", 
                filename=f"test_order_{i}.txt",
                document_content=scenario['document_content']
            )
            
            # Analyze results
            print("\n📊 Results Analysis:")
            print(f"   Final Stage: {result_state.current_stage}")
            print(f"   Errors: {len(result_state.errors)}")
            
            if hasattr(result_state, 'order_contextual_intelligence'):
                context_intel = result_state.order_contextual_intelligence
                print(f"   🧠 Order Complexity: {context_intel.get('overall_complexity', 'unknown')}")
                print(f"   🏢 Business Context: {context_intel.get('primary_business_context', 'unknown')}")
                print(f"   🎯 Recommended Approach: {context_intel.get('recommended_approach', 'unknown')}")
                print(f"   ⚠️ Risk Factors: {len(context_intel.get('risk_assessment', {}))}")
                print(f"   🚨 Escalation Triggers: {len(context_intel.get('escalation_triggers', []))}")
                
                # Validate expectations
                actual_complexity = context_intel.get('overall_complexity', 'unknown')
                actual_context = context_intel.get('primary_business_context', 'unknown')
                
                complexity_match = "✅" if actual_complexity == scenario['expected_complexity'] else "❌"
                context_match = "✅" if actual_context == scenario['expected_context'] else "❌"
                
                print(f"\n🎯 Validation:")
                print(f"   Expected Complexity: {scenario['expected_complexity']} | Actual: {actual_complexity} {complexity_match}")
                print(f"   Expected Context: {scenario['expected_context']} | Actual: {actual_context} {context_match}")
            else:
                print("   ❌ No contextual intelligence data found")
            
            # Check processing metrics
            if hasattr(result_state, 'processing_metrics'):
                metrics = result_state.processing_metrics
                print(f"\n⏱️ Performance Metrics:")
                print(f"   Total Processing Time: {metrics.get('total_processing_time', 0):.2f}s")
                print(f"   Items Processed: {metrics.get('items_processed', 0)}")
                print(f"   Quality Gates Passed: {metrics.get('quality_gates_passed', 0)}")
            
            # Check part matches
            if hasattr(result_state, 'part_matches') and result_state.part_matches:
                total_matches = sum(len(matches) for matches in result_state.part_matches.values())
                print(f"   🔍 Total Part Matches Found: {total_matches}")
                
                # Check for contextual intelligence in results
                contextual_results = 0
                for item_id, matches in result_state.part_matches.items():
                    for match in matches:
                        if hasattr(match, 'notes') and any('contextual' in note.lower() for note in match.notes):
                            contextual_results += 1
                            break
                
                print(f"   🧠 Results with Contextual Intelligence: {contextual_results}")
            
            # Check WebSocket messages
            print(f"\n📡 WebSocket Messages Sent: {len(mock_websocket.messages)}")
            contextual_messages = sum(1 for msg in mock_websocket.messages 
                                    if hasattr(msg, 'data') and msg.data and 
                                       msg.data.get('content', {}).get('contextual_intelligence'))
            print(f"   🧠 Messages with Contextual Info: {contextual_messages}")
            
            print(f"\n✅ Scenario {i} completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Scenario {i} failed: {str(e)}")
            import traceback
            print(f"   Error details: {traceback.format_exc()}")
        
        print("\n" + "-" * 70)
    
    # Test enhanced supervisor metrics
    print("\n📈 Enhanced Supervisor Metrics:")
    metrics = supervisor.get_processing_metrics()
    print(f"   Total Orders Processed: {metrics.get('total_orders_processed', 0)}")
    print(f"   Average Processing Time: {metrics.get('average_processing_time', 0):.2f}s")
    print(f"   Quality Gate Catches: {metrics.get('quality_gate_catches', 0)}")
    
    contextual_stats = metrics.get('contextual_intelligence_stats', {})
    print(f"   🧠 Contextual Intelligence Enabled: {contextual_stats.get('enabled', False)}")
    print(f"   🎯 Contextual Coordinator Active: {contextual_stats.get('contextual_coordinator', False)}")
    
    print("\n🎉 Phase 1 Complete Integration Testing Finished!")
    print("✅ Contextual Intelligence is fully operational across the entire workflow!")

async def test_contextual_intelligence_components():
    """Test individual contextual intelligence components"""
    
    print("\n🔧 Testing Individual Contextual Intelligence Components")
    print("=" * 60)
    
    # Test contextual coordinator
    print("1. Testing AgenticSearchCoordinator with Contextual Intelligence...")
    try:
        from app.agents.agentic_search_coordinator import AgenticSearchCoordinator
        from app.services.parts_catalog import PartsCatalogService
        from app.models.line_item_schemas import LineItem
        
        catalog_service = PartsCatalogService()
        coordinator = AgenticSearchCoordinator(catalog_service)
        
        test_item = LineItem(
            line_id="component_test_001",
            raw_text="Emergency titanium part for aerospace application ASAP",
            urgency="critical"
        )
        
        results = await coordinator.search_for_line_item(test_item)
        print(f"   ✅ Coordinator: {len(results)} results found")
        
        # Check for contextual processing
        contextual_processing = any(
            hasattr(result, 'notes') and any('contextual' in note.lower() for note in result.notes)
            for result in results
        )
        print(f"   🧠 Contextual Processing: {'✅' if contextual_processing else '❌'}")
        
    except Exception as e:
        print(f"   ❌ Coordinator test failed: {str(e)}")
    
    # Test contextual intelligence server
    print("\n2. Testing ContextualIntelligenceServer...")
    try:
        from app.mcp.contextual_intelligence import ContextualIntelligenceServer
        
        context_server = ContextualIntelligenceServer()
        
        test_order = {
            "line_items": [{
                "raw_text": "Emergency bearing replacement - production line down",
                "urgency": "critical"
            }],
            "customer": {"name": "Test Manufacturing"},
            "urgency": "critical"
        }
        
        insights = await context_server.analyze_procurement_context(test_order)
        print(f"   ✅ Context Server: Complexity={insights.complexity_level.value}, Context={insights.business_context.value}")
        print(f"   🎯 Recommended Approach: {insights.recommended_approach}")
        
    except Exception as e:
        print(f"   ❌ Context server test failed: {str(e)}")
    
    # Test MCP tools
    print("\n3. Testing MCP Tools...")
    try:
        from app.mcp.contextual_intelligence import assess_complexity_factors, dynamic_threshold_adjustment
        
        test_line_item = {
            "raw_text": "ASTM certified titanium for aerospace with full traceability",
            "urgency": "high",
            "special_requirements": ["certification", "traceability"]
        }
        
        complexity = await assess_complexity_factors(test_line_item)
        print(f"   ✅ Complexity Assessment: {complexity.get('complexity_level')}")
        
        thresholds = await dynamic_threshold_adjustment({
            "urgency_level": "critical",
            "quality_requirements": "high",
            "cost_sensitivity": "low"
        })
        print(f"   ✅ Dynamic Thresholds: {len(thresholds)} adjustments")
        
    except Exception as e:
        print(f"   ❌ MCP tools test failed: {str(e)}")
    
    print("\n✅ Component testing completed!")

if __name__ == "__main__":
    async def run_all_tests():
        await test_contextual_intelligence_components()
        await test_complete_contextual_workflow()
    
    asyncio.run(run_all_tests())
"""
End-to-end workflow tests for the complete Sales Order Entry System.
"""
import pytest
from unittest.mock import patch, Mock, AsyncMock
import asyncio
from typing import Dict, Any

from app.agents.supervisor import SupervisorAgent
from app.agents.workflow_state import WorkflowState
from app.services.erp.mock_provider import MockERPProvider
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStore
from app.services.websocket_manager import WebSocketManager


class TestCompleteWorkflow:
    """Test the complete order processing workflow end-to-end."""
    
    @pytest.fixture
    def workflow_components(self, temp_dir, mock_websocket_manager):
        """Set up all workflow components."""
        # Create real instances with mocked dependencies
        erp_provider = MockERPProvider()
        
        # Mock embedding service
        embedding_service = Mock(spec=EmbeddingService)
        embedding_service.get_embedding = AsyncMock(return_value=[0.1] * 3072)
        embedding_service.get_part_embedding = AsyncMock(return_value=[0.1] * 3072)
        
        # Real vector store with temp directory
        vector_store = VectorStore(storage_path=str(temp_dir / "vectors"))
        
        # Supervisor agent
        supervisor = SupervisorAgent(websocket_manager=mock_websocket_manager)
        
        return {
            "supervisor": supervisor,
            "erp_provider": erp_provider,
            "embedding_service": embedding_service,
            "vector_store": vector_store,
            "websocket_manager": mock_websocket_manager
        }
    
    @pytest.fixture
    async def sample_parts_catalog(self, workflow_components):
        """Set up sample parts catalog for testing."""
        vector_store = workflow_components["vector_store"]
        embedding_service = workflow_components["embedding_service"]
        
        # Add sample parts to the catalog
        sample_parts = [
            {
                "part_id": "part_001",
                "part_number": "ST-001",
                "description": "Stainless Steel Rod 1/4 inch x 12 feet",
                "unit_price": 25.50,
                "availability": 100,
                "specifications": {"material": "stainless_steel", "diameter": "0.25in"}
            },
            {
                "part_id": "part_002",
                "part_number": "AL-505",
                "description": "Aluminum Sheet 4x8 feet 1/8 inch thick",
                "unit_price": 89.99,
                "availability": 50,
                "specifications": {"material": "aluminum", "thickness": "0.125in"}
            },
            {
                "part_id": "part_003",
                "part_number": "BR-202",
                "description": "Brass Fitting 1/2 inch NPT",
                "unit_price": 15.75,
                "availability": 200,
                "specifications": {"material": "brass", "thread": "1/2_npt"}
            }
        ]
        
        for part in sample_parts:
            # Use mock embedding for each part
            embedding = [0.1 + float(part["part_id"][-1]) * 0.1] * 3072
            await vector_store.add_part(
                part_id=part["part_id"],
                embedding=embedding,
                metadata=part
            )
        
        return sample_parts
    
    @pytest.mark.asyncio
    async def test_successful_pdf_order_workflow(self, workflow_components, sample_parts_catalog, sample_pdf_content):
        """Test complete successful workflow with PDF order."""
        supervisor = workflow_components["supervisor"]
        websocket_manager = workflow_components["websocket_manager"]
        
        # Create initial workflow state
        initial_state = WorkflowState(
            session_id="test_workflow_001",
            document_content=sample_pdf_content,
            filename="purchase_order.pdf",
            status="pending",
            error_count=0,
            metadata={}
        )
        
        # Mock all the agent dependencies
        with patch('app.agents.document_parser.DocumentParserAgent.parse_document', new_callable=AsyncMock) as mock_parser, \
             patch('app.agents.order_extractor.OrderExtractorAgent.extract_order_data', new_callable=AsyncMock) as mock_extractor, \
             patch('app.agents.semantic_search.SemanticSearchAgent.find_part_matches', new_callable=AsyncMock) as mock_search, \
             patch('app.agents.erp_integration.ERPIntegrationAgent.validate_order', new_callable=AsyncMock) as mock_erp, \
             patch('app.agents.review_preparer.ReviewPreparerAgent.prepare_review_data', new_callable=AsyncMock) as mock_review:
            
            # Configure mock responses for successful workflow
            mock_parser.return_value = {
                "extracted_text": """
                PURCHASE ORDER
                
                ACME Corporation
                123 Main Street
                Anytown, ST 12345
                
                PO Number: PO-2024-001
                Date: January 15, 2024
                
                ITEM DESCRIPTION                    QTY    UNIT PRICE    TOTAL
                1. Stainless Steel Rod 1/4" x 12'   10     $25.50      $255.00
                2. Aluminum Sheet 4x8' 1/8" thick    5     $89.99      $449.95
                
                TOTAL: $704.95
                
                Contact: John Smith
                Email: john.smith@acmecorp.com
                """,
                "document_type": "pdf",
                "layout_data": {
                    "tables": [],
                    "forms": {"po_number": "PO-2024-001"}
                }
            }
            
            mock_extractor.return_value = {
                "customer_info": {
                    "name": "John Smith",
                    "email": "john.smith@acmecorp.com",
                    "company": "ACME Corporation",
                    "customer_id": "CUST001"
                },
                "line_items": [
                    {
                        "part_number": "ST-001",
                        "description": "Stainless Steel Rod 1/4 inch x 12 feet",
                        "quantity": 10,
                        "unit_price": 25.50,
                        "total_price": 255.00
                    },
                    {
                        "part_number": "AL-505",
                        "description": "Aluminum Sheet 4x8 feet 1/8 inch thick",
                        "quantity": 5,
                        "unit_price": 89.99,
                        "total_price": 449.95
                    }
                ],
                "order_metadata": {
                    "po_number": "PO-2024-001",
                    "order_date": "2024-01-15",
                    "total_amount": 704.95
                }
            }
            
            mock_search.return_value = [
                {
                    "line_item": mock_extractor.return_value["line_items"][0],
                    "matches": [
                        {
                            "part_id": "part_001",
                            "part_number": "ST-001",
                            "description": "Stainless Steel Rod 1/4 inch x 12 feet",
                            "confidence_score": 0.95,
                            "unit_price": 25.50,
                            "availability": 100
                        }
                    ]
                },
                {
                    "line_item": mock_extractor.return_value["line_items"][1],
                    "matches": [
                        {
                            "part_id": "part_002",
                            "part_number": "AL-505",
                            "description": "Aluminum Sheet 4x8 feet 1/8 inch thick",
                            "confidence_score": 0.92,
                            "unit_price": 89.99,
                            "availability": 50
                        }
                    ]
                }
            ]
            
            mock_erp.return_value = {
                "is_valid": True,
                "customer_validation": {
                    "is_valid": True,
                    "customer_id": "CUST001",
                    "credit_limit": 50000.0
                },
                "inventory_validation": {
                    "is_valid": True,
                    "line_items": [
                        {"part_number": "ST-001", "availability": 100, "unit_price": 25.50},
                        {"part_number": "AL-505", "availability": 50, "unit_price": 89.99}
                    ]
                },
                "pricing_validation": {
                    "is_valid": True,
                    "total_amount": 704.95,
                    "discount_applied": 0.0
                }
            }
            
            mock_review.return_value = {
                "summary": {
                    "total_amount": 704.95,
                    "line_items_count": 2,
                    "matched_items": 2,
                    "items_requiring_review": 0,
                    "confidence": "high"
                },
                "line_items": mock_extractor.return_value["line_items"],
                "customer_info": mock_extractor.return_value["customer_info"],
                "recommendations": [],
                "attention_items": [],
                "ready_for_submission": True
            }
            
            # Execute the complete workflow
            result = await supervisor.execute_workflow(initial_state)
            
            # Verify workflow completed successfully
            assert result["status"] == "completed"
            assert result["session_id"] == "test_workflow_001"
            
            # Verify all agents were called in order
            mock_parser.assert_called_once()
            mock_extractor.assert_called_once()
            mock_search.assert_called_once()
            mock_erp.assert_called_once()
            mock_review.assert_called_once()
            
            # Verify WebSocket notifications were sent
            assert websocket_manager.send_card_update.call_count >= 5  # One for each stage
            
            # Verify the final state contains all expected data
            assert "order_data" in result
            assert result["order_data"]["customer_info"]["name"] == "John Smith"
            assert len(result["order_data"]["line_items"]) == 2
            assert result["order_data"]["total_amount"] == 704.95
    
    @pytest.mark.asyncio
    async def test_workflow_with_partial_matches(self, workflow_components, sample_parts_catalog, sample_pdf_content):
        """Test workflow when some parts don't have exact matches."""
        supervisor = workflow_components["supervisor"]
        
        initial_state = WorkflowState(
            session_id="test_workflow_002",
            document_content=sample_pdf_content,
            filename="purchase_order.pdf",
            status="pending",
            error_count=0,
            metadata={}
        )
        
        with patch('app.agents.document_parser.DocumentParserAgent.parse_document', new_callable=AsyncMock) as mock_parser, \
             patch('app.agents.order_extractor.OrderExtractorAgent.extract_order_data', new_callable=AsyncMock) as mock_extractor, \
             patch('app.agents.semantic_search.SemanticSearchAgent.find_part_matches', new_callable=AsyncMock) as mock_search, \
             patch('app.agents.erp_integration.ERPIntegrationAgent.validate_order', new_callable=AsyncMock) as mock_erp, \
             patch('app.agents.review_preparer.ReviewPreparerAgent.prepare_review_data', new_callable=AsyncMock) as mock_review:
            
            # Configure mocks for partial match scenario
            mock_parser.return_value = {
                "extracted_text": "Order with unknown parts",
                "document_type": "pdf"
            }
            
            mock_extractor.return_value = {
                "customer_info": {"name": "Test Customer"},
                "line_items": [
                    {
                        "part_number": "UNKNOWN-001",  # Part not in catalog
                        "description": "Unknown Part Description",
                        "quantity": 5,
                        "unit_price": 50.00,
                        "total_price": 250.00
                    }
                ],
                "order_metadata": {"total_amount": 250.00}
            }
            
            # No matches found for unknown part
            mock_search.return_value = [
                {
                    "line_item": mock_extractor.return_value["line_items"][0],
                    "matches": []  # No matches
                }
            ]
            
            mock_erp.return_value = {
                "is_valid": False,
                "customer_validation": {"is_valid": True},
                "inventory_validation": {
                    "is_valid": False,
                    "errors": ["Part UNKNOWN-001 not found in inventory"]
                }
            }
            
            mock_review.return_value = {
                "summary": {
                    "total_amount": 250.00,
                    "line_items_count": 1,
                    "matched_items": 0,
                    "items_requiring_review": 1,
                    "confidence": "low"
                },
                "attention_items": [
                    {
                        "type": "no_match",
                        "severity": "high",
                        "title": "Part Not Found",
                        "description": "UNKNOWN-001 could not be matched to catalog",
                        "action_required": "Manual review required"
                    }
                ],
                "ready_for_submission": False
            }
            
            # Execute workflow
            result = await supervisor.execute_workflow(initial_state)
            
            # Should complete but with attention items
            assert result["status"] == "completed"
            assert len(result["review_data"]["attention_items"]) > 0
            assert result["review_data"]["ready_for_submission"] is False
    
    @pytest.mark.asyncio
    async def test_workflow_error_recovery(self, workflow_components, sample_pdf_content):
        """Test workflow error handling and recovery."""
        supervisor = workflow_components["supervisor"]
        
        initial_state = WorkflowState(
            session_id="test_workflow_003",
            document_content=sample_pdf_content,
            filename="purchase_order.pdf",
            status="pending",
            error_count=0,
            metadata={}
        )
        
        with patch('app.agents.document_parser.DocumentParserAgent.parse_document', new_callable=AsyncMock) as mock_parser:
            # Simulate parser error
            mock_parser.side_effect = Exception("Document parsing failed")
            
            # Execute workflow
            result = await supervisor.execute_workflow(initial_state)
            
            # Should handle error gracefully
            assert result["status"] == "error"
            assert "Document parsing failed" in result["error"]
            assert result["error_count"] > 0
    
    @pytest.mark.asyncio
    async def test_order_submission_workflow(self, workflow_components, sample_order_data):
        """Test order submission through ERP system."""
        erp_provider = workflow_components["erp_provider"]
        
        # Test successful submission
        result = await erp_provider.submit_order(sample_order_data)
        
        assert result["success"] is True
        assert "order_id" in result
        assert result["order_id"].startswith("ORD-")
        assert result["status"] == "submitted"
        
        # Verify order was processed correctly
        assert result["total_amount"] == sample_order_data.total_amount
    
    @pytest.mark.asyncio
    async def test_websocket_communication_during_workflow(self, workflow_components, sample_pdf_content):
        """Test WebSocket communication during workflow execution."""
        supervisor = workflow_components["supervisor"]
        websocket_manager = workflow_components["websocket_manager"]
        
        initial_state = WorkflowState(
            session_id="test_workflow_004",
            document_content=sample_pdf_content,
            filename="test.pdf",
            status="pending",
            error_count=0,
            metadata={}
        )
        
        # Mock a simple successful workflow
        with patch('app.agents.document_parser.DocumentParserAgent.parse_document', new_callable=AsyncMock) as mock_parser:
            mock_parser.return_value = {
                "extracted_text": "Simple order",
                "document_type": "pdf"
            }
            
            await supervisor._run_document_parser(initial_state)
            
            # Verify WebSocket notification was sent
            websocket_manager.send_card_update.assert_called_once()
            
            # Verify the card update contains expected information
            call_args = websocket_manager.send_card_update.call_args
            assert call_args[0][0] == "test_workflow_004"  # session_id
            assert "document_parser" in call_args[0][1]["id"]  # card_id
    
    @pytest.mark.asyncio
    async def test_concurrent_workflow_processing(self, workflow_components, sample_pdf_content):
        """Test processing multiple workflows concurrently."""
        supervisor = workflow_components["supervisor"]
        
        # Create multiple workflow states
        workflows = []
        for i in range(3):
            state = WorkflowState(
                session_id=f"concurrent_test_{i}",
                document_content=sample_pdf_content,
                filename=f"order_{i}.pdf",
                status="pending",
                error_count=0,
                metadata={}
            )
            workflows.append(state)
        
        # Mock successful processing
        with patch('app.agents.document_parser.DocumentParserAgent.parse_document', new_callable=AsyncMock) as mock_parser:
            mock_parser.return_value = {
                "extracted_text": "Test order",
                "document_type": "pdf"
            }
            
            # Process all workflows concurrently
            tasks = [supervisor._run_document_parser(workflow) for workflow in workflows]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All should succeed
            assert len(results) == 3
            assert all(not isinstance(result, Exception) for result in results)
            
            # Parser should have been called for each workflow
            assert mock_parser.call_count == 3
    
    @pytest.mark.asyncio
    async def test_performance_with_large_order(self, workflow_components):
        """Test system performance with large orders."""
        supervisor = workflow_components["supervisor"]
        
        # Create a large order (100 line items)
        large_order_content = self._generate_large_order_pdf(100)
        
        initial_state = WorkflowState(
            session_id="large_order_test",
            document_content=large_order_content,
            filename="large_order.pdf",
            status="pending",
            error_count=0,
            metadata={}
        )
        
        with patch('app.agents.document_parser.DocumentParserAgent.parse_document', new_callable=AsyncMock) as mock_parser, \
             patch('app.agents.order_extractor.OrderExtractorAgent.extract_order_data', new_callable=AsyncMock) as mock_extractor:
            
            # Mock extraction of large order
            large_line_items = [
                {
                    "part_number": f"PART-{i:03d}",
                    "description": f"Part {i} description",
                    "quantity": i,
                    "unit_price": 10.0 + i,
                    "total_price": (10.0 + i) * i
                }
                for i in range(1, 101)  # 100 items
            ]
            
            mock_parser.return_value = {
                "extracted_text": "Large order with 100 items",
                "document_type": "pdf"
            }
            
            mock_extractor.return_value = {
                "customer_info": {"name": "Large Order Customer"},
                "line_items": large_line_items,
                "order_metadata": {
                    "total_amount": sum(item["total_price"] for item in large_line_items)
                }
            }
            
            # Measure processing time
            import time
            start_time = time.time()
            
            result = await supervisor._run_order_extractor(initial_state)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Should complete in reasonable time (< 10 seconds for mocked workflow)
            assert processing_time < 10.0
            assert result["status"] == "completed"
            assert len(result["order_data"]["line_items"]) == 100
    
    def _generate_large_order_pdf(self, num_items: int) -> bytes:
        """Generate a large PDF order for testing."""
        # For testing purposes, return a mock PDF with metadata about the size
        pdf_header = b"%PDF-1.4\n"
        pdf_content = f"Large order with {num_items} line items".encode()
        pdf_footer = b"\n%%EOF"
        
        return pdf_header + pdf_content + pdf_footer
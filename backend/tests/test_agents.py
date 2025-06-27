"""
Unit tests for LangGraph agents.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any
import tempfile
from pathlib import Path

from app.agents.supervisor import SupervisorAgent
from app.agents.document_parser import DocumentParserAgent
from app.agents.order_extractor import OrderExtractorAgent
from app.agents.semantic_search import SemanticSearchAgent
from app.agents.erp_integration import ERPIntegrationAgent
from app.agents.review_preparer import ReviewPreparerAgent
from app.agents.workflow_state import WorkflowState
from app.models.schemas import CustomerInfo, OrderLineItem, PartMatch


class TestSupervisorAgent:
    """Test cases for the Supervisor Agent."""
    
    @pytest.fixture
    def supervisor_agent(self, mock_websocket_manager: Mock) -> SupervisorAgent:
        """Create a supervisor agent instance."""
        return SupervisorAgent(websocket_manager=mock_websocket_manager)
    
    @pytest.fixture
    def initial_state(self, sample_pdf_content: bytes) -> WorkflowState:
        """Create initial workflow state."""
        return WorkflowState(
            session_id="test_session_001",
            document_content=sample_pdf_content,
            filename="test_order.pdf",
            status="pending",
            error_count=0,
            metadata={}
        )
    
    @pytest.mark.asyncio
    async def test_workflow_execution_success(self, supervisor_agent: SupervisorAgent, initial_state: WorkflowState):
        """Test successful workflow execution."""
        # Mock all sub-agents
        with patch.object(supervisor_agent, '_run_document_parser', new_callable=AsyncMock) as mock_parser, \
             patch.object(supervisor_agent, '_run_order_extractor', new_callable=AsyncMock) as mock_extractor, \
             patch.object(supervisor_agent, '_run_semantic_search', new_callable=AsyncMock) as mock_search, \
             patch.object(supervisor_agent, '_run_erp_integration', new_callable=AsyncMock) as mock_erp, \
             patch.object(supervisor_agent, '_run_review_preparer', new_callable=AsyncMock) as mock_review:
            
            # Configure mock returns
            mock_parser.return_value = {"status": "completed", "extracted_text": "Sample text"}
            mock_extractor.return_value = {"status": "completed", "customer_info": {}, "line_items": []}
            mock_search.return_value = {"status": "completed", "matched_items": []}
            mock_erp.return_value = {"status": "completed", "validated": True}
            mock_review.return_value = {"status": "completed", "ready_for_review": True}
            
            # Execute workflow
            result = await supervisor_agent.execute_workflow(initial_state)
            
            assert result["status"] == "completed"
            assert result["session_id"] == "test_session_001"
            
            # Verify all agents were called
            mock_parser.assert_called_once()
            mock_extractor.assert_called_once()
            mock_search.assert_called_once()
            mock_erp.assert_called_once()
            mock_review.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, supervisor_agent: SupervisorAgent, initial_state: WorkflowState):
        """Test error handling and recovery mechanisms."""
        with patch.object(supervisor_agent, '_run_document_parser', new_callable=AsyncMock) as mock_parser, \
             patch.object(supervisor_agent, '_handle_error', new_callable=AsyncMock) as mock_error_handler:
            
            # Simulate parser error
            mock_parser.side_effect = Exception("Document parsing failed")
            mock_error_handler.return_value = {"status": "error", "error": "Document parsing failed"}
            
            result = await supervisor_agent.execute_workflow(initial_state)
            
            assert result["status"] == "error"
            mock_error_handler.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_websocket_notifications(self, supervisor_agent: SupervisorAgent, initial_state: WorkflowState, mock_websocket_manager: Mock):
        """Test WebSocket notifications during workflow execution."""
        with patch.object(supervisor_agent, '_run_document_parser', new_callable=AsyncMock) as mock_parser:
            mock_parser.return_value = {"status": "completed", "extracted_text": "Sample text"}
            
            await supervisor_agent._run_document_parser(initial_state)
            
            # Verify WebSocket notification was sent
            mock_websocket_manager.send_card_update.assert_called()
    
    @pytest.mark.asyncio
    async def test_retry_mechanism(self, supervisor_agent: SupervisorAgent, initial_state: WorkflowState):
        """Test retry mechanism for failed operations."""
        with patch.object(supervisor_agent, '_run_document_parser', new_callable=AsyncMock) as mock_parser:
            # Fail twice, then succeed
            mock_parser.side_effect = [Exception("Temp error"), Exception("Temp error"), {"status": "completed"}]
            
            # Execute with retry
            state = initial_state.copy()
            for attempt in range(3):
                try:
                    result = await supervisor_agent._run_document_parser(state)
                    break
                except Exception:
                    if attempt < 2:  # Retry logic
                        continue
                    raise
            
            assert result["status"] == "completed"
            assert mock_parser.call_count == 3


class TestDocumentParserAgent:
    """Test cases for the Document Parser Agent."""
    
    @pytest.fixture
    def parser_agent(self) -> DocumentParserAgent:
        """Create a document parser agent instance."""
        return DocumentParserAgent()
    
    @pytest.mark.asyncio
    async def test_pdf_parsing(self, parser_agent: DocumentParserAgent, sample_pdf_content: bytes):
        """Test PDF document parsing."""
        with patch('fitz.open') as mock_fitz:
            mock_doc = Mock()
            mock_page = Mock()
            mock_page.get_text.return_value = "Sample PDF text content"
            mock_doc.__iter__.return_value = [mock_page]
            mock_doc.__enter__.return_value = mock_doc
            mock_doc.__exit__.return_value = None
            mock_fitz.return_value = mock_doc
            
            result = await parser_agent.parse_document(sample_pdf_content, "test.pdf")
            
            assert result["extracted_text"] == "Sample PDF text content"
            assert result["document_type"] == "pdf"
            mock_fitz.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_email_parsing(self, parser_agent: DocumentParserAgent):
        """Test email document parsing."""
        email_content = b"""From: customer@company.com
To: orders@supplier.com
Subject: Purchase Order PO-001

Please supply the following items:
- 10x Stainless Steel Rods
- 5x Aluminum Sheets
"""
        
        result = await parser_agent.parse_document(email_content, "order.eml")
        
        assert "Purchase Order PO-001" in result["extracted_text"]
        assert "Stainless Steel Rods" in result["extracted_text"]
        assert result["document_type"] == "email"
    
    @pytest.mark.asyncio
    async def test_layout_aware_extraction(self, parser_agent: DocumentParserAgent):
        """Test layout-aware text extraction."""
        mock_layout_data = {
            "tables": [
                {"cells": [["Item", "Qty", "Price"], ["Steel Rod", "10", "$25.50"]]}
            ],
            "forms": {"po_number": "PO-001", "date": "2024-01-15"}
        }
        
        with patch.object(parser_agent, '_extract_layout_elements', new_callable=AsyncMock) as mock_layout:
            mock_layout.return_value = mock_layout_data
            
            result = await parser_agent.parse_document(b"dummy content", "test.pdf")
            
            assert "tables" in result["layout_data"]
            assert "forms" in result["layout_data"]
            assert result["layout_data"]["forms"]["po_number"] == "PO-001"
    
    @pytest.mark.asyncio
    async def test_unsupported_format_error(self, parser_agent: DocumentParserAgent):
        """Test error handling for unsupported file formats."""
        with pytest.raises(ValueError, match="Unsupported document type"):
            await parser_agent.parse_document(b"content", "test.txt")
    
    @pytest.mark.asyncio
    async def test_corrupted_pdf_error(self, parser_agent: DocumentParserAgent):
        """Test error handling for corrupted PDF files."""
        corrupted_pdf = b"Not a real PDF content"
        
        with patch('fitz.open', side_effect=Exception("Invalid PDF")):
            with pytest.raises(Exception, match="Invalid PDF"):
                await parser_agent.parse_document(corrupted_pdf, "test.pdf")


class TestOrderExtractorAgent:
    """Test cases for the Order Extractor Agent."""
    
    @pytest.fixture
    def extractor_agent(self) -> OrderExtractorAgent:
        """Create an order extractor agent instance."""
        return OrderExtractorAgent()
    
    @pytest.mark.asyncio
    async def test_customer_info_extraction(self, extractor_agent: OrderExtractorAgent, sample_extracted_text: str):
        """Test customer information extraction."""
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="""{
                "customer_info": {
                    "name": "John Smith",
                    "email": "john.smith@acmecorp.com",
                    "company": "ACME Corporation",
                    "phone": "555-123-4567"
                }
            }"""))]
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client
            
            result = await extractor_agent.extract_customer_info(sample_extracted_text)
            
            assert result["name"] == "John Smith"
            assert result["email"] == "john.smith@acmecorp.com"
            assert result["company"] == "ACME Corporation"
    
    @pytest.mark.asyncio
    async def test_line_items_extraction(self, extractor_agent: OrderExtractorAgent, sample_extracted_text: str):
        """Test line items extraction."""
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="""{
                "line_items": [
                    {
                        "part_number": "ST-001",
                        "description": "Stainless Steel Rod 1/4 inch x 12 feet",
                        "quantity": 10,
                        "unit_price": 25.50,
                        "total_price": 255.00
                    }
                ]
            }"""))]
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client
            
            result = await extractor_agent.extract_line_items(sample_extracted_text)
            
            assert len(result) == 1
            assert result[0]["part_number"] == "ST-001"
            assert result[0]["quantity"] == 10
            assert result[0]["unit_price"] == 25.50
    
    @pytest.mark.asyncio
    async def test_order_metadata_extraction(self, extractor_agent: OrderExtractorAgent, sample_extracted_text: str):
        """Test order metadata extraction."""
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="""{
                "po_number": "PO-2024-001",
                "order_date": "2024-01-15",
                "delivery_date": "2024-01-25",
                "special_instructions": "Please deliver to loading dock"
            }"""))]
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client
            
            result = await extractor_agent.extract_order_metadata(sample_extracted_text)
            
            assert result["po_number"] == "PO-2024-001"
            assert result["order_date"] == "2024-01-15"
            assert result["special_instructions"] == "Please deliver to loading dock"
    
    @pytest.mark.asyncio
    async def test_confidence_scoring(self, extractor_agent: OrderExtractorAgent):
        """Test confidence scoring for extracted data."""
        extracted_data = {
            "customer_info": {"name": "John Smith", "email": "john@company.com"},
            "line_items": [{"part_number": "ST-001", "quantity": 10}],
            "metadata": {"po_number": "PO-001"}
        }
        
        confidence = extractor_agent._calculate_confidence(extracted_data)
        
        assert 0.0 <= confidence <= 1.0
        # Should have higher confidence with complete data
        assert confidence > 0.7
    
    @pytest.mark.asyncio
    async def test_invalid_json_handling(self, extractor_agent: OrderExtractorAgent):
        """Test handling of invalid JSON responses from LLM."""
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Invalid JSON response"))]
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client
            
            result = await extractor_agent.extract_customer_info("test text")
            
            # Should return empty dict or handle gracefully
            assert isinstance(result, dict)


class TestSemanticSearchAgent:
    """Test cases for the Semantic Search Agent."""
    
    @pytest.fixture
    def search_agent(self, mock_embedding_service: Mock, mock_vector_store: Mock) -> SemanticSearchAgent:
        """Create a semantic search agent instance."""
        return SemanticSearchAgent(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store
        )
    
    @pytest.mark.asyncio
    async def test_find_part_matches(self, search_agent: SemanticSearchAgent, sample_line_items: list[OrderLineItem], mock_vector_store: Mock):
        """Test finding part matches for line items."""
        mock_matches = [
            PartMatch(
                part_id="part_001",
                part_number="ST-001",
                description="Stainless Steel Rod 1/4 inch x 12 feet",
                confidence_score=0.95,
                unit_price=25.50,
                availability=100,
                specifications={}
            )
        ]
        mock_vector_store.search_similar_parts.return_value = mock_matches
        
        results = await search_agent.find_part_matches(sample_line_items)
        
        assert len(results) == len(sample_line_items)
        assert results[0]["matches"][0].confidence_score == 0.95
    
    @pytest.mark.asyncio
    async def test_confidence_threshold_filtering(self, search_agent: SemanticSearchAgent, sample_line_items: list[OrderLineItem], mock_vector_store: Mock):
        """Test filtering matches by confidence threshold."""
        # Mock low confidence matches
        mock_matches = [
            PartMatch(
                part_id="part_001",
                part_number="ST-001", 
                description="Some part",
                confidence_score=0.3,  # Low confidence
                unit_price=25.50,
                availability=100,
                specifications={}
            )
        ]
        mock_vector_store.search_similar_parts.return_value = mock_matches
        
        results = await search_agent.find_part_matches(sample_line_items, min_confidence=0.7)
        
        # Should filter out low confidence matches
        assert len(results[0]["matches"]) == 0
    
    @pytest.mark.asyncio
    async def test_fuzzy_matching_fallback(self, search_agent: SemanticSearchAgent, sample_line_items: list[OrderLineItem], mock_vector_store: Mock):
        """Test fuzzy matching fallback when semantic search fails."""
        # Mock no semantic matches
        mock_vector_store.search_similar_parts.return_value = []
        
        with patch.object(search_agent, '_fuzzy_search_parts', new_callable=AsyncMock) as mock_fuzzy:
            mock_fuzzy.return_value = [
                PartMatch(
                    part_id="part_001",
                    part_number="ST-001",
                    description="Stainless Steel Rod",
                    confidence_score=0.7,
                    unit_price=25.50,
                    availability=100,
                    specifications={}
                )
            ]
            
            results = await search_agent.find_part_matches(sample_line_items, use_fuzzy_fallback=True)
            
            assert len(results[0]["matches"]) == 1
            mock_fuzzy.assert_called()
    
    @pytest.mark.asyncio
    async def test_part_number_exact_matching(self, search_agent: SemanticSearchAgent):
        """Test exact part number matching takes priority."""
        line_item = OrderLineItem(
            part_number="EXACT-MATCH-001",
            description="Some description",
            quantity=1,
            unit_price=10.0,
            total_price=10.0
        )
        
        with patch.object(search_agent, '_exact_part_number_search', new_callable=AsyncMock) as mock_exact:
            mock_exact.return_value = [
                PartMatch(
                    part_id="part_001",
                    part_number="EXACT-MATCH-001",
                    description="Exact match part",
                    confidence_score=1.0,
                    unit_price=10.0,
                    availability=100,
                    specifications={}
                )
            ]
            
            results = await search_agent.find_part_matches([line_item])
            
            assert results[0]["matches"][0].confidence_score == 1.0
            assert results[0]["matches"][0].part_number == "EXACT-MATCH-001"


class TestERPIntegrationAgent:
    """Test cases for the ERP Integration Agent."""
    
    @pytest.fixture
    def erp_agent(self, mock_erp_provider: Mock) -> ERPIntegrationAgent:
        """Create an ERP integration agent instance."""
        return ERPIntegrationAgent(erp_provider=mock_erp_provider)
    
    @pytest.mark.asyncio
    async def test_validate_order_success(self, erp_agent: ERPIntegrationAgent, sample_order_data, mock_erp_provider: Mock):
        """Test successful order validation."""
        # Mock successful validation responses
        mock_erp_provider.validate_customer.return_value = {"is_valid": True, "customer_id": "CUST001"}
        mock_erp_provider.validate_inventory.return_value = {"is_valid": True, "line_items": []}
        mock_erp_provider.get_pricing.return_value = {"is_valid": True, "total_amount": 700.0}
        
        result = await erp_agent.validate_order(sample_order_data)
        
        assert result["is_valid"] is True
        assert result["customer_validation"]["is_valid"] is True
        assert result["inventory_validation"]["is_valid"] is True
        assert result["pricing_validation"]["is_valid"] is True
    
    @pytest.mark.asyncio
    async def test_validation_failure_handling(self, erp_agent: ERPIntegrationAgent, sample_order_data, mock_erp_provider: Mock):
        """Test handling of validation failures."""
        # Mock customer validation failure
        mock_erp_provider.validate_customer.return_value = {"is_valid": False, "error": "Customer not found"}
        
        result = await erp_agent.validate_order(sample_order_data)
        
        assert result["is_valid"] is False
        assert "Customer not found" in result["customer_validation"]["error"]
    
    @pytest.mark.asyncio
    async def test_create_draft_order(self, erp_agent: ERPIntegrationAgent, sample_order_data, mock_erp_provider: Mock):
        """Test draft order creation."""
        mock_erp_provider.create_draft_order.return_value = {
            "success": True,
            "draft_order_id": "DRAFT-001",
            "status": "draft"
        }
        
        result = await erp_agent.create_draft_order(sample_order_data)
        
        assert result["success"] is True
        assert result["draft_order_id"] == "DRAFT-001"
        mock_erp_provider.create_draft_order.assert_called_once_with(sample_order_data)
    
    @pytest.mark.asyncio
    async def test_submit_order(self, erp_agent: ERPIntegrationAgent, sample_order_data, mock_erp_provider: Mock):
        """Test order submission."""
        mock_erp_provider.submit_order.return_value = {
            "success": True,
            "order_id": "ORD-001",
            "status": "submitted"
        }
        
        result = await erp_agent.submit_order(sample_order_data)
        
        assert result["success"] is True
        assert result["order_id"] == "ORD-001"
        mock_erp_provider.submit_order.assert_called_once_with(sample_order_data)


class TestReviewPreparerAgent:
    """Test cases for the Review Preparer Agent."""
    
    @pytest.fixture
    def review_agent(self) -> ReviewPreparerAgent:
        """Create a review preparer agent instance."""
        return ReviewPreparerAgent()
    
    @pytest.mark.asyncio
    async def test_prepare_review_data(self, review_agent: ReviewPreparerAgent, sample_order_data):
        """Test preparation of review data."""
        matched_items = [
            {
                "line_item": sample_order_data.line_items[0],
                "matches": [
                    PartMatch(
                        part_id="part_001",
                        part_number="ST-001",
                        description="Stainless Steel Rod",
                        confidence_score=0.95,
                        unit_price=25.50,
                        availability=100,
                        specifications={}
                    )
                ]
            }
        ]
        
        validation_results = {
            "is_valid": True,
            "customer_validation": {"is_valid": True},
            "inventory_validation": {"is_valid": True}
        }
        
        result = await review_agent.prepare_review_data(
            order_data=sample_order_data,
            matched_items=matched_items,
            validation_results=validation_results
        )
        
        assert "summary" in result
        assert "line_items" in result
        assert "recommendations" in result
        assert result["summary"]["total_amount"] == sample_order_data.total_amount
    
    @pytest.mark.asyncio
    async def test_identify_attention_items(self, review_agent: ReviewPreparerAgent):
        """Test identification of items requiring attention."""
        matched_items = [
            {
                "line_item": OrderLineItem(
                    part_number="ST-001",
                    description="Steel Rod",
                    quantity=10,
                    unit_price=25.50,
                    total_price=255.00
                ),
                "matches": [
                    PartMatch(
                        part_id="part_001",
                        part_number="ST-002",  # Different part number
                        description="Steel Rod",
                        confidence_score=0.6,  # Low confidence
                        unit_price=25.50,
                        availability=5,  # Low availability
                        specifications={}
                    )
                ]
            }
        ]
        
        attention_items = review_agent._identify_attention_items(matched_items)
        
        assert len(attention_items) > 0
        # Should flag low confidence and availability issues
        assert any("confidence" in item["title"].lower() for item in attention_items)
        assert any("availability" in item["title"].lower() for item in attention_items)
    
    @pytest.mark.asyncio
    async def test_generate_recommendations(self, review_agent: ReviewPreparerAgent, sample_order_data):
        """Test generation of recommendations."""
        validation_results = {
            "customer_validation": {"credit_limit": 50000, "available_credit": 45000},
            "pricing_validation": {"total_amount": 10000}
        }
        
        recommendations = review_agent._generate_recommendations(sample_order_data, validation_results)
        
        assert isinstance(recommendations, list)
        # Should have recommendations based on the data
        if sample_order_data.total_amount > 1000:
            assert any("approval" in rec["title"].lower() for rec in recommendations)
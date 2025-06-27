"""
Unit tests for ERP services and providers.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal

from app.services.erp.mock_provider import MockERPProvider
from app.services.erp.dynamics_provider import DynamicsERPProvider
from app.models.schemas import CustomerInfo, OrderLineItem, OrderData


class TestMockERPProvider:
    """Test cases for the Mock ERP Provider."""
    
    @pytest.fixture
    def mock_provider(self) -> MockERPProvider:
        """Create a mock ERP provider instance."""
        return MockERPProvider()
    
    @pytest.mark.asyncio
    async def test_validate_customer_success(self, mock_provider: MockERPProvider, sample_customer_info: CustomerInfo):
        """Test successful customer validation."""
        result = await mock_provider.validate_customer(sample_customer_info)
        
        assert result["is_valid"] is True
        assert result["customer_id"] == sample_customer_info.customer_id
        assert result["credit_limit"] > 0
        assert result["payment_terms"] in ["NET30", "NET15", "COD"]
    
    @pytest.mark.asyncio
    async def test_validate_customer_invalid(self, mock_provider: MockERPProvider):
        """Test customer validation with invalid customer."""
        invalid_customer = CustomerInfo(
            name="Invalid Customer",
            email="invalid@invalid.com",
            customer_id="INVALID"
        )
        
        result = await mock_provider.validate_customer(invalid_customer)
        
        assert result["is_valid"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_validate_inventory_success(self, mock_provider: MockERPProvider, sample_line_items: list[OrderLineItem]):
        """Test successful inventory validation."""
        result = await mock_provider.validate_inventory(sample_line_items)
        
        assert result["is_valid"] is True
        assert len(result["line_items"]) == len(sample_line_items)
        
        for item in result["line_items"]:
            assert item["availability"] >= 0
            assert item["unit_price"] > 0
            assert "lead_time_days" in item
    
    @pytest.mark.asyncio
    async def test_validate_inventory_insufficient_stock(self, mock_provider: MockERPProvider):
        """Test inventory validation with insufficient stock."""
        large_qty_item = OrderLineItem(
            part_number="ST-001",
            description="Test item",
            quantity=10000,  # Very large quantity to trigger insufficient stock
            unit_price=25.50,
            total_price=255000.00
        )
        
        result = await mock_provider.validate_inventory([large_qty_item])
        
        # Should still be valid but with warnings about availability
        assert result["is_valid"] is True
        line_item = result["line_items"][0]
        assert line_item["availability"] < large_qty_item.quantity
    
    @pytest.mark.asyncio
    async def test_get_pricing_success(self, mock_provider: MockERPProvider, sample_line_items: list[OrderLineItem], sample_customer_info: CustomerInfo):
        """Test successful pricing retrieval."""
        result = await mock_provider.get_pricing(sample_line_items, sample_customer_info)
        
        assert result["is_valid"] is True
        assert len(result["line_items"]) == len(sample_line_items)
        assert result["total_amount"] > 0
        
        for item in result["line_items"]:
            assert item["unit_price"] > 0
            assert item["line_total"] > 0
            assert "discount_percent" in item
    
    @pytest.mark.asyncio
    async def test_create_draft_order_success(self, mock_provider: MockERPProvider, sample_order_data: OrderData):
        """Test successful draft order creation."""
        result = await mock_provider.create_draft_order(sample_order_data)
        
        assert result["success"] is True
        assert "draft_order_id" in result
        assert result["draft_order_id"].startswith("DRAFT-")
        assert result["status"] == "draft"
        assert result["total_amount"] == sample_order_data.total_amount
    
    @pytest.mark.asyncio
    async def test_submit_order_success(self, mock_provider: MockERPProvider, sample_order_data: OrderData):
        """Test successful order submission."""
        result = await mock_provider.submit_order(sample_order_data)
        
        assert result["success"] is True
        assert "order_id" in result
        assert result["order_id"].startswith("ORD-")
        assert result["status"] == "submitted"
        assert "estimated_delivery" in result
    
    @pytest.mark.asyncio
    async def test_api_delay_simulation(self, mock_provider: MockERPProvider, sample_customer_info: CustomerInfo):
        """Test that API delay simulation works."""
        import time
        
        start_time = time.time()
        await mock_provider.validate_customer(sample_customer_info)
        end_time = time.time()
        
        # Should have at least some delay (default is 0.5-2.0 seconds, but might be configured differently)
        elapsed = end_time - start_time
        assert elapsed >= 0.1  # At least 100ms delay


class TestDynamicsERPProvider:
    """Test cases for the Dynamics ERP Provider."""
    
    @pytest.fixture
    def dynamics_provider(self) -> DynamicsERPProvider:
        """Create a Dynamics ERP provider instance."""
        with patch.dict('os.environ', {
            'DYNAMICS_CLIENT_ID': 'test-client-id',
            'DYNAMICS_CLIENT_SECRET': 'test-client-secret',
            'DYNAMICS_TENANT_ID': 'test-tenant-id',
            'DYNAMICS_RESOURCE_URL': 'https://test.dynamics.com'
        }):
            return DynamicsERPProvider()
    
    @pytest.mark.asyncio
    async def test_authentication_flow(self, dynamics_provider: DynamicsERPProvider):
        """Test the authentication flow for Dynamics."""
        with patch('app.services.erp.dynamics_provider.ClientSecretCredential') as mock_credential:
            mock_token = Mock()
            mock_token.token = "test-access-token"
            mock_credential.return_value.get_token.return_value = mock_token
            
            token = await dynamics_provider._get_access_token()
            
            assert token == "test-access-token"
            mock_credential.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_customer_api_call(self, dynamics_provider: DynamicsERPProvider, sample_customer_info: CustomerInfo):
        """Test customer validation API call."""
        mock_response_data = {
            "value": [{
                "accountid": "test-account-id",
                "name": sample_customer_info.name,
                "emailaddress1": sample_customer_info.email,
                "creditlimit": 50000.0,
                "paymenttermscode": 2  # NET30
            }]
        }
        
        with patch.object(dynamics_provider, '_make_api_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data
            
            result = await dynamics_provider.validate_customer(sample_customer_info)
            
            assert result["is_valid"] is True
            assert result["customer_id"] == "test-account-id"
            assert result["credit_limit"] == 50000.0
            mock_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_customer_not_found(self, dynamics_provider: DynamicsERPProvider, sample_customer_info: CustomerInfo):
        """Test customer validation when customer is not found."""
        mock_response_data = {"value": []}
        
        with patch.object(dynamics_provider, '_make_api_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data
            
            result = await dynamics_provider.validate_customer(sample_customer_info)
            
            assert result["is_valid"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, dynamics_provider: DynamicsERPProvider, sample_customer_info: CustomerInfo):
        """Test API error handling."""
        with patch.object(dynamics_provider, '_make_api_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = Exception("API Error")
            
            result = await dynamics_provider.validate_customer(sample_customer_info)
            
            assert result["is_valid"] is False
            assert "error" in result
            assert "API Error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, dynamics_provider: DynamicsERPProvider):
        """Test rate limiting functionality."""
        # Test that rate limiting allows requests within limits
        for i in range(5):  # Should be within rate limits
            with patch.object(dynamics_provider, '_make_api_request', new_callable=AsyncMock) as mock_request:
                mock_request.return_value = {"value": []}
                result = await dynamics_provider.validate_customer(CustomerInfo(name=f"Customer {i}"))
                assert "error" not in result or "rate limit" not in result.get("error", "").lower()


class TestERPProviderFactory:
    """Test cases for ERP provider factory."""
    
    def test_create_mock_provider(self):
        """Test creating mock provider through factory."""
        with patch.dict('os.environ', {'ERP_PROVIDER': 'mock'}):
            from app.services.erp.base import create_erp_provider
            provider = create_erp_provider()
            assert isinstance(provider, MockERPProvider)
    
    def test_create_dynamics_provider(self):
        """Test creating Dynamics provider through factory."""
        with patch.dict('os.environ', {
            'ERP_PROVIDER': 'dynamics',
            'DYNAMICS_CLIENT_ID': 'test-id',
            'DYNAMICS_CLIENT_SECRET': 'test-secret',
            'DYNAMICS_TENANT_ID': 'test-tenant',
            'DYNAMICS_RESOURCE_URL': 'https://test.dynamics.com'
        }):
            from app.services.erp.base import create_erp_provider
            provider = create_erp_provider()
            assert isinstance(provider, DynamicsERPProvider)
    
    def test_invalid_provider_type(self):
        """Test error handling for invalid provider type."""
        with patch.dict('os.environ', {'ERP_PROVIDER': 'invalid'}):
            from app.services.erp.base import create_erp_provider
            with pytest.raises(ValueError, match="Unknown ERP provider"):
                create_erp_provider()


class TestERPIntegrationWorkflows:
    """Test complete ERP integration workflows."""
    
    @pytest.mark.asyncio
    async def test_complete_order_workflow(self, mock_provider: MockERPProvider, sample_order_data: OrderData):
        """Test complete order processing workflow."""
        # Step 1: Validate customer
        customer_result = await mock_provider.validate_customer(sample_order_data.customer_info)
        assert customer_result["is_valid"] is True
        
        # Step 2: Validate inventory
        inventory_result = await mock_provider.validate_inventory(sample_order_data.line_items)
        assert inventory_result["is_valid"] is True
        
        # Step 3: Get pricing
        pricing_result = await mock_provider.get_pricing(sample_order_data.line_items, sample_order_data.customer_info)
        assert pricing_result["is_valid"] is True
        
        # Step 4: Create draft order
        draft_result = await mock_provider.create_draft_order(sample_order_data)
        assert draft_result["success"] is True
        
        # Step 5: Submit order
        submit_result = await mock_provider.submit_order(sample_order_data)
        assert submit_result["success"] is True
        
        # Verify order ID is different from draft ID
        assert submit_result["order_id"] != draft_result["draft_order_id"]
    
    @pytest.mark.asyncio
    async def test_workflow_with_errors(self, mock_provider: MockERPProvider):
        """Test workflow handling when errors occur."""
        # Create an order that will cause validation issues
        invalid_order = OrderData(
            customer_info=CustomerInfo(name="Invalid Customer", customer_id="INVALID"),
            line_items=[
                OrderLineItem(
                    part_number="INVALID-PART",
                    description="Non-existent part",
                    quantity=1,
                    unit_price=0.0,
                    total_price=0.0
                )
            ],
            total_amount=0.0
        )
        
        # Customer validation should fail
        customer_result = await mock_provider.validate_customer(invalid_order.customer_info)
        assert customer_result["is_valid"] is False
        
        # Should not proceed with order creation if customer is invalid
        # This would typically be handled by the workflow logic
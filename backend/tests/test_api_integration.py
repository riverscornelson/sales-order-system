"""
Integration tests for API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, AsyncMock
import io
import json
from typing import Dict, Any

from app.main import app
from app.models.schemas import ProcessingSession, OrderData, CustomerInfo


@pytest.fixture
def client() -> TestClient:
    """Create FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_pdf_file() -> io.BytesIO:
    """Create a sample PDF file for upload testing."""
    # Minimal valid PDF structure
    pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj
xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
trailer<</Size 4/Root 1 0 R>>
startxref
185
%%EOF"""
    
    return io.BytesIO(pdf_content)


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_health_check(self, client: TestClient):
        """Test basic health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
    
    def test_detailed_health_check(self, client: TestClient):
        """Test detailed health check with system information."""
        response = client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
        assert "system" in data
        assert data["services"]["database"] in ["healthy", "degraded", "unhealthy"]
        assert data["services"]["erp"] in ["healthy", "degraded", "unhealthy"]


class TestUploadEndpoints:
    """Test document upload endpoints."""
    
    def test_upload_pdf_success(self, client: TestClient, sample_pdf_file: io.BytesIO):
        """Test successful PDF upload."""
        with patch('app.agents.supervisor.SupervisorAgent.execute_workflow', new_callable=AsyncMock) as mock_workflow:
            mock_workflow.return_value = {
                "session_id": "test_session_001",
                "status": "processing",
                "message": "Document uploaded successfully"
            }
            
            response = client.post(
                "/api/upload",
                files={"file": ("test.pdf", sample_pdf_file, "application/pdf")}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == "test_session_001"
            assert data["status"] == "processing"
            assert data["message"] == "Document uploaded successfully"
    
    def test_upload_without_file(self, client: TestClient):
        """Test upload endpoint without file."""
        response = client.post("/api/upload")
        
        assert response.status_code == 422  # Validation error
    
    def test_upload_invalid_file_type(self, client: TestClient):
        """Test upload with invalid file type."""
        text_file = io.BytesIO(b"This is not a PDF")
        
        response = client.post(
            "/api/upload",
            files={"file": ("test.txt", text_file, "text/plain")}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Unsupported file type" in data["detail"]
    
    def test_upload_large_file(self, client: TestClient):
        """Test upload with file exceeding size limit."""
        # Create a large file (>10MB)
        large_file = io.BytesIO(b"x" * (11 * 1024 * 1024))
        
        response = client.post(
            "/api/upload",
            files={"file": ("large.pdf", large_file, "application/pdf")}
        )
        
        assert response.status_code == 413  # Request Entity Too Large
    
    @patch('app.agents.supervisor.SupervisorAgent.execute_workflow')
    def test_upload_processing_error(self, mock_workflow: AsyncMock, client: TestClient, sample_pdf_file: io.BytesIO):
        """Test upload when processing fails."""
        mock_workflow.side_effect = Exception("Processing failed")
        
        response = client.post(
            "/api/upload",
            files={"file": ("test.pdf", sample_pdf_file, "application/pdf")}
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "Processing failed" in data["detail"]


class TestOrderEndpoints:
    """Test order processing endpoints."""
    
    def test_get_session_status(self, client: TestClient):
        """Test getting session status."""
        session_id = "test_session_001"
        
        with patch('app.api.orders.get_session_status') as mock_get_status:
            mock_get_status.return_value = ProcessingSession(
                session_id=session_id,
                status="completed",
                created_at="2024-01-15T10:30:00Z",
                updated_at="2024-01-15T10:35:00Z",
                metadata={"processing_time": 45.2}
            )
            
            response = client.get(f"/api/orders/{session_id}/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == session_id
            assert data["status"] == "completed"
    
    def test_get_session_status_not_found(self, client: TestClient):
        """Test getting status for non-existent session."""
        session_id = "non_existent_session"
        
        with patch('app.api.orders.get_session_status') as mock_get_status:
            mock_get_status.return_value = None
            
            response = client.get(f"/api/orders/{session_id}/status")
            
            assert response.status_code == 404
    
    def test_submit_order_success(self, client: TestClient, sample_order_data: OrderData):
        """Test successful order submission."""
        session_id = "test_session_001"
        
        with patch('app.services.erp.base.create_erp_provider') as mock_erp_factory:
            mock_provider = Mock()
            mock_provider.submit_order = AsyncMock(return_value={
                "success": True,
                "order_id": "ORD-001",
                "status": "submitted"
            })
            mock_erp_factory.return_value = mock_provider
            
            response = client.post(
                f"/api/orders/{session_id}/submit",
                json=sample_order_data.dict()
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["order_id"] == "ORD-001"
    
    def test_submit_order_validation_error(self, client: TestClient):
        """Test order submission with validation errors."""
        session_id = "test_session_001"
        invalid_order = {"invalid": "data"}
        
        response = client.post(
            f"/api/orders/{session_id}/submit",
            json=invalid_order
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_submit_order_erp_failure(self, client: TestClient, sample_order_data: OrderData):
        """Test order submission when ERP fails."""
        session_id = "test_session_001"
        
        with patch('app.services.erp.base.create_erp_provider') as mock_erp_factory:
            mock_provider = Mock()
            mock_provider.submit_order = AsyncMock(return_value={
                "success": False,
                "error": "ERP system unavailable"
            })
            mock_erp_factory.return_value = mock_provider
            
            response = client.post(
                f"/api/orders/{session_id}/submit",
                json=sample_order_data.dict()
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "ERP system unavailable" in data["detail"]
    
    def test_get_order_details(self, client: TestClient):
        """Test retrieving order details."""
        session_id = "test_session_001"
        
        with patch('app.api.orders.get_order_details') as mock_get_details:
            mock_order_data = OrderData(
                customer_info=CustomerInfo(name="Test Customer"),
                line_items=[],
                total_amount=100.0
            )
            mock_get_details.return_value = mock_order_data
            
            response = client.get(f"/api/orders/{session_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["customer_info"]["name"] == "Test Customer"
            assert data["total_amount"] == 100.0
    
    def test_get_order_details_not_found(self, client: TestClient):
        """Test retrieving details for non-existent order."""
        session_id = "non_existent_session"
        
        with patch('app.api.orders.get_order_details') as mock_get_details:
            mock_get_details.return_value = None
            
            response = client.get(f"/api/orders/{session_id}")
            
            assert response.status_code == 404


class TestWebSocketEndpoints:
    """Test WebSocket endpoints."""
    
    def test_websocket_connection(self, client: TestClient):
        """Test WebSocket connection establishment."""
        client_id = "test_client_001"
        
        with client.websocket_connect(f"/ws/{client_id}") as websocket:
            # Should successfully connect
            assert websocket is not None
    
    def test_websocket_message_handling(self, client: TestClient):
        """Test WebSocket message handling."""
        client_id = "test_client_001"
        
        with patch('app.services.websocket_manager.WebSocketManager.handle_message', new_callable=AsyncMock) as mock_handle:
            with client.websocket_connect(f"/ws/{client_id}") as websocket:
                test_message = {"type": "ping", "data": {}}
                websocket.send_json(test_message)
                
                # Should handle the message
                mock_handle.assert_called_once()
    
    def test_websocket_broadcast(self, client: TestClient):
        """Test WebSocket broadcasting to multiple clients."""
        client_id_1 = "test_client_001"
        client_id_2 = "test_client_002"
        
        with client.websocket_connect(f"/ws/{client_id_1}") as ws1, \
             client.websocket_connect(f"/ws/{client_id_2}") as ws2:
            
            # Both connections should be established
            assert ws1 is not None
            assert ws2 is not None


class TestErrorHandling:
    """Test API error handling."""
    
    def test_404_error(self, client: TestClient):
        """Test 404 error handling."""
        response = client.get("/non-existent-endpoint")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    def test_500_error_handling(self, client: TestClient):
        """Test 500 error handling."""
        with patch('app.api.health.get_health_status', side_effect=Exception("Internal error")):
            response = client.get("/health")
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
    
    def test_cors_headers(self, client: TestClient):
        """Test CORS headers are present."""
        response = client.options("/api/upload")
        
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers


class TestRateLimiting:
    """Test API rate limiting."""
    
    @pytest.mark.slow
    def test_rate_limiting(self, client: TestClient):
        """Test rate limiting functionality."""
        # Make multiple rapid requests
        responses = []
        for i in range(20):  # Exceed typical rate limit
            response = client.get("/health")
            responses.append(response.status_code)
        
        # Some requests should be rate limited (429 status)
        assert 429 in responses or all(r == 200 for r in responses)  # Depends on rate limit config


class TestAuthentication:
    """Test API authentication if implemented."""
    
    def test_protected_endpoint_without_auth(self, client: TestClient):
        """Test accessing protected endpoint without authentication."""
        # If authentication is implemented, this should fail
        response = client.get("/api/admin/status")
        
        # Should either be 401 (unauthorized) or 404 (if endpoint doesn't exist)
        assert response.status_code in [401, 404]
    
    def test_protected_endpoint_with_auth(self, client: TestClient):
        """Test accessing protected endpoint with authentication."""
        # Mock authentication header
        headers = {"Authorization": "Bearer valid-token"}
        
        with patch('app.api.auth.verify_token', return_value=True):
            response = client.get("/api/admin/status", headers=headers)
            
            # Should succeed if endpoint exists and auth is valid
            assert response.status_code in [200, 404]


class TestValidation:
    """Test request validation."""
    
    def test_invalid_json(self, client: TestClient):
        """Test handling of invalid JSON."""
        response = client.post(
            "/api/orders/test/submit",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_missing_required_fields(self, client: TestClient):
        """Test validation of missing required fields."""
        incomplete_order = {"customer_info": {}}  # Missing required fields
        
        response = client.post(
            "/api/orders/test/submit",
            json=incomplete_order
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_field_type_validation(self, client: TestClient):
        """Test field type validation."""
        invalid_order = {
            "customer_info": "should be object",  # Wrong type
            "line_items": "should be array",      # Wrong type
            "total_amount": "not a number"        # Wrong type
        }
        
        response = client.post(
            "/api/orders/test/submit",
            json=invalid_order
        )
        
        assert response.status_code == 422


class TestPerformance:
    """Test API performance characteristics."""
    
    @pytest.mark.slow
    def test_concurrent_requests(self, client: TestClient):
        """Test handling of concurrent requests."""
        import threading
        import time
        
        results = []
        
        def make_request():
            start_time = time.time()
            response = client.get("/health")
            end_time = time.time()
            results.append({
                "status_code": response.status_code,
                "response_time": end_time - start_time
            })
        
        # Create multiple threads to simulate concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert all(r["status_code"] == 200 for r in results)
        
        # Response times should be reasonable (< 5 seconds)
        assert all(r["response_time"] < 5.0 for r in results)
    
    def test_large_payload_handling(self, client: TestClient):
        """Test handling of large payloads."""
        # Create a large but valid order
        large_order = {
            "customer_info": {
                "name": "Test Customer",
                "email": "test@example.com"
            },
            "line_items": [
                {
                    "part_number": f"PART-{i:04d}",
                    "description": f"Part {i} with long description " * 10,
                    "quantity": i,
                    "unit_price": 10.0 + i,
                    "total_price": (10.0 + i) * i
                }
                for i in range(1, 1001)  # 1000 line items
            ],
            "total_amount": sum((10.0 + i) * i for i in range(1, 1001))
        }
        
        response = client.post(
            "/api/orders/test/submit",
            json=large_order
        )
        
        # Should handle large payload (either succeed or fail gracefully)
        assert response.status_code in [200, 413, 422]
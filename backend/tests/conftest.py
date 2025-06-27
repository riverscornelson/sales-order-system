"""
Test configuration and fixtures for the Sales Order Entry System tests.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from typing import Generator, Dict, Any
import tempfile
import os
from pathlib import Path

from app.models.schemas import (
    CustomerInfo, OrderLineItem, OrderData, ProcessingSession,
    DocumentInfo, PartMatch
)
from app.services.erp.mock_provider import MockERPProvider
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStore


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_customer_info() -> CustomerInfo:
    """Sample customer information for testing."""
    return CustomerInfo(
        name="John Smith",
        email="john.smith@acmecorp.com", 
        company="ACME Corporation",
        customer_id="CUST001",
        phone="555-123-4567",
        address="123 Main St, Anytown, ST 12345"
    )


@pytest.fixture
def sample_line_items() -> list[OrderLineItem]:
    """Sample order line items for testing."""
    return [
        OrderLineItem(
            part_number="ST-001",
            description="Stainless Steel Rod 1/4 inch x 12 feet",
            quantity=10,
            unit_price=25.50,
            total_price=255.00,
            matched_part_id="part_001",
            confidence_score=0.95,
            alternatives=[
                PartMatch(
                    part_id="part_002",
                    part_number="ST-001A",
                    description="Stainless Steel Rod 1/4 inch x 12 feet (Grade 316)",
                    confidence_score=0.85,
                    unit_price=28.00,
                    availability=50,
                    specifications={"grade": "316", "length": "12ft"}
                )
            ]
        ),
        OrderLineItem(
            part_number="AL-505", 
            description="Aluminum Sheet 4x8 feet 1/8 inch thick",
            quantity=5,
            unit_price=89.99,
            total_price=449.95,
            matched_part_id="part_003",
            confidence_score=0.92,
            alternatives=[]
        )
    ]


@pytest.fixture
def sample_order_data(sample_customer_info: CustomerInfo, sample_line_items: list[OrderLineItem]) -> OrderData:
    """Sample complete order data for testing."""
    return OrderData(
        customer_info=sample_customer_info,
        line_items=sample_line_items,
        order_date="2024-01-15",
        delivery_date="2024-01-25", 
        special_instructions="Please deliver to loading dock",
        total_amount=704.95
    )


@pytest.fixture
def sample_document_info() -> DocumentInfo:
    """Sample document information for testing."""
    return DocumentInfo(
        filename="purchase_order_001.pdf",
        file_size=245760,
        mime_type="application/pdf",
        upload_timestamp="2024-01-15T10:30:00Z"
    )


@pytest.fixture
def sample_processing_session(sample_document_info: DocumentInfo, sample_order_data: OrderData) -> ProcessingSession:
    """Sample processing session for testing."""
    return ProcessingSession(
        session_id="session_001",
        document_info=sample_document_info,
        order_data=sample_order_data,
        status="completed",
        created_at="2024-01-15T10:30:00Z",
        updated_at="2024-01-15T10:35:00Z",
        metadata={
            "processing_time": 45.2,
            "confidence_scores": {
                "extraction": 0.94,
                "matching": 0.89,
                "validation": 0.96
            }
        }
    )


@pytest.fixture
def mock_erp_provider() -> MockERPProvider:
    """Mock ERP provider for testing."""
    return MockERPProvider()


@pytest.fixture
def mock_embedding_service() -> Mock:
    """Mock embedding service for testing."""
    mock = Mock(spec=EmbeddingService)
    mock.get_embedding = AsyncMock(return_value=[0.1] * 3072)
    mock.get_part_embedding = AsyncMock(return_value=[0.2] * 3072)
    mock.dimensions = 3072
    return mock


@pytest.fixture
def mock_vector_store() -> Mock:
    """Mock vector store for testing."""
    mock = Mock(spec=VectorStore)
    mock.search_similar_parts = AsyncMock(return_value=[
        PartMatch(
            part_id="part_001",
            part_number="ST-001",
            description="Stainless Steel Rod 1/4 inch x 12 feet",
            confidence_score=0.95,
            unit_price=25.50,
            availability=100,
            specifications={"material": "stainless_steel", "diameter": "0.25in"}
        )
    ])
    mock.add_part = AsyncMock()
    mock.update_part = AsyncMock()
    return mock


@pytest.fixture
def mock_websocket_manager() -> Mock:
    """Mock WebSocket manager for testing."""
    mock = Mock()
    mock.send_card_update = AsyncMock()
    mock.send_status_update = AsyncMock()
    mock.connect_client = AsyncMock()
    mock.disconnect_client = AsyncMock()
    return mock


@pytest.fixture
def sample_pdf_content() -> bytes:
    """Sample PDF content for testing document parsing."""
    # This is a minimal valid PDF structure for testing
    return b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Sample PDF Content) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000204 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
297
%%EOF"""


@pytest.fixture
def sample_extracted_text() -> str:
    """Sample extracted text from a purchase order."""
    return """
PURCHASE ORDER

ACME Corporation
123 Main Street
Anytown, ST 12345

To: Metal Supply Co.
    456 Industrial Blvd
    Manufacturing City, ST 67890

PO Number: PO-2024-001
Date: January 15, 2024
Delivery Date: January 25, 2024

ITEM DESCRIPTION                    QTY    UNIT PRICE    TOTAL
1. Stainless Steel Rod 1/4" x 12'   10     $25.50      $255.00
2. Aluminum Sheet 4x8' 1/8" thick    5     $89.99      $449.95

                                           TOTAL: $704.95

Special Instructions: Please deliver to loading dock

Contact: John Smith
Email: john.smith@acmecorp.com
Phone: 555-123-4567
"""


@pytest.fixture
def environment_vars() -> Dict[str, str]:
    """Environment variables for testing."""
    return {
        "ENVIRONMENT": "test",
        "LOG_LEVEL": "DEBUG",
        "ERP_PROVIDER": "mock",
        "ERP_MOCK_DELAY": "0.1",
        "EMBEDDING_PROVIDER": "openai",
        "OPENAI_API_KEY": "test-key",
        "GOOGLE_CLOUD_PROJECT": "test-project",
        "DATABASE_URL": "sqlite:///:memory:",
        "REDIS_URL": "redis://localhost:6379/0"
    }


@pytest.fixture(autouse=True)
def set_test_env(environment_vars: Dict[str, str]) -> Generator[None, None, None]:
    """Set environment variables for tests."""
    original_env = {}
    for key, value in environment_vars.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield
    
    # Restore original environment
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


class AsyncContextManager:
    """Helper class for testing async context managers."""
    
    def __init__(self, return_value=None):
        self.return_value = return_value
    
    async def __aenter__(self):
        return self.return_value
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def async_context_manager():
    """Factory for creating async context managers in tests."""
    return AsyncContextManager
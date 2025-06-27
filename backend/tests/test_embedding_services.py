"""
Unit tests for embedding and vector services.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import numpy as np
from typing import List

from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStore
from app.services.parts_catalog import PartsCatalogService
from app.models.schemas import PartMatch, OrderLineItem


class TestEmbeddingService:
    """Test cases for the Embedding Service."""
    
    @pytest.fixture
    def embedding_service(self) -> EmbeddingService:
        """Create an embedding service instance."""
        with patch.dict('os.environ', {
            'EMBEDDING_PROVIDER': 'openai',
            'OPENAI_API_KEY': 'test-key'
        }):
            return EmbeddingService()
    
    @pytest.mark.asyncio
    async def test_get_embedding_openai(self, embedding_service: EmbeddingService):
        """Test getting embeddings from OpenAI."""
        mock_embedding = [0.1] * 3072
        
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.data = [Mock(embedding=mock_embedding)]
            mock_client.embeddings.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client
            
            # Recreate service to use mocked client
            embedding_service = EmbeddingService()
            result = await embedding_service.get_embedding("test text")
            
            assert len(result) == 3072
            assert result == mock_embedding
            mock_client.embeddings.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_part_embedding(self, embedding_service: EmbeddingService):
        """Test getting specialized part embeddings."""
        mock_embedding = [0.2] * 3072
        
        with patch.object(embedding_service, 'get_embedding', new_callable=AsyncMock) as mock_get_embedding:
            mock_get_embedding.return_value = mock_embedding
            
            line_item = OrderLineItem(
                part_number="ST-001",
                description="Stainless Steel Rod 1/4 inch x 12 feet",
                quantity=10,
                unit_price=25.50,
                total_price=255.00
            )
            
            result = await embedding_service.get_part_embedding(line_item)
            
            assert len(result) == 3072
            assert result == mock_embedding
            # Should have been called with formatted part description
            mock_get_embedding.assert_called_once()
            call_args = mock_get_embedding.call_args[0][0]
            assert "ST-001" in call_args
            assert "Stainless Steel Rod" in call_args
    
    @pytest.mark.asyncio
    async def test_batch_get_embeddings(self, embedding_service: EmbeddingService):
        """Test batch embedding generation."""
        texts = ["text 1", "text 2", "text 3"]
        mock_embeddings = [[0.1] * 3072, [0.2] * 3072, [0.3] * 3072]
        
        with patch.object(embedding_service, 'get_embedding', new_callable=AsyncMock) as mock_get_embedding:
            mock_get_embedding.side_effect = mock_embeddings
            
            results = await embedding_service.batch_get_embeddings(texts)
            
            assert len(results) == 3
            assert results == mock_embeddings
            assert mock_get_embedding.call_count == 3
    
    @pytest.mark.asyncio
    async def test_embedding_error_handling(self, embedding_service: EmbeddingService):
        """Test error handling in embedding generation."""
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.embeddings.create = AsyncMock(side_effect=Exception("API Error"))
            mock_openai.return_value = mock_client
            
            embedding_service = EmbeddingService()
            
            with pytest.raises(Exception, match="API Error"):
                await embedding_service.get_embedding("test text")
    
    def test_normalize_part_description(self, embedding_service: EmbeddingService):
        """Test part description normalization."""
        line_item = OrderLineItem(
            part_number="ST-001",
            description="Stainless Steel Rod 1/4\" x 12'",
            quantity=10,
            unit_price=25.50,
            total_price=255.00
        )
        
        normalized = embedding_service._normalize_part_description(line_item)
        
        assert "ST-001" in normalized
        assert "stainless steel rod" in normalized.lower()
        assert "0.25" in normalized or "1/4" in normalized
        assert "12" in normalized
    
    @pytest.mark.asyncio
    async def test_vertex_ai_embedding(self):
        """Test Vertex AI embedding provider."""
        with patch.dict('os.environ', {
            'EMBEDDING_PROVIDER': 'vertex_ai',
            'GOOGLE_CLOUD_PROJECT': 'test-project'
        }):
            with patch('vertexai.init'), \
                 patch('vertexai.language_models.TextEmbeddingModel.from_pretrained') as mock_model:
                
                mock_instance = Mock()
                mock_instance.get_embeddings = Mock(return_value=[Mock(values=[0.1] * 768)])
                mock_model.return_value = mock_instance
                
                service = EmbeddingService()
                result = await service.get_embedding("test text")
                
                assert len(result) == 768  # Vertex AI typically returns 768-dim embeddings
                mock_instance.get_embeddings.assert_called_once()


class TestVectorStore:
    """Test cases for the Vector Store."""
    
    @pytest.fixture
    def vector_store(self, temp_dir) -> VectorStore:
        """Create a vector store instance."""
        return VectorStore(storage_path=str(temp_dir / "test_vectors"))
    
    @pytest.fixture
    def sample_parts_data(self) -> List[dict]:
        """Sample parts data for testing."""
        return [
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
            }
        ]
    
    @pytest.mark.asyncio
    async def test_add_part(self, vector_store: VectorStore, sample_parts_data: List[dict]):
        """Test adding a part to the vector store."""
        part_data = sample_parts_data[0]
        embedding = [0.1] * 3072
        
        await vector_store.add_part(
            part_id=part_data["part_id"],
            embedding=embedding,
            metadata=part_data
        )
        
        # Verify part was added
        assert len(vector_store._vectors) == 1
        assert part_data["part_id"] in vector_store._metadata
    
    @pytest.mark.asyncio
    async def test_search_similar_parts(self, vector_store: VectorStore, sample_parts_data: List[dict]):
        """Test searching for similar parts."""
        # Add sample parts
        for i, part_data in enumerate(sample_parts_data):
            embedding = [0.1 + i * 0.1] * 3072  # Slightly different embeddings
            await vector_store.add_part(
                part_id=part_data["part_id"],
                embedding=embedding,
                metadata=part_data
            )
        
        # Search with query embedding
        query_embedding = [0.1] * 3072  # Should be closest to first part
        results = await vector_store.search_similar_parts(
            query_embedding=query_embedding,
            top_k=2,
            min_confidence=0.0
        )
        
        assert len(results) <= 2
        assert all(isinstance(result, PartMatch) for result in results)
        # First result should be most similar (highest confidence)
        if len(results) > 1:
            assert results[0].confidence_score >= results[1].confidence_score
    
    @pytest.mark.asyncio
    async def test_update_part(self, vector_store: VectorStore, sample_parts_data: List[dict]):
        """Test updating an existing part."""
        part_data = sample_parts_data[0]
        original_embedding = [0.1] * 3072
        
        # Add initial part
        await vector_store.add_part(
            part_id=part_data["part_id"],
            embedding=original_embedding,
            metadata=part_data
        )
        
        # Update part
        updated_data = part_data.copy()
        updated_data["unit_price"] = 30.00
        updated_embedding = [0.2] * 3072
        
        await vector_store.update_part(
            part_id=part_data["part_id"],
            embedding=updated_embedding,
            metadata=updated_data
        )
        
        # Verify update
        stored_metadata = vector_store._metadata[part_data["part_id"]]
        assert stored_metadata["unit_price"] == 30.00
    
    @pytest.mark.asyncio
    async def test_confidence_threshold_filtering(self, vector_store: VectorStore, sample_parts_data: List[dict]):
        """Test filtering results by confidence threshold."""
        # Add parts with very different embeddings
        part1_embedding = [1.0] + [0.0] * 3071
        part2_embedding = [0.0] * 3071 + [1.0]
        
        await vector_store.add_part("part1", part1_embedding, sample_parts_data[0])
        await vector_store.add_part("part2", part2_embedding, sample_parts_data[1])
        
        # Search with high confidence threshold
        query_embedding = [1.0] + [0.0] * 3071  # Should match part1 closely
        results = await vector_store.search_similar_parts(
            query_embedding=query_embedding,
            top_k=2,
            min_confidence=0.8
        )
        
        # Should only return high-confidence matches
        assert all(result.confidence_score >= 0.8 for result in results)
    
    @pytest.mark.asyncio
    async def test_empty_search(self, vector_store: VectorStore):
        """Test searching in empty vector store."""
        query_embedding = [0.1] * 3072
        results = await vector_store.search_similar_parts(query_embedding)
        
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_persistence(self, vector_store: VectorStore, sample_parts_data: List[dict]):
        """Test vector store persistence."""
        part_data = sample_parts_data[0]
        embedding = [0.1] * 3072
        
        # Add part and save
        await vector_store.add_part(
            part_id=part_data["part_id"],
            embedding=embedding,
            metadata=part_data
        )
        await vector_store.save_to_disk()
        
        # Create new vector store instance and load
        new_vector_store = VectorStore(storage_path=vector_store.storage_path)
        await new_vector_store.load_from_disk()
        
        # Verify data was persisted
        assert len(new_vector_store._vectors) == 1
        assert part_data["part_id"] in new_vector_store._metadata


class TestPartsCatalogService:
    """Test cases for the Parts Catalog Service."""
    
    @pytest.fixture
    def catalog_service(self, mock_embedding_service: Mock, mock_vector_store: Mock) -> PartsCatalogService:
        """Create a parts catalog service instance."""
        return PartsCatalogService(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store
        )
    
    @pytest.mark.asyncio
    async def test_find_matching_parts(self, catalog_service: PartsCatalogService, mock_embedding_service: Mock, mock_vector_store: Mock):
        """Test finding matching parts for a line item."""
        line_item = OrderLineItem(
            part_number="ST-001",
            description="Stainless Steel Rod 1/4 inch x 12 feet",
            quantity=10,
            unit_price=25.50,
            total_price=255.00
        )
        
        # Mock the search results
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
        mock_embedding_service.get_part_embedding.return_value = [0.1] * 3072
        
        results = await catalog_service.find_matching_parts(line_item)
        
        assert len(results) == 1
        assert results[0].confidence_score == 0.95
        mock_embedding_service.get_part_embedding.assert_called_once_with(line_item)
        mock_vector_store.search_similar_parts.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_part_to_catalog(self, catalog_service: PartsCatalogService, mock_embedding_service: Mock, mock_vector_store: Mock):
        """Test adding a part to the catalog."""
        part_data = {
            "part_id": "part_001",
            "part_number": "ST-001", 
            "description": "Stainless Steel Rod 1/4 inch x 12 feet",
            "unit_price": 25.50,
            "availability": 100,
            "specifications": {"material": "stainless_steel"}
        }
        
        mock_embedding_service.get_embedding.return_value = [0.1] * 3072
        
        await catalog_service.add_part_to_catalog(part_data)
        
        mock_embedding_service.get_embedding.assert_called_once()
        mock_vector_store.add_part.assert_called_once_with(
            part_id=part_data["part_id"],
            embedding=[0.1] * 3072,
            metadata=part_data
        )
    
    @pytest.mark.asyncio
    async def test_batch_process_parts(self, catalog_service: PartsCatalogService, mock_embedding_service: Mock, mock_vector_store: Mock):
        """Test batch processing multiple parts."""
        parts_data = [
            {"part_id": "part_001", "description": "Part 1"},
            {"part_id": "part_002", "description": "Part 2"}
        ]
        
        mock_embedding_service.batch_get_embeddings.return_value = [
            [0.1] * 3072,
            [0.2] * 3072
        ]
        
        await catalog_service.batch_process_parts(parts_data)
        
        mock_embedding_service.batch_get_embeddings.assert_called_once()
        assert mock_vector_store.add_part.call_count == 2
    
    @pytest.mark.asyncio
    async def test_semantic_search_with_filters(self, catalog_service: PartsCatalogService, mock_vector_store: Mock):
        """Test semantic search with filters."""
        query = "stainless steel rod"
        filters = {"material": "stainless_steel", "min_price": 20.0}
        
        # Mock filtered results
        mock_matches = [
            PartMatch(
                part_id="part_001",
                part_number="ST-001",
                description="Stainless Steel Rod",
                confidence_score=0.95,
                unit_price=25.50,
                availability=100,
                specifications={"material": "stainless_steel"}
            )
        ]
        mock_vector_store.search_similar_parts.return_value = mock_matches
        
        results = await catalog_service.semantic_search(query, filters=filters)
        
        assert len(results) == 1
        assert results[0].specifications["material"] == "stainless_steel"
        assert results[0].unit_price >= 20.0
    
    @pytest.mark.asyncio
    async def test_fuzzy_matching_fallback(self, catalog_service: PartsCatalogService, mock_vector_store: Mock):
        """Test fuzzy matching fallback when semantic search returns no results."""
        line_item = OrderLineItem(
            part_number="ST-001-TYPO",  # Typo in part number
            description="Stainless Steel Rod",
            quantity=1,
            unit_price=25.50,
            total_price=25.50
        )
        
        # Mock no semantic results but fuzzy match available
        mock_vector_store.search_similar_parts.return_value = []
        
        with patch.object(catalog_service, '_fuzzy_search') as mock_fuzzy:
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
            
            results = await catalog_service.find_matching_parts(line_item, use_fuzzy_fallback=True)
            
            assert len(results) == 1
            assert results[0].part_number == "ST-001"
            mock_fuzzy.assert_called_once()
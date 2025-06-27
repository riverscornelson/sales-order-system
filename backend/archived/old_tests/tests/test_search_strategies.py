import pytest
from unittest.mock import Mock, AsyncMock
from app.agents.search_strategies.part_number import PartNumberStrategy
from app.agents.search_strategies.description import FullDescriptionStrategy
from app.agents.search_strategies.key_terms import KeyTermsStrategy
from app.agents.match_processor import MatchProcessor


class TestPartNumberStrategy:
    @pytest.mark.asyncio
    async def test_exact_part_number_match(self):
        # Arrange
        mock_catalog = Mock()
        mock_catalog.search_parts = AsyncMock(return_value=[
            {"part": {"id": "1", "part_number": "ABC123"}, "scores": {"combined_score": 0.95}}
        ])
        
        strategy = PartNumberStrategy(mock_catalog)
        
        # Act
        results = await strategy.execute("ABC123")
        
        # Assert
        assert len(results) == 1
        assert results[0]["part"]["part_number"] == "ABC123"
        mock_catalog.search_parts.assert_called_once_with(
            "ABC123", None, top_k=10, search_type="part_number"
        )
    
    @pytest.mark.asyncio
    async def test_partial_part_number_fallback(self):
        # Arrange
        mock_catalog = Mock()
        mock_catalog.search_parts = AsyncMock(side_effect=[
            [],  # No exact match
            [{"part": {"id": "2", "part_number": "ABC123-456"}, "scores": {"combined_score": 0.8}}]
        ])
        
        strategy = PartNumberStrategy(mock_catalog)
        
        # Act
        results = await strategy.execute("ABC123")
        
        # Assert
        assert len(results) == 1
        assert mock_catalog.search_parts.call_count == 2


class TestKeyTermsStrategy:
    def test_extract_key_terms(self):
        strategy = KeyTermsStrategy(Mock())
        
        # Test basic extraction
        terms = strategy._extract_key_terms("stainless steel hex bolt with washer")
        assert "stainless" in terms
        assert "steel" in terms
        assert "hex" in terms
        assert "bolt" in terms
        assert "washer" in terms
        assert "with" not in terms  # Stop word
        
        # Test compound terms
        terms = strategy._extract_key_terms("heavy-duty motor mount")
        assert "heavy-duty" in terms
        assert "motor" in terms
        assert "mount" in terms


class TestMatchProcessor:
    def test_deduplicate_matches(self):
        processor = MatchProcessor()
        
        matches = [
            {"part": {"id": "1"}, "scores": {"strategy_weighted_score": 0.8}},
            {"part": {"id": "2"}, "scores": {"strategy_weighted_score": 0.7}},
            {"part": {"id": "1"}, "scores": {"strategy_weighted_score": 0.9}},  # Duplicate with higher score
        ]
        
        deduped = processor.deduplicate_matches(matches)
        
        assert len(deduped) == 2
        # Should keep the higher scoring duplicate
        part1_match = next(m for m in deduped if m["part"]["id"] == "1")
        assert part1_match["scores"]["strategy_weighted_score"] == 0.9
    
    def test_generate_match_explanation(self):
        processor = MatchProcessor()
        
        item = {"description": "steel bolt", "material": "steel"}
        match = {
            "part": {"id": "1", "material": "stainless steel"},
            "scores": {"combined_score": 0.85, "dimension_match": True},
            "search_strategy": "FullDescriptionStrategy"
        }
        
        explanation = processor.generate_match_explanation(item, match)
        
        assert "Matched by description" in explanation
        assert "High confidence match" in explanation
        assert "Material matches request" in explanation
        assert "Dimensions match specifications" in explanation
    
    def test_calculate_match_quality(self):
        processor = MatchProcessor()
        
        # Test excellent quality
        matches = [
            {"scores": {"strategy_weighted_score": 0.9}},
            {"scores": {"strategy_weighted_score": 0.85}}
        ]
        quality = processor.calculate_match_quality(matches)
        assert quality["match_quality"] == "excellent"
        assert quality["best_confidence"] == 0.9
        
        # Test no matches
        quality = processor.calculate_match_quality([])
        assert quality["match_quality"] == "no_match"
        assert quality["average_confidence"] == 0
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import structlog

logger = structlog.get_logger()


class SearchStrategy(ABC):
    """Base class for all search strategies"""
    
    def __init__(self, weight: float = 1.0):
        self.weight = weight
        self.strategy_type = self.__class__.__name__
    
    @abstractmethod
    async def execute(self, query: str, filters: Optional[Dict] = None, top_k: int = 10) -> List[Dict[str, Any]]:
        """Execute the search strategy and return matches"""
        pass
    
    def apply_weight(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply strategy weight to match scores"""
        for match in matches:
            if "scores" not in match:
                match["scores"] = {}
            
            original_score = match["scores"].get("combined_score", 0)
            match["scores"]["strategy_weighted_score"] = original_score * self.weight
            match["search_strategy"] = self.strategy_type
            
        return matches


class SearchContext:
    """Context for executing search strategies"""
    
    def __init__(self, parts_catalog, embedding_service):
        self.parts_catalog = parts_catalog
        self.embedding_service = embedding_service
        self.min_confidence_threshold = 0.5
    
    async def execute_strategy(self, strategy: SearchStrategy, query: str, 
                             filters: Optional[Dict] = None, top_k: int = 10) -> List[Dict[str, Any]]:
        """Execute a strategy with context"""
        try:
            matches = await strategy.execute(query, filters, top_k)
            weighted_matches = strategy.apply_weight(matches)
            
            # Filter by minimum confidence
            return [
                m for m in weighted_matches 
                if m.get("scores", {}).get("combined_score", 0) >= self.min_confidence_threshold
            ]
        except Exception as e:
            logger.debug(f"Strategy {strategy.strategy_type} failed", 
                        query=query[:50], error=str(e))
            return []
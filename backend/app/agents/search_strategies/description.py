from typing import Dict, Any, List, Optional
from .base import SearchStrategy


class FullDescriptionStrategy(SearchStrategy):
    """Strategy for searching by full description"""
    
    def __init__(self, parts_catalog):
        super().__init__(weight=0.9)
        self.parts_catalog = parts_catalog
    
    async def execute(self, query: str, filters: Optional[Dict] = None, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search using the full description"""
        if not query:
            return []
        
        return await self.parts_catalog.search_parts(
            query,
            filters,
            top_k=top_k
        )


class NormalizedDescriptionStrategy(SearchStrategy):
    """Strategy for searching with normalized descriptions"""
    
    def __init__(self, parts_catalog, embedding_service):
        super().__init__(weight=0.8)
        self.parts_catalog = parts_catalog
        self.embedding_service = embedding_service
    
    async def execute(self, query: str, filters: Optional[Dict] = None, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search using normalized description"""
        if not query:
            return []
        
        normalized = self.embedding_service.normalize_part_description(query)
        if normalized == query:  # Skip if no normalization occurred
            return []
        
        return await self.parts_catalog.search_parts(
            normalized,
            filters,
            top_k=top_k
        )
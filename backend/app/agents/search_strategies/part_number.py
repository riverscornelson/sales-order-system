from typing import Dict, Any, List, Optional
from .base import SearchStrategy


class PartNumberStrategy(SearchStrategy):
    """Strategy for direct part number searches"""
    
    def __init__(self, parts_catalog):
        super().__init__(weight=1.0)  # Highest weight for exact part numbers
        self.parts_catalog = parts_catalog
    
    async def execute(self, query: str, filters: Optional[Dict] = None, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search by exact or partial part number match"""
        if not query:
            return []
        
        # Clean part number
        cleaned_query = query.strip().upper()
        
        # Try exact match first
        results = await self.parts_catalog.search_parts(
            cleaned_query,
            filters,
            top_k=top_k,
            search_type="part_number"
        )
        
        # If no results, try partial match
        if not results and len(cleaned_query) > 3:
            results = await self.parts_catalog.search_parts(
                cleaned_query,
                filters,
                top_k=top_k,
                search_type="part_number_partial"
            )
        
        return results
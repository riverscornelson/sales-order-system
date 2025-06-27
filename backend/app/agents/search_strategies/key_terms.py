from typing import Dict, Any, List, Optional
import re
from .base import SearchStrategy


class KeyTermsStrategy(SearchStrategy):
    """Strategy for searching by extracted key terms"""
    
    def __init__(self, parts_catalog):
        super().__init__(weight=0.7)
        self.parts_catalog = parts_catalog
        self.stop_words = {'the', 'and', 'or', 'with', 'for', 'of', 'in', 'on', 'at', 'to', 'a', 'an'}
    
    async def execute(self, query: str, filters: Optional[Dict] = None, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search using extracted key terms"""
        if not query:
            return []
        
        key_terms = self._extract_key_terms(query)
        if not key_terms:
            return []
        
        search_query = " ".join(key_terms)
        return await self.parts_catalog.search_parts(
            search_query,
            filters,
            top_k=top_k,
            search_type="key_terms"
        )
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from text"""
        # Clean and split text
        text = re.sub(r'[^\w\s-]', ' ', text.lower())
        words = text.split()
        
        # Filter out stop words and short words
        key_terms = [
            word for word in words 
            if len(word) > 2 and word not in self.stop_words
        ]
        
        # Look for compound terms (e.g., "stainless-steel")
        compound_terms = re.findall(r'\b\w+-\w+\b', text.lower())
        key_terms.extend(compound_terms)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_terms = []
        for term in key_terms:
            if term not in seen:
                seen.add(term)
                unique_terms.append(term)
        
        return unique_terms[:10]  # Limit to top 10 terms
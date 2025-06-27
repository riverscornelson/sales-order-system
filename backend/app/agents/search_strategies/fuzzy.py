from typing import Dict, Any, List, Optional
from .base import SearchStrategy


class FuzzyMatchStrategy(SearchStrategy):
    """Strategy for fuzzy matching when other strategies fail"""
    
    def __init__(self, parts_catalog):
        super().__init__(weight=0.4)  # Lower weight for fuzzy matches
        self.parts_catalog = parts_catalog
        self.stop_words = {'the', 'and', 'or', 'with', 'for', 'of', 'in', 'on', 'at', 'to', 'a', 'an'}
    
    async def execute(self, query: str, filters: Optional[Dict] = None, top_k: int = 10) -> List[Dict[str, Any]]:
        """Perform fuzzy matching for difficult cases"""
        if not query:
            return []
        
        # Extract individual words
        words = query.lower().split()
        important_words = [
            word for word in words 
            if len(word) > 2 and word not in self.stop_words
        ]
        
        if not important_words:
            return []
        
        all_matches = []
        
        # Search for combinations of important words
        for i in range(len(important_words)):
            for j in range(i + 1, min(i + 3, len(important_words) + 1)):
                phrase = " ".join(important_words[i:j])
                
                matches = await self.parts_catalog.search_parts(
                    phrase,
                    filters,
                    top_k=3,
                    search_type="fuzzy"
                )
                
                # Mark as fuzzy matches
                for match in matches:
                    if "scores" not in match:
                        match["scores"] = {}
                    match["scores"]["fuzzy_match"] = True
                    match["scores"]["combined_score"] *= 0.8  # Reduce confidence
                
                all_matches.extend(matches)
        
        # Deduplicate by part ID
        seen_ids = set()
        unique_matches = []
        for match in all_matches:
            part_id = match.get("part", {}).get("id")
            if part_id and part_id not in seen_ids:
                seen_ids.add(part_id)
                unique_matches.append(match)
        
        # Sort by score and return top results
        unique_matches.sort(
            key=lambda x: x.get("scores", {}).get("combined_score", 0),
            reverse=True
        )
        
        return unique_matches[:top_k]
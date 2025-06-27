from typing import Dict, Any, List, Optional
import asyncio
import structlog
import re

from ..services.parts_catalog import PartsCatalogService
from ..services.embeddings import PartEmbeddingService

logger = structlog.get_logger()

class SemanticSearchAgent:
    """Agent responsible for finding part matches using semantic search"""
    
    def __init__(self):
        self.parts_catalog = PartsCatalogService()
        self.embedding_service = PartEmbeddingService()
        
        # Configuration
        self.max_matches_per_item = 5
        self.min_confidence_threshold = 0.5
        self.fuzzy_match_threshold = 0.4
    
    async def find_part_matches(self, line_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find part matches for extracted line items"""
        
        logger.info("Starting semantic search for parts", 
                   line_items_count=len(line_items))
        
        try:
            # Initialize catalog if needed
            await self.parts_catalog.initialize_catalog()
            
            matches = {}
            match_stats = {
                "total_items": len(line_items),
                "matched_items": 0,
                "high_confidence_matches": 0,
                "partial_matches": 0,
                "no_matches": 0
            }
            
            # Process each line item
            for i, item in enumerate(line_items):
                item_id = f"item_{i}"
                
                logger.debug("Processing line item", 
                           item_id=item_id,
                           description=item.get("description", "")[:100])
                
                # Find matches for this item
                item_matches = await self._find_matches_for_item(item)
                
                if item_matches:
                    matches[item_id] = item_matches
                    
                    # Update statistics
                    best_match = item_matches[0] if item_matches else {}
                    best_score = best_match.get("scores", {}).get("combined_score", 0)
                    
                    if best_score >= 0.8:
                        match_stats["high_confidence_matches"] += 1
                        match_stats["matched_items"] += 1
                    elif best_score >= 0.5:
                        match_stats["partial_matches"] += 1
                        match_stats["matched_items"] += 1
                    else:
                        match_stats["no_matches"] += 1
                else:
                    match_stats["no_matches"] += 1
                    matches[item_id] = []
            
            result = {
                "matches": matches,
                "statistics": match_stats,
                "confidence": self._calculate_overall_confidence(match_stats),
                "agent": "semantic_search"
            }
            
            logger.info("Semantic search completed", 
                       total_items=match_stats["total_items"],
                       matched_items=match_stats["matched_items"],
                       high_confidence=match_stats["high_confidence_matches"])
            
            return result
            
        except Exception as e:
            logger.error("Semantic search failed", error=str(e))
            raise Exception(f"Semantic search failed: {str(e)}")
    
    async def _find_matches_for_item(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find matches for a single line item"""
        
        description = item.get("description", "")
        part_number = item.get("part_number")
        quantity = item.get("quantity", 1)
        
        if not description and not part_number:
            return []
        
        try:
            # Prepare search strategies
            search_strategies = []
            
            # Strategy 1: Direct part number search
            if part_number:
                search_strategies.append({
                    "type": "part_number",
                    "query": part_number,
                    "weight": 1.0
                })
            
            # Strategy 2: Full description search
            if description:
                search_strategies.append({
                    "type": "full_description", 
                    "query": description,
                    "weight": 0.9
                })
                
                # Strategy 3: Normalized description search
                normalized_desc = self.embedding_service.normalize_part_description(description)
                if normalized_desc != description:
                    search_strategies.append({
                        "type": "normalized_description",
                        "query": normalized_desc,
                        "weight": 0.8
                    })
                
                # Strategy 4: Key terms extraction
                key_terms = self._extract_key_terms(description)
                if key_terms:
                    search_strategies.append({
                        "type": "key_terms",
                        "query": " ".join(key_terms),
                        "weight": 0.7
                    })
            
            # Execute search strategies
            all_matches = []
            
            for strategy in search_strategies:
                matches = await self._execute_search_strategy(strategy, item)
                
                # Weight the scores based on strategy
                for match in matches:
                    original_score = match.get("scores", {}).get("combined_score", 0)
                    weighted_score = original_score * strategy["weight"]
                    
                    match["scores"]["strategy_weighted_score"] = weighted_score
                    match["search_strategy"] = strategy["type"]
                
                all_matches.extend(matches)
            
            # Deduplicate and merge matches
            unique_matches = self._deduplicate_matches(all_matches)
            
            # Add fuzzy matching for poor results
            if not unique_matches or unique_matches[0].get("scores", {}).get("strategy_weighted_score", 0) < 0.6:
                fuzzy_matches = await self._fuzzy_match_search(description)
                unique_matches.extend(fuzzy_matches)
                unique_matches = self._deduplicate_matches(unique_matches)
            
            # Sort by weighted score and limit results
            unique_matches.sort(
                key=lambda x: x.get("scores", {}).get("strategy_weighted_score", 0), 
                reverse=True
            )
            
            final_matches = unique_matches[:self.max_matches_per_item]
            
            # Add match explanations
            for match in final_matches:
                match["match_explanation"] = self._generate_match_explanation(item, match)
            
            return final_matches
            
        except Exception as e:
            logger.error("Failed to find matches for item", 
                        description=description[:100],
                        error=str(e))
            return []
    
    async def _execute_search_strategy(self, strategy: Dict[str, Any], 
                                     item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute a specific search strategy"""
        
        query = strategy["query"]
        
        # Extract filters from item if possible
        filters = {}
        
        # Material filtering
        material_hints = self._extract_material_hints(query)
        if material_hints:
            filters["material"] = material_hints[0]
        
        # Dimension filtering
        dimensions = self.embedding_service.extract_dimensions(query)
        if dimensions:
            filters["dimensions"] = dimensions
        
        try:
            # Execute search
            results = await self.parts_catalog.search_parts(
                query, 
                filters,
                top_k=self.max_matches_per_item * 2  # Get more for deduplication
            )
            
            # Filter by minimum confidence
            filtered_results = [
                r for r in results 
                if r.get("scores", {}).get("combined_score", 0) >= self.min_confidence_threshold
            ]
            
            return filtered_results
            
        except Exception as e:
            logger.debug("Search strategy failed", 
                        strategy=strategy["type"],
                        query=query[:50],
                        error=str(e))
            return []
    
    async def _fuzzy_match_search(self, description: str) -> List[Dict[str, Any]]:
        """Perform fuzzy matching for difficult cases"""
        
        try:
            # Extract individual words and search for each
            words = description.lower().split()
            important_words = [
                word for word in words 
                if len(word) > 2 and word not in ['the', 'and', 'or', 'with', 'for']
            ]
            
            all_fuzzy_matches = []
            
            # Search for combinations of important words
            for i in range(len(important_words)):
                for j in range(i + 1, min(i + 3, len(important_words) + 1)):
                    phrase = " ".join(important_words[i:j])
                    
                    matches = await self.parts_catalog.search_parts(
                        phrase,
                        top_k=3
                    )
                    
                    # Mark as fuzzy matches with lower confidence
                    for match in matches:
                        match["scores"]["fuzzy_match"] = True
                        original_score = match.get("scores", {}).get("combined_score", 0)
                        match["scores"]["strategy_weighted_score"] = original_score * 0.6
                        match["search_strategy"] = "fuzzy_match"
                    
                    all_fuzzy_matches.extend(matches)
            
            # Filter and deduplicate
            fuzzy_matches = [
                m for m in all_fuzzy_matches
                if m.get("scores", {}).get("strategy_weighted_score", 0) >= self.fuzzy_match_threshold
            ]
            
            return self._deduplicate_matches(fuzzy_matches)
            
        except Exception as e:
            logger.debug("Fuzzy matching failed", error=str(e))
            return []
    
    def _extract_key_terms(self, description: str) -> List[str]:
        """Extract key terms from description for targeted search"""
        
        # Common metal industry terms
        material_terms = [
            'stainless', 'steel', 'aluminum', 'brass', 'copper', 'titanium',
            'carbon', 'alloy', '304', '316', '316l', '6061', '2024', '1018'
        ]
        
        shape_terms = [
            'sheet', 'plate', 'bar', 'rod', 'tube', 'pipe', 'angle', 'channel',
            'beam', 'hex', 'round', 'square', 'flat'
        ]
        
        # Extract numbers (dimensions)
        numbers = re.findall(r'\d+\.?\d*', description)
        
        # Extract material and shape terms
        desc_lower = description.lower()
        found_materials = [term for term in material_terms if term in desc_lower]
        found_shapes = [term for term in shape_terms if term in desc_lower]
        
        # Combine key terms
        key_terms = found_materials + found_shapes + numbers[:3]  # Limit numbers
        
        return key_terms
    
    def _extract_material_hints(self, text: str) -> List[str]:
        """Extract material hints from text"""
        
        material_map = {
            'stainless': 'Stainless Steel',
            'steel': 'Steel',
            'aluminum': 'Aluminum', 
            'aluminium': 'Aluminum',
            'brass': 'Brass',
            'copper': 'Copper',
            'titanium': 'Titanium',
            'carbon': 'Carbon Steel'
        }
        
        text_lower = text.lower()
        found_materials = []
        
        for keyword, material in material_map.items():
            if keyword in text_lower:
                found_materials.append(material)
        
        return found_materials
    
    def _deduplicate_matches(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate matches based on part number"""
        
        seen_parts = set()
        unique_matches = []
        
        for match in matches:
            part_number = match.get("part_number")
            if part_number and part_number not in seen_parts:
                seen_parts.add(part_number)
                unique_matches.append(match)
        
        return unique_matches
    
    def _generate_match_explanation(self, item: Dict[str, Any], 
                                   match: Dict[str, Any]) -> str:
        """Generate human-readable explanation for the match"""
        
        explanations = []
        scores = match.get("scores", {})
        
        # Strategy explanation
        strategy = match.get("search_strategy", "unknown")
        if strategy == "part_number":
            explanations.append("Direct part number match")
        elif strategy == "full_description":
            explanations.append("Full description semantic match")
        elif strategy == "normalized_description":
            explanations.append("Normalized description match")
        elif strategy == "key_terms":
            explanations.append("Key terms match")
        elif strategy == "fuzzy_match":
            explanations.append("Fuzzy word matching")
        
        # Score explanation
        combined_score = scores.get("strategy_weighted_score", 0)
        if combined_score >= 0.8:
            explanations.append("High confidence match")
        elif combined_score >= 0.6:
            explanations.append("Good match")
        elif combined_score >= 0.4:
            explanations.append("Possible match")
        else:
            explanations.append("Low confidence match")
        
        # Material match
        item_desc = item.get("description", "").lower()
        match_material = match.get("material", "").lower()
        if any(mat in item_desc for mat in match_material.split()):
            explanations.append("Material match")
        
        return " | ".join(explanations)
    
    def _calculate_overall_confidence(self, match_stats: Dict[str, Any]) -> float:
        """Calculate overall confidence for the matching process"""
        
        total_items = match_stats.get("total_items", 1)
        matched_items = match_stats.get("matched_items", 0)
        high_confidence = match_stats.get("high_confidence_matches", 0)
        
        if total_items == 0:
            return 0.0
        
        # Calculate confidence based on match rates
        match_rate = matched_items / total_items
        high_confidence_rate = high_confidence / total_items
        
        # Weighted confidence score
        overall_confidence = (match_rate * 0.6) + (high_confidence_rate * 0.4)
        
        return round(overall_confidence, 3)
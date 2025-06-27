from typing import Dict, Any, List, Optional
import asyncio
import structlog

from ..services.local_parts_catalog import LocalPartsCatalogService
from ..services.embeddings import PartEmbeddingService
from .search_strategies.base import SearchContext
from .search_strategies.part_number import PartNumberStrategy
from .search_strategies.description import FullDescriptionStrategy, NormalizedDescriptionStrategy
from .search_strategies.key_terms import KeyTermsStrategy
from .search_strategies.fuzzy import FuzzyMatchStrategy
from .match_processor import MatchProcessor

logger = structlog.get_logger()


class SemanticSearchAgent:
    """Refactored agent using strategy pattern for better maintainability and testability"""
    
    def __init__(self):
        # Services
        self.parts_catalog = LocalPartsCatalogService()
        self.embedding_service = PartEmbeddingService()
        
        # Components
        self.search_context = SearchContext(self.parts_catalog, self.embedding_service)
        self.match_processor = MatchProcessor(max_matches_per_item=5)
        
        # Initialize strategies
        self._init_strategies()
    
    def _init_strategies(self):
        """Initialize search strategies"""
        self.strategies = {
            "part_number": PartNumberStrategy(self.parts_catalog),
            "full_description": FullDescriptionStrategy(self.parts_catalog),
            "normalized_description": NormalizedDescriptionStrategy(
                self.parts_catalog, self.embedding_service
            ),
            "key_terms": KeyTermsStrategy(self.parts_catalog),
            "fuzzy": FuzzyMatchStrategy(self.parts_catalog)
        }
    
    async def find_part_matches(self, line_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find part matches for extracted line items"""
        logger.info("Starting semantic search for parts", 
                   line_items_count=len(line_items))
        
        try:
            matches = {}
            match_stats = self._init_match_stats(len(line_items))
            
            # Process each line item
            tasks = []
            for i, item in enumerate(line_items):
                item_id = f"item_{i}"
                task = self._process_item(item_id, item)
                tasks.append(task)
            
            # Process items concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect results and update statistics
            for i, result in enumerate(results):
                item_id = f"item_{i}"
                
                if isinstance(result, Exception):
                    logger.error(f"Failed to process item {item_id}", error=str(result))
                    matches[item_id] = []
                    match_stats["no_matches"] += 1
                else:
                    matches[item_id] = result
                    self._update_match_stats(match_stats, result)
            
            return {
                "matches": matches,
                "statistics": match_stats,
                "confidence": self._calculate_overall_confidence(match_stats),
                "agent": "semantic_search"
            }
            
        except Exception as e:
            logger.error("Semantic search failed", error=str(e))
            raise Exception(f"Semantic search failed: {str(e)}")
    
    async def _process_item(self, item_id: str, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process a single line item"""
        logger.debug(f"Processing {item_id}", 
                    description=item.get("description", "")[:100])
        
        # Find matches
        item_matches = await self._find_matches_for_item(item)
        
        # Add match explanations
        for match in item_matches:
            match["match_explanation"] = self.match_processor.generate_match_explanation(
                item, match
            )
        
        return item_matches
    
    async def _find_matches_for_item(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find matches for a single line item using multiple strategies"""
        description = item.get("description", "")
        part_number = item.get("part_number")
        
        if not description and not part_number:
            return []
        
        # Build strategy execution plan
        strategies_to_run = []
        
        if part_number:
            strategies_to_run.append(("part_number", part_number))
        
        if description:
            strategies_to_run.append(("full_description", description))
            
            # Check if normalized description is different
            normalized = self.embedding_service.normalize_part_description(description)
            if normalized != description:
                strategies_to_run.append(("normalized_description", normalized))
            
            strategies_to_run.append(("key_terms", description))
        
        # Execute strategies
        all_matches = []
        for strategy_name, query in strategies_to_run:
            strategy = self.strategies[strategy_name]
            filters = self._extract_filters(item, query)
            
            matches = await self.search_context.execute_strategy(
                strategy, query, filters, top_k=10
            )
            all_matches.extend(matches)
        
        # Deduplicate and process matches
        unique_matches = self.match_processor.deduplicate_matches(all_matches)
        
        # Apply fuzzy matching if results are poor
        if self._should_apply_fuzzy_matching(unique_matches):
            fuzzy_matches = await self._apply_fuzzy_matching(description, item)
            unique_matches.extend(fuzzy_matches)
            unique_matches = self.match_processor.deduplicate_matches(unique_matches)
        
        # Sort and limit results
        final_matches = self.match_processor.sort_and_limit_matches(unique_matches)
        
        return final_matches
    
    def _extract_filters(self, item: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Extract search filters from item and query"""
        filters = {}
        
        # Material filtering
        if item.get("material"):
            filters["material"] = item["material"]
        else:
            material_hints = self._extract_material_hints(query)
            if material_hints:
                filters["material"] = material_hints[0]
        
        # Dimension filtering
        dimensions = self.embedding_service.extract_dimensions(query)
        if dimensions:
            filters["dimensions"] = dimensions
        
        return filters
    
    def _extract_material_hints(self, text: str) -> List[str]:
        """Extract material hints from text"""
        material_keywords = [
            "steel", "stainless", "aluminum", "brass", "copper", "plastic",
            "rubber", "iron", "titanium", "carbon", "alloy", "zinc"
        ]
        
        text_lower = text.lower()
        found_materials = []
        
        for material in material_keywords:
            if material in text_lower:
                found_materials.append(material)
        
        return found_materials
    
    def _should_apply_fuzzy_matching(self, matches: List[Dict[str, Any]]) -> bool:
        """Determine if fuzzy matching should be applied"""
        if not matches:
            return True
        
        best_score = max(
            m.get("scores", {}).get("strategy_weighted_score", 0) 
            for m in matches
        )
        
        return best_score < 0.6
    
    async def _apply_fuzzy_matching(self, description: str, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply fuzzy matching strategy"""
        strategy = self.strategies["fuzzy"]
        filters = self._extract_filters(item, description)
        
        return await self.search_context.execute_strategy(
            strategy, description, filters, top_k=5
        )
    
    def _init_match_stats(self, total_items: int) -> Dict[str, int]:
        """Initialize match statistics"""
        return {
            "total_items": total_items,
            "matched_items": 0,
            "high_confidence_matches": 0,
            "partial_matches": 0,
            "no_matches": 0
        }
    
    def _update_match_stats(self, stats: Dict[str, int], matches: List[Dict[str, Any]]):
        """Update match statistics based on results"""
        if not matches:
            stats["no_matches"] += 1
            return
        
        quality = self.match_processor.calculate_match_quality(matches)
        best_confidence = quality["best_confidence"]
        
        if best_confidence >= 0.8:
            stats["high_confidence_matches"] += 1
            stats["matched_items"] += 1
        elif best_confidence >= 0.5:
            stats["partial_matches"] += 1
            stats["matched_items"] += 1
        else:
            stats["no_matches"] += 1
    
    def _calculate_overall_confidence(self, stats: Dict[str, int]) -> float:
        """Calculate overall confidence score for the search results"""
        if stats["total_items"] == 0:
            return 0.0
        
        # Weight different match types
        score = (
            stats["high_confidence_matches"] * 1.0 +
            stats["partial_matches"] * 0.6
        ) / stats["total_items"]
        
        return min(score, 1.0)
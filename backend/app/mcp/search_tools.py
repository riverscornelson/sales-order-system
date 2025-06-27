"""
MCP Search Tools for Agentic Parts Discovery
Provides comprehensive search capabilities for intelligent agent-driven parts lookup
"""

import asyncio
import re
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import structlog
from fuzzywuzzy import fuzz, process
import pandas as pd
import numpy as np

from ..services.parts_catalog import PartsCatalogService
from ..models.line_item_schemas import LineItem, SearchResult, MatchConfidence

logger = structlog.get_logger()

@dataclass
class SearchStrategy:
    """Represents a search strategy with metadata"""
    name: str
    description: str
    confidence_boost: float
    typical_use_cases: List[str]

class AgenticSearchTools:
    """MCP-style search tools for autonomous agent use"""
    
    def __init__(self, catalog_service: PartsCatalogService):
        self.catalog_service = catalog_service
        self.search_strategies = self._initialize_search_strategies()
        
    def _initialize_search_strategies(self) -> Dict[str, SearchStrategy]:
        """Initialize available search strategies with metadata"""
        return {
            "semantic_vector": SearchStrategy(
                name="Semantic Vector Search",
                description="Embedding-based similarity search for general matching",
                confidence_boost=1.0,
                typical_use_cases=["General part descriptions", "Material specifications", "Complex requirements"]
            ),
            "fuzzy_text": SearchStrategy(
                name="Fuzzy Text Search", 
                description="Flexible string matching across all text fields",
                confidence_boost=0.8,
                typical_use_cases=["Part numbers", "Exact material names", "Manufacturer specifications"]
            ),
            "material_category": SearchStrategy(
                name="Material Category Search",
                description="Structured search by material type and form factor",
                confidence_boost=0.9,
                typical_use_cases=["Material-specific searches", "Form factor matching", "Category browsing"]
            ),
            "dimensional": SearchStrategy(
                name="Dimensional Search",
                description="Size-based matching with configurable tolerances",
                confidence_boost=0.7,
                typical_use_cases=["Specific size requirements", "Dimensional constraints", "Tolerance-based matching"]
            ),
            "alternative_materials": SearchStrategy(
                name="Alternative Materials Search",
                description="Find substitute materials for given applications",
                confidence_boost=0.6,
                typical_use_cases=["Material substitution", "Cost optimization", "Availability alternatives"]
            )
        }
    
    async def semantic_vector_search(self, query: str, top_k: int = 10, 
                                   min_similarity: float = 0.3) -> List[SearchResult]:
        """
        MCP Tool: Traditional embedding-based semantic search
        
        Args:
            query: Natural language search query
            top_k: Maximum number of results to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of search results with similarity scores
        """
        logger.info("🔍 Executing semantic vector search", 
                   query=query, top_k=top_k, min_similarity=min_similarity)
        
        try:
            # Check if we're using mock embeddings and adjust threshold
            from ..services.embeddings import PartEmbeddingService
            embedding_service = PartEmbeddingService()
            
            # If using mock embeddings, use a very low threshold
            adjusted_min_similarity = min_similarity
            if hasattr(embedding_service.embedding_service, 'client') and not embedding_service.embedding_service.client:  # Using mock embeddings
                adjusted_min_similarity = -1.0  # Accept any similarity
                logger.warning("Using mock embeddings - adjusting similarity threshold to accept all results",
                             original_threshold=min_similarity, adjusted_threshold=adjusted_min_similarity)
            
            # Use existing catalog service for vector search
            results = await self.catalog_service.search_parts(
                query=query,
                filters=None,
                top_k=top_k
            )
            
            # Filter by minimum similarity and convert to SearchResult objects
            search_results = []
            for i, result in enumerate(results):
                combined_score = result.get("scores", {}).get("combined_score", 0)
                if combined_score >= adjusted_min_similarity:
                    search_result = SearchResult(
                        rank=i + 1,
                        part_number=result["part_number"],
                        description=result["description"],
                        similarity_score=combined_score,
                        spec_match={"overall": "semantic_match"},
                        availability=result.get("availability"),
                        unit_price=result.get("unit_price"),
                        supplier=result.get("supplier"),
                        match_confidence=self._score_to_confidence(combined_score),
                        notes=[f"Found via semantic vector search (similarity: {combined_score:.3f})"]
                    )
                    search_results.append(search_result)
            
            logger.info("✅ Semantic vector search completed", 
                       results_found=len(search_results), query=query)
            return search_results
            
        except Exception as e:
            logger.error("❌ Semantic vector search failed", error=str(e), query=query)
            return []
    
    async def fuzzy_text_search(self, terms: List[str], material_type: str = None,
                              fuzzy_threshold: int = 70) -> List[SearchResult]:
        """
        MCP Tool: Fuzzy string matching across descriptions, part numbers, specs
        
        Args:
            terms: List of search terms to match
            material_type: Optional material filter
            fuzzy_threshold: Minimum fuzzy match score (0-100)
            
        Returns:
            List of search results ranked by fuzzy match score
        """
        logger.info("🔤 Executing fuzzy text search", 
                   terms=terms, material_type=material_type, threshold=fuzzy_threshold)
        
        try:
            # Get all parts from catalog (we'll implement a get_all_parts method)
            all_parts = await self._get_all_catalog_parts()
            if not all_parts:
                logger.warning("No parts found in catalog for fuzzy search")
                return []
            
            fuzzy_matches = []
            
            for part in all_parts:
                # Create searchable text from part
                searchable_text = self._create_searchable_text(part)
                
                # Apply material filter if specified
                if material_type and not self._material_matches(part, material_type):
                    continue
                
                # Calculate fuzzy match scores for each term
                best_score = 0
                matched_term = ""
                
                for term in terms:
                    score = fuzz.partial_ratio(term.lower(), searchable_text.lower())
                    if score > best_score:
                        best_score = score
                        matched_term = term
                
                # Include if above threshold
                if best_score >= fuzzy_threshold:
                    search_result = SearchResult(
                        rank=0,  # Will be reranked
                        part_number=part["part_number"],
                        description=part["description"],
                        similarity_score=best_score / 100.0,  # Normalize to 0-1
                        spec_match={"overall": "fuzzy_text_match", "matched_term": matched_term},
                        availability=part.get("availability"),
                        unit_price=part.get("unit_price"),
                        supplier=part.get("supplier"),
                        match_confidence=self._score_to_confidence(best_score / 100.0),
                        notes=[f"Fuzzy match for '{matched_term}' (score: {best_score})"]
                    )
                    fuzzy_matches.append((best_score, search_result))
            
            # Sort by score and assign ranks
            fuzzy_matches.sort(key=lambda x: x[0], reverse=True)
            search_results = []
            for i, (score, result) in enumerate(fuzzy_matches[:20]):  # Limit to top 20
                result.rank = i + 1
                search_results.append(result)
            
            logger.info("✅ Fuzzy text search completed", 
                       results_found=len(search_results), terms=terms)
            return search_results
            
        except Exception as e:
            logger.error("❌ Fuzzy text search failed", error=str(e), terms=terms)
            return []
    
    async def material_category_search(self, material: str, form: str = None, 
                                     size_range: Dict = None, strict: bool = False) -> List[SearchResult]:
        """
        MCP Tool: Search by material properties with flexible constraints
        
        Args:
            material: Material type (e.g., "steel", "aluminum", "4140")
            form: Form factor (e.g., "bar", "sheet", "tube")
            size_range: Dictionary with size constraints
            strict: Whether to use strict matching or fuzzy
            
        Returns:
            List of search results filtered by material and form
        """
        logger.info("🔧 Executing material category search", 
                   material=material, form=form, size_range=size_range)
        
        try:
            # Create filters for catalog search
            filters = {}
            
            # Material mapping
            material_lower = material.lower()
            if any(term in material_lower for term in ["4140", "carbon steel"]):
                filters["material"] = "Carbon Steel"
            elif "aluminum" in material_lower or "aluminium" in material_lower:
                filters["material"] = "Aluminum"
            elif "stainless" in material_lower:
                filters["material"] = "Stainless Steel"
            elif "steel" in material_lower:
                filters["material"] = "Steel"
            elif "titanium" in material_lower:
                filters["material"] = "Titanium"
            elif "brass" in material_lower:
                filters["material"] = "Brass"
            elif "copper" in material_lower:
                filters["material"] = "Copper"
            
            # Form/category mapping
            if form:
                form_lower = form.lower()
                if "bar" in form_lower or "rod" in form_lower:
                    filters["category"] = "Bar"
                elif "sheet" in form_lower:
                    filters["category"] = "Sheet"
                elif "plate" in form_lower:
                    filters["category"] = "Plate"
                elif "tube" in form_lower or "pipe" in form_lower:
                    filters["category"] = "Tube"
                elif "angle" in form_lower:
                    filters["category"] = "Angle"
            
            # Use catalog service with filters
            query = f"{material} {form or ''}".strip()
            results = await self.catalog_service.search_parts(
                query=query,
                filters=filters,
                top_k=15
            )
            
            # Convert to SearchResult objects
            search_results = []
            for i, result in enumerate(results):
                # Additional size filtering if requested
                if size_range and not self._size_matches(result, size_range):
                    continue
                
                combined_score = result.get("scores", {}).get("combined_score", 0)
                search_result = SearchResult(
                    rank=i + 1,
                    part_number=result["part_number"],
                    description=result["description"],
                    similarity_score=combined_score,
                    spec_match=self._analyze_material_match(result, material, form),
                    availability=result.get("availability"),
                    unit_price=result.get("unit_price"),
                    supplier=result.get("supplier"),
                    match_confidence=self._score_to_confidence(combined_score),
                    notes=[f"Material category match: {filters}"]
                )
                search_results.append(search_result)
            
            logger.info("✅ Material category search completed", 
                       results_found=len(search_results), material=material)
            return search_results
            
        except Exception as e:
            logger.error("❌ Material category search failed", error=str(e), material=material)
            return []
    
    async def dimensional_search(self, target_dims: Dict, tolerance: float = 0.2) -> List[SearchResult]:
        """
        MCP Tool: Find parts within dimensional tolerances
        
        Args:
            target_dims: Target dimensions (e.g., {"diameter": 6.25, "length": 20})
            tolerance: Tolerance as fraction (e.g., 0.2 = 20%)
            
        Returns:
            List of parts matching dimensional criteria
        """
        logger.info("📏 Executing dimensional search", 
                   target_dims=target_dims, tolerance=tolerance)
        
        try:
            all_parts = await self._get_all_catalog_parts()
            dimensional_matches = []
            
            for part in all_parts:
                specs = part.get("specifications", {})
                if not specs:
                    continue
                
                # Check dimensional matches
                match_score = self._calculate_dimensional_match(specs, target_dims, tolerance)
                if match_score > 0:
                    search_result = SearchResult(
                        rank=0,  # Will be reranked
                        part_number=part["part_number"],
                        description=part["description"],
                        similarity_score=match_score,
                        spec_match=self._analyze_dimensional_match(specs, target_dims),
                        availability=part.get("availability"),
                        unit_price=part.get("unit_price"),
                        supplier=part.get("supplier"),
                        match_confidence=self._score_to_confidence(match_score),
                        notes=[f"Dimensional match within {tolerance*100:.1f}% tolerance"]
                    )
                    dimensional_matches.append((match_score, search_result))
            
            # Sort by match score and assign ranks
            dimensional_matches.sort(key=lambda x: x[0], reverse=True)
            search_results = []
            for i, (score, result) in enumerate(dimensional_matches[:15]):
                result.rank = i + 1
                search_results.append(result)
            
            logger.info("✅ Dimensional search completed", 
                       results_found=len(search_results), target_dims=target_dims)
            return search_results
            
        except Exception as e:
            logger.error("❌ Dimensional search failed", error=str(e), target_dims=target_dims)
            return []
    
    async def alternative_materials_search(self, primary_material: str, 
                                         application: str = "general") -> List[SearchResult]:
        """
        MCP Tool: Find suitable alternative materials for given application
        
        Args:
            primary_material: Primary material being replaced
            application: Application context (affects substitution rules)
            
        Returns:
            List of alternative materials with suitability scores
        """
        logger.info("🔄 Executing alternative materials search", 
                   primary_material=primary_material, application=application)
        
        try:
            # Define material substitution rules
            alternatives = self._get_material_alternatives(primary_material, application)
            
            if not alternatives:
                logger.warning("No alternatives found for material", material=primary_material)
                return []
            
            # Search for each alternative material
            all_alternatives = []
            for alt_material, suitability_score in alternatives.items():
                alt_results = await self.material_category_search(alt_material)
                
                # Adjust scores based on suitability
                for result in alt_results:
                    result.similarity_score *= suitability_score
                    result.notes.append(f"Alternative to {primary_material} (suitability: {suitability_score:.2f})")
                    all_alternatives.append((result.similarity_score, result))
            
            # Sort and rank alternatives
            all_alternatives.sort(key=lambda x: x[0], reverse=True)
            search_results = []
            for i, (score, result) in enumerate(all_alternatives[:15]):
                result.rank = i + 1
                search_results.append(result)
            
            logger.info("✅ Alternative materials search completed", 
                       results_found=len(search_results), primary_material=primary_material)
            return search_results
            
        except Exception as e:
            logger.error("❌ Alternative materials search failed", 
                        error=str(e), primary_material=primary_material)
            return []
    
    async def catalog_exploration(self, query_type: str = "overview") -> Dict[str, Any]:
        """
        MCP Tool: Explore catalog structure and available materials
        
        Args:
            query_type: Type of exploration ("overview", "materials", "categories", "sizes")
            
        Returns:
            Dictionary with catalog exploration results
        """
        logger.info("🗺️ Executing catalog exploration", query_type=query_type)
        
        try:
            all_parts = await self._get_all_catalog_parts()
            
            if query_type == "overview":
                return await self._get_catalog_overview(all_parts)
            elif query_type == "materials":
                return await self._get_materials_breakdown(all_parts)
            elif query_type == "categories":
                return await self._get_categories_breakdown(all_parts)
            elif query_type == "sizes":
                return await self._get_size_ranges(all_parts)
            else:
                return {"error": f"Unknown query_type: {query_type}"}
                
        except Exception as e:
            logger.error("❌ Catalog exploration failed", error=str(e), query_type=query_type)
            return {"error": str(e)}
    
    async def debug_search_pipeline(self, query: str) -> Dict[str, Any]:
        """
        MCP Tool: Debug why a specific search returns no results
        
        Args:
            query: The search query to debug
            
        Returns:
            Detailed debug information about search pipeline
        """
        logger.info("🔧 Executing search pipeline debug", query=query)
        
        debug_info = {
            "query": query,
            "timestamp": logger._context.get("timestamp", "unknown"),
            "catalog_status": {},
            "embedding_test": {},
            "search_results": {},
            "text_matches": {},
            "recommendations": []
        }
        
        try:
            # Check catalog status
            stats = await self.catalog_service.get_catalog_stats()
            debug_info["catalog_status"] = {
                "total_parts": stats.get("total_parts", 0),
                "vector_store_count": stats.get("vector_store", {}).get("count", 0),
                "materials_available": len(stats.get("materials", [])),
                "categories_available": len(stats.get("categories", []))
            }
            
            # Test embedding generation
            try:
                from ..services.embeddings import PartEmbeddingService
                embedding_service = PartEmbeddingService()
                test_embedding = await embedding_service.create_query_embedding(query)
                debug_info["embedding_test"] = {
                    "embedding_generated": test_embedding is not None,
                    "embedding_length": len(test_embedding) if test_embedding else 0,
                    "embedding_preview": test_embedding[:5] if test_embedding else None
                }
            except Exception as e:
                debug_info["embedding_test"] = {"error": str(e)}
            
            # Test multiple search strategies
            semantic_results = await self.semantic_vector_search(query, top_k=5)
            debug_info["search_results"]["semantic_vector"] = {
                "count": len(semantic_results),
                "top_result": semantic_results[0].dict() if semantic_results else None
            }
            
            # Test fuzzy text search
            fuzzy_results = await self.fuzzy_text_search([query], fuzzy_threshold=50)
            debug_info["search_results"]["fuzzy_text"] = {
                "count": len(fuzzy_results),
                "top_result": fuzzy_results[0].dict() if fuzzy_results else None
            }
            
            # Simple text matching test
            simple_matches = await self._simple_text_matches(query)
            debug_info["text_matches"] = {
                "count": len(simple_matches),
                "matches": simple_matches[:3]
            }
            
            # Generate recommendations
            debug_info["recommendations"] = self._generate_debug_recommendations(debug_info)
            
            logger.info("✅ Search pipeline debug completed", 
                       query=query, issues_found=len(debug_info["recommendations"]))
            return debug_info
            
        except Exception as e:
            logger.error("❌ Search pipeline debug failed", error=str(e), query=query)
            debug_info["error"] = str(e)
            return debug_info
    
    # Helper methods
    
    async def _get_all_catalog_parts(self) -> List[Dict[str, Any]]:
        """Get all parts from catalog for processing"""
        try:
            # First try to get parts from vector store (which has CSV data)
            from ..services.local_vector_store import LocalPartsCatalogVectorStore
            vector_store = LocalPartsCatalogVectorStore()
            
            try:
                # Get all parts from vector store
                all_vector_parts = await vector_store.get_all_parts()
                if all_vector_parts and len(all_vector_parts) > len(self.catalog_service.mock_parts):
                    logger.info(f"Using vector store parts: {len(all_vector_parts)} parts")
                    return all_vector_parts
            except Exception as e:
                logger.warning("Could not get parts from vector store", error=str(e))
            
            # Fallback to mock parts
            logger.info(f"Using mock parts: {len(self.catalog_service.mock_parts)} parts")
            return self.catalog_service.mock_parts
            
        except Exception as e:
            logger.error("Failed to get catalog parts", error=str(e))
            return []
    
    def _create_searchable_text(self, part: Dict[str, Any]) -> str:
        """Create searchable text from part data"""
        searchable_parts = [
            part.get("part_number", ""),
            part.get("description", ""),
            part.get("material", ""),
            part.get("category", ""),
            part.get("supplier", "")
        ]
        
        # Add specifications
        specs = part.get("specifications", {})
        for key, value in specs.items():
            searchable_parts.append(f"{key}:{value}")
        
        return " ".join(str(p) for p in searchable_parts if p)
    
    def _material_matches(self, part: Dict[str, Any], material_type: str) -> bool:
        """Check if part material matches type"""
        part_material = part.get("material", "").lower()
        material_type_lower = material_type.lower()
        
        # Simple material matching logic
        return material_type_lower in part_material or part_material in material_type_lower
    
    def _score_to_confidence(self, score: float) -> MatchConfidence:
        """Convert numeric score to confidence enum"""
        if score >= 0.9:
            return MatchConfidence.HIGH
        elif score >= 0.75:
            return MatchConfidence.MEDIUM_HIGH
        elif score >= 0.6:
            return MatchConfidence.MEDIUM
        elif score >= 0.4:
            return MatchConfidence.MEDIUM_LOW
        else:
            return MatchConfidence.LOW
    
    def _size_matches(self, result: Dict[str, Any], size_range: Dict) -> bool:
        """Check if result matches size constraints"""
        # Simplified size matching - can be enhanced
        specs = result.get("specifications", {})
        
        for dim_name, target_value in size_range.items():
            if dim_name in specs:
                spec_value = specs[dim_name]
                if isinstance(spec_value, (int, float)) and isinstance(target_value, (int, float)):
                    # Check if within reasonable range
                    if abs(spec_value - target_value) / target_value > 0.5:  # 50% tolerance
                        return False
        
        return True
    
    def _analyze_material_match(self, result: Dict[str, Any], 
                              material: str, form: str) -> Dict[str, str]:
        """Analyze how well result matches material and form"""
        spec_match = {}
        
        result_material = result.get("material", "").lower()
        material_lower = material.lower()
        
        if material_lower in result_material:
            spec_match["material"] = "exact_match"
        elif any(term in result_material for term in material_lower.split()):
            spec_match["material"] = "partial_match"
        else:
            spec_match["material"] = "different"
        
        if form:
            result_category = result.get("category", "").lower()
            form_lower = form.lower()
            
            if form_lower in result_category or result_category in form_lower:
                spec_match["form"] = "exact_match"
            else:
                spec_match["form"] = "different"
        
        return spec_match
    
    def _calculate_dimensional_match(self, specs: Dict, target_dims: Dict, 
                                   tolerance: float) -> float:
        """Calculate dimensional match score"""
        if not specs or not target_dims:
            return 0.0
        
        matches = 0
        total = 0
        
        for dim_name, target_value in target_dims.items():
            if dim_name in specs:
                spec_value = specs[dim_name]
                if isinstance(spec_value, (int, float)) and isinstance(target_value, (int, float)):
                    total += 1
                    deviation = abs(spec_value - target_value) / target_value
                    if deviation <= tolerance:
                        matches += 1
        
        return matches / total if total > 0 else 0.0
    
    def _analyze_dimensional_match(self, specs: Dict, target_dims: Dict) -> Dict[str, str]:
        """Analyze dimensional matching details"""
        spec_match = {"overall": "dimensional_analysis"}
        
        for dim_name, target_value in target_dims.items():
            if dim_name in specs:
                spec_value = specs[dim_name]
                if isinstance(spec_value, (int, float)) and isinstance(target_value, (int, float)):
                    deviation = abs(spec_value - target_value) / target_value
                    if deviation <= 0.1:
                        spec_match[dim_name] = "exact_match"
                    elif deviation <= 0.2:
                        spec_match[dim_name] = "close_match"
                    else:
                        spec_match[dim_name] = "different"
        
        return spec_match
    
    def _get_material_alternatives(self, primary_material: str, 
                                 application: str) -> Dict[str, float]:
        """Get alternative materials with suitability scores"""
        primary_lower = primary_material.lower()
        
        # Material substitution rules
        alternatives = {}
        
        if "4140" in primary_lower or "carbon steel" in primary_lower:
            alternatives.update({
                "4340": 0.9,  # Very similar steel
                "1045": 0.7,  # Lower carbon steel
                "Steel": 0.6,  # Generic steel
                "Alloy Steel": 0.8  # General alloy steels
            })
        
        if "aluminum" in primary_lower:
            alternatives.update({
                "6061": 0.9,
                "2024": 0.8,
                "7075": 0.7
            })
        
        if "stainless" in primary_lower:
            alternatives.update({
                "304": 0.9,
                "316": 0.8,
                "316L": 0.8
            })
        
        return alternatives
    
    async def _get_catalog_overview(self, all_parts: List[Dict]) -> Dict[str, Any]:
        """Generate catalog overview"""
        materials = set()
        categories = set()
        suppliers = set()
        total_value = 0
        
        for part in all_parts:
            if part.get("material"):
                materials.add(part["material"])
            if part.get("category"):
                categories.add(part["category"])
            if part.get("supplier"):
                suppliers.add(part["supplier"])
            if part.get("unit_price") and part.get("availability"):
                total_value += part["unit_price"] * part["availability"]
        
        return {
            "total_parts": len(all_parts),
            "unique_materials": len(materials),
            "unique_categories": len(categories),
            "unique_suppliers": len(suppliers),
            "total_inventory_value": round(total_value, 2),
            "materials_list": sorted(list(materials)),
            "categories_list": sorted(list(categories))
        }
    
    async def _get_materials_breakdown(self, all_parts: List[Dict]) -> Dict[str, Any]:
        """Get detailed materials breakdown"""
        materials_count = {}
        for part in all_parts:
            material = part.get("material", "Unknown")
            materials_count[material] = materials_count.get(material, 0) + 1
        
        return {
            "materials_breakdown": materials_count,
            "most_common": max(materials_count.items(), key=lambda x: x[1]) if materials_count else None,
            "total_materials": len(materials_count)
        }
    
    async def _get_categories_breakdown(self, all_parts: List[Dict]) -> Dict[str, Any]:
        """Get detailed categories breakdown"""
        categories_count = {}
        for part in all_parts:
            category = part.get("category", "Unknown")
            categories_count[category] = categories_count.get(category, 0) + 1
        
        return {
            "categories_breakdown": categories_count,
            "most_common": max(categories_count.items(), key=lambda x: x[1]) if categories_count else None,
            "total_categories": len(categories_count)
        }
    
    async def _get_size_ranges(self, all_parts: List[Dict]) -> Dict[str, Any]:
        """Get size ranges analysis"""
        dimensions = {}
        
        for part in all_parts:
            specs = part.get("specifications", {})
            for key, value in specs.items():
                if isinstance(value, (int, float)) and "price" not in key.lower():
                    if key not in dimensions:
                        dimensions[key] = {"min": value, "max": value, "count": 1}
                    else:
                        dimensions[key]["min"] = min(dimensions[key]["min"], value)
                        dimensions[key]["max"] = max(dimensions[key]["max"], value)
                        dimensions[key]["count"] += 1
        
        return {
            "dimensional_ranges": dimensions,
            "common_dimensions": sorted(dimensions.keys(), key=lambda x: dimensions[x]["count"], reverse=True)[:5]
        }
    
    async def _simple_text_matches(self, query: str) -> List[str]:
        """Simple text matching for debugging"""
        all_parts = await self._get_all_catalog_parts()
        matches = []
        
        query_lower = query.lower()
        for part in all_parts:
            searchable = self._create_searchable_text(part).lower()
            if query_lower in searchable:
                matches.append(f"{part['part_number']}: {part['description']}")
        
        return matches
    
    def _generate_debug_recommendations(self, debug_info: Dict) -> List[str]:
        """Generate recommendations based on debug results"""
        recommendations = []
        
        catalog_status = debug_info.get("catalog_status", {})
        if catalog_status.get("total_parts", 0) == 0:
            recommendations.append("Catalog appears empty - check catalog loading")
        
        if catalog_status.get("vector_store_count", 0) == 0:
            recommendations.append("Vector store empty - check embedding generation")
        
        embedding_test = debug_info.get("embedding_test", {})
        if not embedding_test.get("embedding_generated", False):
            recommendations.append("Embedding generation failed - check OpenAI API key")
        
        search_results = debug_info.get("search_results", {})
        if all(result.get("count", 0) == 0 for result in search_results.values()):
            recommendations.append("All search strategies failed - check query formatting")
        
        text_matches = debug_info.get("text_matches", {})
        if text_matches.get("count", 0) > 0:
            recommendations.append("Simple text matches found - semantic search may be the issue")
        
        return recommendations
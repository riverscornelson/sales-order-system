import asyncio
import re
from typing import List, Dict, Any, Optional
import structlog

from ..models.line_item_schemas import LineItem, SearchResult, MatchConfidence
from ..services.parts_catalog import PartsCatalogService

logger = structlog.get_logger()

class LineItemSearchAgent:
    """Agent responsible for finding potential part matches for individual line items"""
    
    def __init__(self, catalog_service: PartsCatalogService):
        self.catalog_service = catalog_service
        
    async def search_for_line_item(self, line_item: LineItem) -> List[SearchResult]:
        """Perform comprehensive search for a single line item"""
        
        logger.info("Starting search for line item", 
                   line_id=line_item.line_id,
                   raw_text=line_item.raw_text[:100])
        
        try:
            # Generate multiple search strategies
            search_queries = self._generate_search_queries(line_item)
            
            # Execute searches in parallel
            search_tasks = []
            for strategy, query in search_queries.items():
                task = self._execute_search_strategy(strategy, query, line_item)
                search_tasks.append(task)
            
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Merge and rank all results
            merged_results = self._merge_and_rank_results(search_results, line_item)
            
            # Convert to SearchResult objects
            formatted_results = self._format_search_results(merged_results, line_item)
            
            logger.info("Search completed for line item",
                       line_id=line_item.line_id,
                       total_results=len(formatted_results))
            
            return formatted_results
            
        except Exception as e:
            logger.error("Search failed for line item",
                        line_id=line_item.line_id,
                        error=str(e))
            return []
    
    def _generate_search_queries(self, line_item: LineItem) -> Dict[str, str]:
        """Generate multiple search strategies for comprehensive coverage"""
        
        specs = line_item.extracted_specs
        queries = {}
        
        if not specs:
            # Fallback to raw text parsing
            queries["raw_text"] = line_item.raw_text
            return queries
        
        # Strategy 1: Full specification search
        full_query_parts = []
        if specs.material_grade:
            full_query_parts.append(specs.material_grade)
        if specs.form:
            full_query_parts.append(specs.form)
        if specs.dimensions:
            dims = self._format_dimensions(specs.dimensions)
            if dims:
                full_query_parts.append(dims)
        
        if full_query_parts:
            queries["full_spec"] = " ".join(full_query_parts)
        
        # Strategy 2: Material + Form only
        if specs.material_grade and specs.form:
            queries["material_form"] = f"{specs.material_grade} {specs.form}"
        
        # Strategy 3: Material only (broadest)
        if specs.material_grade:
            queries["material_only"] = specs.material_grade
        
        # Strategy 4: Alternative material grades
        if specs.grade_equivalents:
            for i, alt_grade in enumerate(specs.grade_equivalents[:3]):  # Limit to 3 alternatives
                alt_query_parts = [alt_grade]
                if specs.form:
                    alt_query_parts.append(specs.form)
                queries[f"alternative_{i+1}"] = " ".join(alt_query_parts)
        
        # Strategy 5: Dimensional search (for when material is unclear)
        if specs.dimensions and specs.form:
            dims = self._format_dimensions(specs.dimensions)
            if dims:
                queries["dimensional"] = f"{specs.form} {dims}"
        
        # Strategy 6: Specification keywords
        spec_keywords = []
        if specs.surface_finish:
            spec_keywords.append(specs.surface_finish)
        if specs.heat_treatment:
            spec_keywords.append(specs.heat_treatment)
        if spec_keywords:
            base_query = queries.get("material_form", queries.get("material_only", ""))
            if base_query:
                queries["with_specs"] = f"{base_query} {' '.join(spec_keywords)}"
        
        # Fallback: Use raw text if no structured queries generated
        if not queries:
            queries["raw_text"] = line_item.raw_text
        
        logger.info("Generated search queries", 
                    line_id=line_item.line_id,
                    strategies=list(queries.keys()),
                    queries=queries)
        
        return queries
    
    def _format_dimensions(self, dimensions: Dict[str, Any]) -> str:
        """Format dimensions for search query"""
        
        if not dimensions:
            return ""
        
        dim_parts = []
        
        # Handle common dimension patterns
        if "length" in dimensions and "width" in dimensions:
            if "thickness" in dimensions:
                # L x W x T format
                dim_parts.append(f"{dimensions['length']}x{dimensions['width']}x{dimensions['thickness']}")
            else:
                # L x W format
                dim_parts.append(f"{dimensions['length']}x{dimensions['width']}")
        elif "diameter" in dimensions:
            # Diameter format
            dim_parts.append(f"diameter {dimensions['diameter']}")
            if "length" in dimensions:
                dim_parts.append(f"length {dimensions['length']}")
        
        # Add individual dimensions as keywords
        for key, value in dimensions.items():
            if key not in ["length", "width", "thickness", "diameter"] and value:
                dim_parts.append(f"{key} {value}")
        
        return " ".join(dim_parts)
    
    async def _execute_search_strategy(self, strategy: str, query: str, 
                                     line_item: LineItem) -> Dict[str, Any]:
        """Execute a single search strategy"""
        
        try:
            # Determine search parameters based on strategy
            if strategy == "full_spec":
                top_k = 5
                filters = self._create_filters(line_item)
            elif strategy == "material_form":
                top_k = 8
                filters = self._create_material_filters(line_item)
            elif strategy in ["material_only", "raw_text"]:
                top_k = 10
                filters = None
            else:
                top_k = 5
                filters = None
            
            # Execute search
            logger.info("Executing search strategy", 
                       strategy=strategy, 
                       query=query.strip(), 
                       filters=filters, 
                       top_k=top_k)
            results = await self.catalog_service.search_parts(
                query=query.strip(),
                filters=filters,
                top_k=top_k
            )
            logger.info("Search strategy results", 
                       strategy=strategy, 
                       results_count=len(results))
            
            return {
                "strategy": strategy,
                "query": query,
                "results": results,
                "success": True
            }
            
        except Exception as e:
            logger.warning("Search strategy failed",
                          strategy=strategy,
                          query=query,
                          error=str(e))
            return {
                "strategy": strategy,
                "query": query,
                "results": [],
                "success": False,
                "error": str(e)
            }
    
    def _create_filters(self, line_item: LineItem) -> Optional[Dict[str, Any]]:
        """Create search filters based on line item specifications"""
        
        if not line_item.extracted_specs:
            return None
        
        filters = {}
        specs = line_item.extracted_specs
        
        # Material filter
        if specs.material_grade:
            # Extract base material (e.g., "Aluminum" from "Aluminum 6061")
            material_lower = specs.material_grade.lower()
            if "aluminum" in material_lower or "aluminium" in material_lower:
                filters["material"] = "Aluminum"
            elif "stainless" in material_lower:
                filters["material"] = "Stainless Steel"
            elif "titanium" in material_lower:
                filters["material"] = "Titanium"
            elif "steel" in material_lower and "stainless" not in material_lower:
                if "carbon" in material_lower:
                    filters["material"] = "Carbon Steel"
                else:
                    filters["material"] = "Steel"
            elif "brass" in material_lower:
                filters["material"] = "Brass"
            elif "copper" in material_lower:
                filters["material"] = "Copper"
        
        # Category filter based on form
        if specs.form:
            form_lower = specs.form.lower()
            if "sheet" in form_lower:
                filters["category"] = "Sheet"
            elif "plate" in form_lower:
                filters["category"] = "Plate"
            elif "bar" in form_lower or "rod" in form_lower:
                filters["category"] = "Bar"
            elif "tube" in form_lower or "pipe" in form_lower:
                filters["category"] = "Tube"
            elif "angle" in form_lower:
                filters["category"] = "Angle"
        
        return filters if filters else None
    
    def _create_material_filters(self, line_item: LineItem) -> Optional[Dict[str, Any]]:
        """Create material-only filters for broader search"""
        
        filters = self._create_filters(line_item)
        
        # Remove category filter to broaden search
        if filters and "category" in filters:
            del filters["category"]
        
        return filters
    
    def _merge_and_rank_results(self, search_results: List[Dict[str, Any]], 
                               line_item: LineItem) -> List[Dict[str, Any]]:
        """Merge results from multiple search strategies and rank them"""
        
        # Collect all unique results
        all_results = {}  # part_number -> result with best score
        strategy_weights = {
            "full_spec": 1.0,
            "material_form": 0.8,
            "with_specs": 0.9,
            "alternative_1": 0.7,
            "alternative_2": 0.6,
            "alternative_3": 0.5,
            "dimensional": 0.6,
            "material_only": 0.4,
            "raw_text": 0.3
        }
        
        for search_result in search_results:
            if isinstance(search_result, Exception) or not search_result.get("success"):
                continue
            
            strategy = search_result["strategy"]
            weight = strategy_weights.get(strategy, 0.5)
            
            for result in search_result["results"]:
                part_number = result.get("part_number")
                if not part_number:
                    continue
                
                # Calculate weighted score
                original_score = result.get("scores", {}).get("combined_score", 0)
                weighted_score = original_score * weight
                
                # Keep the best scoring result for each part
                if part_number not in all_results or weighted_score > all_results[part_number]["weighted_score"]:
                    result_copy = result.copy()
                    result_copy["weighted_score"] = weighted_score
                    result_copy["found_by_strategy"] = strategy
                    result_copy["original_score"] = original_score
                    all_results[part_number] = result_copy
        
        # Sort by weighted score
        sorted_results = sorted(all_results.values(), 
                              key=lambda x: x["weighted_score"], 
                              reverse=True)
        
        # Limit to top results
        return sorted_results[:15]
    
    def _format_search_results(self, merged_results: List[Dict[str, Any]], 
                             line_item: LineItem) -> List[SearchResult]:
        """Format merged results into SearchResult objects"""
        
        formatted_results = []
        
        for i, result in enumerate(merged_results):
            # Determine match confidence based on score and strategy
            confidence = self._calculate_match_confidence(
                result["weighted_score"], 
                result["found_by_strategy"],
                result,
                line_item
            )
            
            # Analyze specification matches
            spec_match = self._analyze_spec_match(result, line_item)
            
            search_result = SearchResult(
                rank=i + 1,
                part_number=result["part_number"],
                description=result["description"],
                similarity_score=result["weighted_score"],
                spec_match=spec_match,
                availability=result.get("availability"),
                unit_price=result.get("unit_price"),
                supplier=result.get("supplier"),
                match_confidence=confidence,
                notes=[f"Found by: {result['found_by_strategy']}"]
            )
            
            formatted_results.append(search_result)
        
        return formatted_results
    
    def _calculate_match_confidence(self, score: float, strategy: str, 
                                  result: Dict[str, Any], line_item: LineItem) -> MatchConfidence:
        """Calculate match confidence based on multiple factors"""
        
        # Base confidence from score
        if score >= 0.9:
            base_confidence = "high"
        elif score >= 0.75:
            base_confidence = "medium-high"
        elif score >= 0.6:
            base_confidence = "medium"
        elif score >= 0.4:
            base_confidence = "medium-low"
        else:
            base_confidence = "low"
        
        # Adjust based on strategy
        strategy_confidence_boost = {
            "full_spec": 0,
            "material_form": 0,
            "with_specs": 0,
            "alternative_1": -1,
            "dimensional": -1,
            "material_only": -2,
            "raw_text": -2
        }
        
        confidence_levels = ["low", "medium-low", "medium", "medium-high", "high"]
        current_index = confidence_levels.index(base_confidence)
        boost = strategy_confidence_boost.get(strategy, 0)
        
        new_index = max(0, min(len(confidence_levels) - 1, current_index + boost))
        
        return MatchConfidence(confidence_levels[new_index])
    
    def _analyze_spec_match(self, result: Dict[str, Any], 
                          line_item: LineItem) -> Dict[str, str]:
        """Analyze how well the result matches the line item specifications"""
        
        spec_match = {}
        
        if not line_item.extracted_specs:
            return {"overall": "unknown"}
        
        specs = line_item.extracted_specs
        result_desc = result.get("description", "").lower()
        result_material = result.get("material", "").lower()
        
        # Material match
        if specs.material_grade:
            spec_material = specs.material_grade.lower()
            if spec_material in result_material or spec_material in result_desc:
                spec_match["material"] = "exact_match"
            elif any(word in result_material for word in spec_material.split()):
                spec_match["material"] = "partial_match"
            else:
                spec_match["material"] = "different"
        else:
            spec_match["material"] = "not_specified"
        
        # Form match
        if specs.form:
            spec_form = specs.form.lower()
            if spec_form in result_desc:
                spec_match["form"] = "exact_match"
            elif any(synonym in result_desc for synonym in self._get_form_synonyms(spec_form)):
                spec_match["form"] = "equivalent"
            else:
                spec_match["form"] = "different"
        else:
            spec_match["form"] = "not_specified"
        
        # Dimensions match (basic check)
        if specs.dimensions:
            # This is a simplified check - could be enhanced
            has_dimension_match = False
            for dim_key, dim_value in specs.dimensions.items():
                if str(dim_value) in result_desc:
                    has_dimension_match = True
                    break
            
            spec_match["dimensions"] = "match_found" if has_dimension_match else "no_match"
        else:
            spec_match["dimensions"] = "not_specified"
        
        return spec_match
    
    def _get_form_synonyms(self, form: str) -> List[str]:
        """Get synonyms for form factors"""
        
        synonyms = {
            "sheet": ["plate", "panel"],
            "plate": ["sheet", "slab"],
            "bar": ["rod", "stick"],
            "rod": ["bar", "round"],
            "tube": ["pipe", "tubing"],
            "pipe": ["tube", "tubing"],
            "angle": ["l-shape", "corner"]
        }
        
        return synonyms.get(form.lower(), [])
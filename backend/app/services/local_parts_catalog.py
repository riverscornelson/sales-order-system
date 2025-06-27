"""
Local Parts Catalog Service
Uses SQLite database for parts catalog operations
"""

import asyncio
import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

from ..database.connection_pool import get_secure_db_manager, SecureDatabaseManager
from .embeddings import PartEmbeddingService

logger = structlog.get_logger()

class LocalPartsCatalogService:
    """Service for managing parts catalog using local SQLite database"""
    
    def __init__(self):
        self.db_manager: SecureDatabaseManager = get_secure_db_manager()
        self.embedding_service = PartEmbeddingService()
    
    async def search_parts(self, query: str, 
                          filters: Optional[Dict[str, Any]] = None,
                          top_k: int = 50) -> List[Dict[str, Any]]:
        """Search for parts using multiple strategies"""
        
        try:
            logger.info("Searching parts", 
                       query=query, 
                       filters=filters,
                       top_k=top_k)
            
            # Strategy 1: Direct part number search
            direct_matches = self._search_by_part_number(query)
            
            # Strategy 2: Full-text search
            fts_matches = self._search_full_text(query, top_k)
            
            # Strategy 3: Description-based search
            desc_matches = self._search_by_description(query, top_k)
            
            # Strategy 4: Category/material filtering
            filtered_matches = self._search_with_filters(query, filters, top_k)
            
            # Combine and score results
            all_matches = self._combine_and_score_results(
                query, direct_matches, fts_matches, desc_matches, filtered_matches
            )
            
            # Apply additional filters
            if filters:
                all_matches = self._apply_filters(all_matches, filters)
            
            # Sort by combined score and limit results
            all_matches.sort(key=lambda x: x.get("scores", {}).get("combined_score", 0), reverse=True)
            
            final_results = all_matches[:top_k]
            
            logger.info("Parts search completed", 
                       query=query,
                       results_count=len(final_results))
            
            return final_results
            
        except Exception as e:
            logger.error("Parts search failed", query=query, error=str(e))
            return []
    
    def _search_by_part_number(self, query: str) -> List[Dict[str, Any]]:
        """Search for exact or partial part number matches"""
        try:
            # Try exact match first using secure method
            exact_match = self.db_manager.get_part_by_number_safe(query.strip())
            if exact_match:
                exact_match["match_type"] = "exact_part_number"
                exact_match["base_score"] = 1.0
                return [exact_match]
            
            # Try partial matches
            search_query = """
            SELECT * FROM parts_catalog 
            WHERE part_number LIKE ? AND active = 1
            ORDER BY 
                CASE 
                    WHEN part_number = ? THEN 1
                    WHEN part_number LIKE ? THEN 2
                    ELSE 3
                END,
                part_number ASC
            LIMIT 20
            """
            
            partial_term = f"%{query.strip()}%"
            exact_term = query.strip()
            starts_with = f"{query.strip()}%"
            
            result = self.db_manager.execute_query(
                search_query, (partial_term, exact_term, starts_with), validate_table='parts_catalog'
            )
            results = result.rows
            
            for result in results:
                result["match_type"] = "partial_part_number"
                result["base_score"] = 0.8
            
            return results
            
        except Exception as e:
            logger.warning("Part number search failed", error=str(e))
            return []
    
    def _search_full_text(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search using SQLite FTS (Full-Text Search)"""
        try:
            # Use secure full-text search
            result = self.db_manager.search_parts_full_text_safe(query, limit)
            results = result.rows
            
            for result in results:
                result["match_type"] = "full_text"
                result["base_score"] = 0.7
            
            return results
            
        except Exception as e:
            logger.warning("Full-text search failed", error=str(e))
            return []
    
    def _search_by_description(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search by description using LIKE queries"""
        try:
            result = self.db_manager.execute_safe_search(query, 'parts_catalog', limit=limit)
            results = result.rows
            
            for result in results:
                result["match_type"] = "description"
                result["base_score"] = 0.6
            
            return results
            
        except Exception as e:
            logger.warning("Description search failed", error=str(e))
            return []
    
    def _search_with_filters(self, query: str, filters: Optional[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        """Search with category, material, or other filters"""
        try:
            if not filters:
                return []
            
            conditions = ["active = 1"]
            params = []
            
            # Build WHERE conditions based on filters
            if filters.get("category"):
                conditions.append("category = ?")
                params.append(filters["category"])
            
            if filters.get("material"):
                conditions.append("material LIKE ?")
                params.append(f"%{filters['material']}%")
            
            if filters.get("availability_status"):
                conditions.append("availability_status = ?")
                params.append(filters["availability_status"])
            
            if filters.get("price_range"):
                price_range = filters["price_range"]
                if price_range.get("min"):
                    conditions.append("list_price >= ?")
                    params.append(price_range["min"])
                if price_range.get("max"):
                    conditions.append("list_price <= ?")
                    params.append(price_range["max"])
            
            # Add query terms to description search
            if query.strip():
                conditions.append("description LIKE ?")
                params.append(f"%{query.strip()}%")
            
            search_query = f"""
            SELECT * FROM parts_catalog 
            WHERE {' AND '.join(conditions)}
            ORDER BY list_price ASC
            LIMIT ?
            """
            params.append(limit)
            
            results = self.db_manager.execute_query(search_query, tuple(params))
            
            for result in results:
                result["match_type"] = "filtered"
                result["base_score"] = 0.5
            
            return results
            
        except Exception as e:
            logger.warning("Filtered search failed", error=str(e))
            return []
    
    def _combine_and_score_results(self, query: str, *result_sets) -> List[Dict[str, Any]]:
        """Combine results from different search strategies and calculate scores"""
        
        # Deduplicate by part number
        seen_parts = {}
        
        for result_set in result_sets:
            for part in result_set:
                part_number = part.get("part_number")
                if not part_number:
                    continue
                
                if part_number not in seen_parts:
                    # Calculate comprehensive scores
                    scores = self._calculate_part_scores(query, part)
                    part["scores"] = scores
                    seen_parts[part_number] = part
                else:
                    # Boost score for parts found in multiple strategies
                    existing_part = seen_parts[part_number]
                    boost = 0.1
                    if "scores" in existing_part:
                        existing_part["scores"]["combined_score"] += boost
        
        return list(seen_parts.values())
    
    def _calculate_part_scores(self, query: str, part: Dict[str, Any]) -> Dict[str, float]:
        """Calculate comprehensive scoring for a part"""
        
        query_lower = query.lower()
        part_number = str(part.get("part_number", "")).lower()
        description = str(part.get("description", "")).lower()
        material = str(part.get("material", "")).lower()
        keywords = str(part.get("keywords", "")).lower()
        
        scores = {
            "part_number_score": 0.0,
            "description_score": 0.0,
            "material_score": 0.0,
            "keyword_score": 0.0,
            "availability_score": 0.0,
            "specification_score": 0.0,
            "base_score": part.get("base_score", 0.0)
        }
        
        # Part number scoring
        if query_lower == part_number:
            scores["part_number_score"] = 1.0
        elif query_lower in part_number:
            scores["part_number_score"] = 0.8
        elif part_number.startswith(query_lower):
            scores["part_number_score"] = 0.7
        elif any(word in part_number for word in query_lower.split()):
            scores["part_number_score"] = 0.5
        
        # Description scoring
        query_words = set(query_lower.split())
        desc_words = set(description.split())
        common_words = query_words & desc_words
        
        if common_words:
            scores["description_score"] = len(common_words) / len(query_words)
        
        # Material scoring
        if any(word in material for word in query_words):
            scores["material_score"] = 0.8
        
        # Keywords scoring
        if any(word in keywords for word in query_words):
            scores["keyword_score"] = 0.6
        
        # Availability scoring (prefer in-stock items)
        availability = part.get("availability_status", "").lower()
        if availability == "in_stock":
            scores["availability_score"] = 1.0
        elif availability == "limited":
            scores["availability_score"] = 0.7
        elif availability == "special_order":
            scores["availability_score"] = 0.5
        
        # Specification scoring (for dimensional matches)
        scores["specification_score"] = self._calculate_specification_score(query, part)
        
        # Combined score with weights
        combined_score = (
            scores["part_number_score"] * 0.25 +
            scores["description_score"] * 0.20 +
            scores["material_score"] * 0.15 +
            scores["keyword_score"] * 0.10 +
            scores["availability_score"] * 0.10 +
            scores["specification_score"] * 0.10 +
            scores["base_score"] * 0.10
        )
        
        scores["combined_score"] = combined_score
        
        return scores
    
    def _calculate_specification_score(self, query: str, part: Dict[str, Any]) -> float:
        """Calculate score based on specification matches"""
        
        try:
            # Extract numbers from query
            query_numbers = [float(match) for match in re.findall(r'\d+\.?\d*', query)]
            if not query_numbers:
                return 0.0
            
            score = 0.0
            dimensional_fields = [
                'diameter_inches', 'length_inches', 'width_inches', 
                'height_inches', 'thickness_inches'
            ]
            
            for field in dimensional_fields:
                if part.get(field) and part[field] in query_numbers:
                    score += 0.2
            
            # Check material grades
            material_grade = part.get("material_grade", "")
            if material_grade:
                grade_numbers = re.findall(r'\d+', material_grade)
                for grade_num in grade_numbers:
                    if float(grade_num) in query_numbers:
                        score += 0.2
            
            return min(score, 1.0)
            
        except Exception:
            return 0.0
    
    def _apply_filters(self, parts: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply additional filters to search results"""
        
        filtered_parts = []
        
        for part in parts:
            include_part = True
            
            # Category filter
            if filters.get("category") and part.get("category") != filters["category"]:
                include_part = False
            
            # Material filter
            if filters.get("material") and filters["material"].lower() not in part.get("material", "").lower():
                include_part = False
            
            # Availability filter
            if filters.get("availability_status") and part.get("availability_status") != filters["availability_status"]:
                include_part = False
            
            # Price range filter
            if filters.get("price_range"):
                price = part.get("list_price", 0)
                price_range = filters["price_range"]
                if price_range.get("min") and price < price_range["min"]:
                    include_part = False
                if price_range.get("max") and price > price_range["max"]:
                    include_part = False
            
            # In stock filter
            if filters.get("in_stock_only") and part.get("availability_status") != "IN_STOCK":
                include_part = False
            
            if include_part:
                filtered_parts.append(part)
        
        return filtered_parts
    
    async def get_part_details(self, part_number: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific part"""
        
        try:
            part = self.db_manager.get_part_by_number(part_number)
            if part:
                # Add additional computed fields
                part["weight_kg"] = part.get("weight_lbs", 0) * 0.453592 if part.get("weight_lbs") else None
                part["volume_cubic_inches"] = self._calculate_volume(part)
                part["availability_text"] = self._get_availability_text(part)
                
            return part
            
        except Exception as e:
            logger.error("Failed to get part details", 
                        part_number=part_number,
                        error=str(e))
            return None
    
    def _calculate_volume(self, part: Dict[str, Any]) -> Optional[float]:
        """Calculate volume from dimensions"""
        try:
            length = part.get("length_inches")
            width = part.get("width_inches") 
            height = part.get("height_inches")
            diameter = part.get("diameter_inches")
            
            if diameter and length:
                # Cylindrical volume
                radius = diameter / 2
                return 3.14159 * radius * radius * length
            elif length and width and height:
                # Rectangular volume
                return length * width * height
            
            return None
        except Exception:
            return None
    
    def _get_availability_text(self, part: Dict[str, Any]) -> str:
        """Get human-readable availability text"""
        status = part.get("availability_status", "").upper()
        quantity = part.get("quantity_on_hand", 0)
        lead_time = part.get("lead_time_days", 0)
        
        if status == "IN_STOCK":
            return f"In Stock ({quantity} available)"
        elif status == "LIMITED":
            return f"Limited Stock ({quantity} available)"
        elif status == "BACKORDER":
            return f"Backorder ({lead_time} days lead time)"
        elif status == "SPECIAL_ORDER":
            return f"Special Order ({lead_time} days lead time)"
        elif status == "DISCONTINUED":
            return "Discontinued"
        else:
            return f"Status: {status}"
    
    async def get_catalog_stats(self) -> Dict[str, Any]:
        """Get statistics about the parts catalog"""
        
        try:
            stats = self.db_manager.get_database_stats()
            stats["last_updated"] = datetime.now().isoformat()
            return stats
            
        except Exception as e:
            logger.error("Failed to get catalog stats", error=str(e))
            return {}
    
    def get_categories(self) -> List[Dict[str, Any]]:
        """Get all available categories"""
        try:
            return self.db_manager.get_categories()
        except Exception as e:
            logger.error("Failed to get categories", error=str(e))
            return []
    
    def get_materials(self) -> List[str]:
        """Get all available materials"""
        try:
            return self.db_manager.get_materials()
        except Exception as e:
            logger.error("Failed to get materials", error=str(e))
            return []
    
    async def check_health(self) -> Dict[str, Any]:
        """Check the health of the parts catalog service"""
        
        try:
            # Test database connection
            stats = self.db_manager.get_database_stats()
            
            health_status = {
                "status": "healthy",
                "database": {
                    "connected": True,
                    "total_parts": stats.get("total_parts", 0)
                },
                "timestamp": datetime.now().isoformat()
            }
            
            return health_status
            
        except Exception as e:
            logger.error("Parts catalog health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
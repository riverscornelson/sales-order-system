import os
import csv
import json
from typing import List, Dict, Any, Optional
import asyncio
import structlog
from datetime import datetime

from .embeddings import PartEmbeddingService
from .vector_store import PartsCatalogVectorStore

logger = structlog.get_logger()

class PartsCatalogService:
    """Service for managing and indexing parts catalog"""
    
    def __init__(self):
        self.embedding_service = PartEmbeddingService()
        self.vector_store = PartsCatalogVectorStore()
        
        # Mock data for development
        self.mock_parts = self._create_mock_parts_catalog()
    
    def _create_mock_parts_catalog(self) -> List[Dict[str, Any]]:
        """Create mock parts catalog for development"""
        
        return [
            {
                "part_number": "ST-304-12x8x0.25",
                "description": "Stainless Steel 304 Sheet, 12\" x 8\" x 0.25\" thick",
                "category": "Sheet Metal",
                "material": "Stainless Steel 304",
                "specifications": {
                    "length": 12.0,
                    "width": 8.0,
                    "thickness": 0.25,
                    "grade": "304",
                    "finish": "2B",
                    "units": "inches"
                },
                "unit_price": 45.50,
                "availability": 150,
                "supplier": "MetalCorp Inc",
                "weight_per_unit": 8.2,
                "minimum_order": 1
            },
            {
                "part_number": "AL-6061-10x6x0.5",
                "description": "Aluminum 6061 Plate, 10\" x 6\" x 0.5\" thick",
                "category": "Plate",
                "material": "Aluminum 6061",
                "specifications": {
                    "length": 10.0,
                    "width": 6.0,
                    "thickness": 0.5,
                    "grade": "6061-T6",
                    "finish": "Mill",
                    "units": "inches"
                },
                "unit_price": 32.75,
                "availability": 200,
                "supplier": "AlumTech Supply",
                "weight_per_unit": 4.8,
                "minimum_order": 5
            },
            {
                "part_number": "CS-1018-8x4x0.375",
                "description": "Carbon Steel 1018 Bar, 8\" x 4\" x 0.375\" thick",
                "category": "Bar Stock",
                "material": "Carbon Steel 1018",
                "specifications": {
                    "length": 8.0,
                    "width": 4.0,
                    "thickness": 0.375,
                    "grade": "1018",
                    "finish": "Hot Rolled",
                    "units": "inches"
                },
                "unit_price": 18.25,
                "availability": 300,
                "supplier": "SteelWorks LLC",
                "weight_per_unit": 6.1,
                "minimum_order": 10
            },
            {
                "part_number": "TI-6AL4V-ROD-1.0x12",
                "description": "Titanium 6Al-4V Round Rod, 1.0\" diameter x 12\" length",
                "category": "Rod",
                "material": "Titanium 6Al-4V",
                "specifications": {
                    "diameter": 1.0,
                    "length": 12.0,
                    "grade": "Grade 5",
                    "condition": "Annealed",
                    "units": "inches"
                },
                "unit_price": 185.00,
                "availability": 25,
                "supplier": "TitaniumPro",
                "weight_per_unit": 1.8,
                "minimum_order": 1
            },
            {
                "part_number": "BR-C360-HEX-0.75x6",
                "description": "Brass C360 Hexagonal Bar, 0.75\" across flats x 6\" length",
                "category": "Hex Bar",
                "material": "Brass C360",
                "specifications": {
                    "across_flats": 0.75,
                    "length": 6.0,
                    "grade": "C360",
                    "finish": "Free Cutting",
                    "units": "inches"
                },
                "unit_price": 28.40,
                "availability": 80,
                "supplier": "BrassCraft",
                "weight_per_unit": 2.2,
                "minimum_order": 5
            },
            {
                "part_number": "ST-316L-TUBE-2x1x0.125",
                "description": "Stainless Steel 316L Square Tube, 2\" x 1\" x 0.125\" wall",
                "category": "Tubing",
                "material": "Stainless Steel 316L",
                "specifications": {
                    "outer_width": 2.0,
                    "outer_height": 1.0,
                    "wall_thickness": 0.125,
                    "grade": "316L",
                    "finish": "Polished",
                    "units": "inches"
                },
                "unit_price": 52.80,
                "availability": 45,
                "supplier": "TubeTech Industries",
                "weight_per_unit": 3.4,
                "minimum_order": 2
            },
            {
                "part_number": "CU-110-SHEET-12x12x0.062",
                "description": "Copper 110 Sheet, 12\" x 12\" x 0.062\" thick",
                "category": "Sheet Metal",
                "material": "Copper 110",
                "specifications": {
                    "length": 12.0,
                    "width": 12.0,
                    "thickness": 0.062,
                    "grade": "110",
                    "temper": "Soft",
                    "units": "inches"
                },
                "unit_price": 67.25,
                "availability": 95,
                "supplier": "CopperSource",
                "weight_per_unit": 12.8,
                "minimum_order": 1
            },
            {
                "part_number": "AL-2024-ANGLE-2x2x0.125",
                "description": "Aluminum 2024 Angle, 2\" x 2\" x 0.125\" thick",
                "category": "Angle",
                "material": "Aluminum 2024",
                "specifications": {
                    "leg1": 2.0,
                    "leg2": 2.0,
                    "thickness": 0.125,
                    "grade": "2024-T3",
                    "finish": "Clad",
                    "units": "inches"
                },
                "unit_price": 38.90,
                "availability": 120,
                "supplier": "AeroMetal Supply",
                "weight_per_unit": 2.1,
                "minimum_order": 3
            }
        ]
    
    async def initialize_catalog(self, force_reindex: bool = False) -> bool:
        """Initialize the parts catalog with embeddings"""
        
        logger.info("Initializing parts catalog", force_reindex=force_reindex)
        
        try:
            # Check if catalog already exists
            stats = await self.vector_store.get_collection_stats()
            
            if stats.get("count", 0) > 0 and not force_reindex:
                logger.info("Parts catalog already initialized", 
                           count=stats["count"])
                return True
            
            # Index all parts
            indexed_count = 0
            
            for part in self.mock_parts:
                success = await self.index_part(part)
                if success:
                    indexed_count += 1
                else:
                    logger.warning("Failed to index part", 
                                 part_number=part.get("part_number"))
            
            logger.info("Parts catalog initialization completed", 
                       total_parts=len(self.mock_parts),
                       indexed_parts=indexed_count)
            
            return indexed_count > 0
            
        except Exception as e:
            logger.error("Failed to initialize parts catalog", error=str(e))
            return False
    
    async def index_part(self, part_data: Dict[str, Any]) -> bool:
        """Index a single part in the vector store"""
        
        try:
            # Generate embedding for the part
            embedding = await self.embedding_service.create_part_embedding(part_data)
            
            if not embedding:
                logger.error("Failed to generate embedding", 
                           part_number=part_data.get("part_number"))
                return False
            
            # Store in vector store
            success = await self.vector_store.index_part(part_data, embedding)
            
            if success:
                logger.debug("Indexed part", 
                           part_number=part_data.get("part_number"))
            
            return success
            
        except Exception as e:
            logger.error("Failed to index part", 
                        part_number=part_data.get("part_number"),
                        error=str(e))
            return False
    
    async def search_parts(self, query: str, 
                          filters: Optional[Dict[str, Any]] = None,
                          top_k: int = 10) -> List[Dict[str, Any]]:
        """Search for parts using semantic search"""
        
        try:
            logger.info("Searching parts", 
                       query=query, 
                       filters=filters,
                       top_k=top_k)
            
            # Create context from filters for better embeddings
            context = {}
            if filters:
                if filters.get("material"):
                    context["material_hints"] = [filters["material"]]
                if filters.get("dimensions"):
                    context["dimensions"] = filters["dimensions"]
            
            # Generate query embedding
            query_embedding = await self.embedding_service.create_query_embedding(
                query, context
            )
            
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []
            
            # Search vector store
            results = await self.vector_store.search_parts(
                query_embedding, 
                filters,
                top_k,
                min_similarity=0.5
            )
            
            # Enhance results with additional scoring
            enhanced_results = []
            
            for result in results:
                metadata = result.get("metadata", {})
                
                # Calculate additional scores
                text_similarity = self._calculate_text_similarity(query, metadata)
                spec_match = self._calculate_spec_match(query, metadata)
                
                # Combined score
                vector_score = result.get("similarity", 0.0)
                combined_score = (
                    vector_score * 0.6 + 
                    text_similarity * 0.25 + 
                    spec_match * 0.15
                )
                
                enhanced_result = {
                    "part_number": metadata.get("part_number"),
                    "description": metadata.get("description"),
                    "material": metadata.get("material"),
                    "category": metadata.get("category"),
                    "specifications": metadata.get("specifications", {}),
                    "unit_price": metadata.get("unit_price"),
                    "availability": metadata.get("availability"),
                    "supplier": metadata.get("supplier"),
                    "scores": {
                        "vector_similarity": vector_score,
                        "text_similarity": text_similarity,
                        "spec_match": spec_match,
                        "combined_score": combined_score
                    }
                }
                
                enhanced_results.append(enhanced_result)
            
            # Sort by combined score
            enhanced_results.sort(key=lambda x: x["scores"]["combined_score"], reverse=True)
            
            logger.info("Parts search completed", 
                       query=query,
                       results_count=len(enhanced_results))
            
            return enhanced_results
            
        except Exception as e:
            logger.error("Parts search failed", query=query, error=str(e))
            return []
    
    def _calculate_text_similarity(self, query: str, metadata: Dict[str, Any]) -> float:
        """Calculate text-based similarity score"""
        
        query_lower = query.lower()
        score = 0.0
        
        # Check part number match
        part_number = metadata.get("part_number", "").lower()
        if query_lower in part_number or part_number in query_lower:
            score += 0.4
        
        # Check description match
        description = metadata.get("description", "").lower()
        common_words = set(query_lower.split()) & set(description.split())
        if common_words:
            score += len(common_words) / len(query_lower.split()) * 0.3
        
        # Check material match
        material = metadata.get("material", "").lower()
        if any(word in material for word in query_lower.split()):
            score += 0.3
        
        return min(score, 1.0)
    
    def _calculate_spec_match(self, query: str, metadata: Dict[str, Any]) -> float:
        """Calculate specification-based match score"""
        
        specs = metadata.get("specifications", {})
        if not specs:
            return 0.0
        
        query_lower = query.lower()
        score = 0.0
        
        # Extract numbers from query for dimension matching
        import re
        query_numbers = [float(m) for m in re.findall(r'\d+\.?\d*', query)]
        
        # Check if any spec values match query numbers
        for spec_key, spec_value in specs.items():
            if isinstance(spec_value, (int, float)):
                if spec_value in query_numbers:
                    score += 0.2
        
        # Check grade/material specifications
        grade_keywords = ['304', '316', '6061', '1018', '2024', 'grade']
        for keyword in grade_keywords:
            if keyword in query_lower:
                for spec_value in specs.values():
                    if isinstance(spec_value, str) and keyword in spec_value.lower():
                        score += 0.3
                        break
        
        return min(score, 1.0)
    
    async def get_part_details(self, part_number: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific part"""
        
        try:
            # First check vector store
            part_data = await self.vector_store.get_part_by_number(part_number)
            
            if part_data:
                return part_data.get("metadata")
            
            # Fallback to mock data
            for part in self.mock_parts:
                if part.get("part_number") == part_number:
                    return part
            
            return None
            
        except Exception as e:
            logger.error("Failed to get part details", 
                        part_number=part_number,
                        error=str(e))
            return None
    
    async def get_catalog_stats(self) -> Dict[str, Any]:
        """Get statistics about the parts catalog"""
        
        try:
            vector_stats = await self.vector_store.get_collection_stats()
            
            # Additional stats from mock data
            categories = set()
            materials = set()
            total_value = 0.0
            
            for part in self.mock_parts:
                if part.get("category"):
                    categories.add(part["category"])
                if part.get("material"):
                    materials.add(part["material"])
                if part.get("unit_price") and part.get("availability"):
                    total_value += part["unit_price"] * part["availability"]
            
            stats = {
                "vector_store": vector_stats,
                "total_parts": len(self.mock_parts),
                "categories": list(categories),
                "materials": list(materials),
                "total_inventory_value": total_value,
                "last_updated": datetime.now().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error("Failed to get catalog stats", error=str(e))
            return {}
    
    async def load_catalog_from_csv(self, file_path: str) -> bool:
        """Load parts catalog from CSV file"""
        
        try:
            parts = []
            
            with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    # Convert numeric fields
                    for field in ['unit_price', 'availability', 'weight_per_unit', 'minimum_order']:
                        if row.get(field):
                            try:
                                row[field] = float(row[field])
                            except ValueError:
                                pass
                    
                    # Parse specifications if present
                    if row.get('specifications'):
                        try:
                            row['specifications'] = json.loads(row['specifications'])
                        except json.JSONDecodeError:
                            row['specifications'] = {}
                    
                    parts.append(row)
            
            # Index all parts
            indexed_count = 0
            for part in parts:
                success = await self.index_part(part)
                if success:
                    indexed_count += 1
            
            logger.info("Loaded catalog from CSV", 
                       file_path=file_path,
                       total_parts=len(parts),
                       indexed_parts=indexed_count)
            
            return indexed_count > 0
            
        except Exception as e:
            logger.error("Failed to load catalog from CSV", 
                        file_path=file_path,
                        error=str(e))
            return False
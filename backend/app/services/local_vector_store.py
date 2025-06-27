import os
import json
import pickle
from typing import List, Dict, Any, Optional
import asyncio
import structlog
import numpy as np
from datetime import datetime
from pathlib import Path

logger = structlog.get_logger()

class LocalVectorStore:
    """Local file-based vector storage for development"""
    
    def __init__(self, storage_dir: str = "data/vectors"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache for fast access
        self._vector_cache = {}
        self._cache_loaded = False
        
        logger.info("Initialized local vector store", storage_dir=str(self.storage_dir))
    
    def _get_collection_path(self, collection_name: str) -> Path:
        """Get file path for a collection"""
        return self.storage_dir / f"{collection_name}.json"
    
    async def store_vectors(self, vectors: List[Dict[str, Any]], 
                           collection_name: str = "parts_catalog") -> bool:
        """Store vectors with metadata to local file"""
        
        try:
            # Prepare data structure
            vector_data = {
                "collection_name": collection_name,
                "created_at": datetime.now().isoformat(),
                "count": len(vectors),
                "vectors": vectors
            }
            
            # Store to local file
            file_path = self._get_collection_path(collection_name)
            
            with open(file_path, 'w') as f:
                json.dump(vector_data, f, default=str, indent=2)
            
            # Update cache
            self._vector_cache[collection_name] = vectors
            
            logger.info("Stored vectors locally", 
                       collection=collection_name,
                       count=len(vectors),
                       file=str(file_path))
            
            return True
            
        except Exception as e:
            logger.error("Failed to store vectors", 
                        collection=collection_name,
                        error=str(e))
            return False
    
    async def load_vectors(self, collection_name: str = "parts_catalog") -> List[Dict[str, Any]]:
        """Load vectors from local file with caching"""
        
        # Check cache first
        if collection_name in self._vector_cache:
            return self._vector_cache[collection_name]
        
        try:
            file_path = self._get_collection_path(collection_name)
            
            if not file_path.exists():
                logger.warning("Vector collection not found", 
                             collection=collection_name,
                             file=str(file_path))
                return []
            
            # Load and parse
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            vectors = data.get("vectors", [])
            
            # Cache the results
            self._vector_cache[collection_name] = vectors
            
            logger.info("Loaded vectors from local file", 
                       collection=collection_name,
                       count=len(vectors))
            
            return vectors
            
        except Exception as e:
            logger.error("Failed to load vectors", 
                        collection=collection_name,
                        error=str(e))
            return []
    
    async def search_similar(self, query_vector: List[float], 
                           collection_name: str = "parts_catalog",
                           top_k: int = 10,
                           min_similarity: float = 0.5) -> List[Dict[str, Any]]:
        """Search for similar vectors"""
        
        # Load vectors if not cached
        vectors = await self.load_vectors(collection_name)
        
        if not vectors:
            return []
        
        try:
            results = []
            query_vec = np.array(query_vector)
            
            for vector_data in vectors:
                stored_vector = vector_data.get("vector", [])
                if not stored_vector:
                    continue
                
                # Calculate cosine similarity
                stored_vec = np.array(stored_vector)
                similarity = self._cosine_similarity(query_vec, stored_vec)
                
                if similarity >= min_similarity:
                    result = {
                        "similarity": float(similarity),
                        "metadata": vector_data.get("metadata", {}),
                        "id": vector_data.get("id")
                    }
                    results.append(result)
            
            # Sort by similarity (descending) and limit results
            results.sort(key=lambda x: x["similarity"], reverse=True)
            results = results[:top_k]
            
            logger.debug("Vector search completed", 
                       collection=collection_name,
                       query_dims=len(query_vector),
                       candidates=len(vectors),
                       results=len(results))
            
            return results
            
        except Exception as e:
            logger.error("Vector search failed", 
                        collection=collection_name,
                        error=str(e))
            return []
    
    async def get_all_parts(self, collection_name: str = "parts_catalog") -> List[Dict[str, Any]]:
        """Get all parts metadata from vector store"""
        
        try:
            vectors = await self.load_vectors(collection_name)
            
            # Extract just the metadata (part information) from each vector
            parts = []
            for vector_data in vectors:
                metadata = vector_data.get("metadata", {})
                if metadata:
                    parts.append(metadata)
            
            logger.info("Retrieved all parts from vector store", 
                       collection=collection_name,
                       count=len(parts))
            
            return parts
            
        except Exception as e:
            logger.error("Failed to get all parts", 
                        collection=collection_name,
                        error=str(e))
            return []
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        
        try:
            # Handle zero vectors
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(np.dot(vec1, vec2) / (norm1 * norm2))
        except Exception:
            return 0.0
    
    async def add_vector(self, vector: List[float], metadata: Dict[str, Any],
                        vector_id: str, collection_name: str = "parts_catalog") -> bool:
        """Add a single vector to the collection"""
        
        try:
            # Load existing vectors
            vectors = await self.load_vectors(collection_name)
            
            # Create new vector entry
            new_vector = {
                "id": vector_id,
                "vector": vector,
                "metadata": metadata,
                "created_at": datetime.now().isoformat()
            }
            
            # Check for existing vector with same ID
            existing_index = None
            for i, vec in enumerate(vectors):
                if vec.get("id") == vector_id:
                    existing_index = i
                    break
            
            if existing_index is not None:
                # Update existing vector
                vectors[existing_index] = new_vector
                logger.debug("Updated existing vector", id=vector_id)
            else:
                # Add new vector
                vectors.append(new_vector)
                logger.debug("Added new vector", id=vector_id)
            
            # Store updated collection
            return await self.store_vectors(vectors, collection_name)
            
        except Exception as e:
            logger.error("Failed to add vector", 
                        id=vector_id,
                        collection=collection_name,
                        error=str(e))
            return False
    
    async def get_collection_stats(self, collection_name: str = "parts_catalog") -> Dict[str, Any]:
        """Get statistics about a vector collection"""
        
        try:
            vectors = await self.load_vectors(collection_name)
            
            if not vectors:
                return {
                    "collection_name": collection_name,
                    "count": 0,
                    "exists": False
                }
            
            # Calculate basic stats
            vector_dims = len(vectors[0].get("vector", [])) if vectors else 0
            
            # Get creation dates
            creation_dates = [
                v.get("created_at") for v in vectors 
                if v.get("created_at")
            ]
            
            stats = {
                "collection_name": collection_name,
                "count": len(vectors),
                "vector_dimensions": vector_dims,
                "exists": True,
                "first_created": min(creation_dates) if creation_dates else None,
                "last_created": max(creation_dates) if creation_dates else None
            }
            
            return stats
            
        except Exception as e:
            logger.error("Failed to get collection stats", 
                        collection=collection_name,
                        error=str(e))
            return {
                "collection_name": collection_name,
                "count": 0,
                "exists": False,
                "error": str(e)
            }
    
    async def clear_cache(self):
        """Clear the in-memory vector cache"""
        self._vector_cache.clear()
        self._cache_loaded = False
        logger.info("Cleared vector cache")


class LocalPartsCatalogVectorStore(LocalVectorStore):
    """Specialized local vector store for parts catalog"""
    
    def __init__(self, storage_dir: str = "data/vectors"):
        super().__init__(storage_dir)
        self.collection_name = "parts_catalog"
    
    async def index_part(self, part_data: Dict[str, Any], 
                        vector: List[float]) -> bool:
        """Index a single part with its vector"""
        
        part_id = part_data.get("part_number") or part_data.get("id")
        if not part_id:
            logger.error("Part ID required for indexing")
            return False
        
        metadata = {
            "part_number": part_data.get("part_number"),
            "description": part_data.get("description"),
            "category": part_data.get("category"),
            "material": part_data.get("material"),
            "specifications": part_data.get("specifications", {}),
            "unit_price": part_data.get("unit_price"),
            "availability": part_data.get("availability"),
            "supplier": part_data.get("supplier"),
            "indexed_at": datetime.now().isoformat()
        }
        
        return await self.add_vector(vector, metadata, part_id, self.collection_name)
    
    async def search_parts(self, query_vector: List[float], 
                          filters: Optional[Dict[str, Any]] = None,
                          top_k: int = 10,
                          min_similarity: float = 0.5) -> List[Dict[str, Any]]:
        """Search for parts with optional filtering"""
        
        # Get initial results from vector search
        results = await self.search_similar(
            query_vector, 
            self.collection_name, 
            top_k * 2,  # Get more results for filtering
            min_similarity
        )
        
        # Apply filters if provided
        if filters:
            filtered_results = []
            
            for result in results:
                metadata = result.get("metadata", {})
                
                # Apply filters
                passes_filter = True
                
                if filters.get("category") and metadata.get("category"):
                    if metadata["category"].lower() != filters["category"].lower():
                        passes_filter = False
                
                if filters.get("material") and metadata.get("material"):
                    if filters["material"].lower() not in metadata["material"].lower():
                        passes_filter = False
                
                if filters.get("max_price") and metadata.get("unit_price"):
                    if metadata["unit_price"] > filters["max_price"]:
                        passes_filter = False
                
                if filters.get("min_availability") and metadata.get("availability"):
                    if metadata["availability"] < filters["min_availability"]:
                        passes_filter = False
                
                if passes_filter:
                    filtered_results.append(result)
            
            results = filtered_results
        
        # Limit to requested number of results
        return results[:top_k]
    
    async def get_part_by_number(self, part_number: str) -> Optional[Dict[str, Any]]:
        """Get specific part by part number"""
        
        vectors = await self.load_vectors(self.collection_name)
        
        for vector_data in vectors:
            metadata = vector_data.get("metadata", {})
            if metadata.get("part_number") == part_number:
                return {
                    "id": vector_data.get("id"),
                    "metadata": metadata,
                    "vector": vector_data.get("vector")
                }
        
        return None
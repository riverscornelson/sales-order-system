import os
from typing import List, Dict, Any, Optional
import asyncio
import structlog
import numpy as np
from google.cloud import aiplatform
import openai
from openai import AsyncOpenAI

logger = structlog.get_logger()

class EmbeddingService:
    """Service for generating vector embeddings using multiple providers"""
    
    def __init__(self):
        self.provider = os.getenv('EMBEDDING_PROVIDER', 'openai').lower()
        
        if self.provider == 'vertex':
            self._init_vertex_ai()
        elif self.provider == 'openai':
            self._init_openai()
        else:
            raise ValueError(f"Unsupported embedding provider: {self.provider}")
    
    def _init_vertex_ai(self):
        """Initialize Vertex AI embeddings"""
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        location = os.getenv('VERTEX_AI_LOCATION', 'us-central1')
        
        if not project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable required for Vertex AI")
        
        aiplatform.init(project=project_id, location=location)
        self.model_name = "textembedding-gecko@003"
        self.dimensions = 768
        
        logger.info("Initialized Vertex AI embeddings", model=self.model_name)
    
    def _init_openai(self):
        """Initialize OpenAI embeddings"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable required for OpenAI embeddings")
        
        self.client = AsyncOpenAI(api_key=api_key)
        self.model_name = "text-embedding-3-large"
        self.dimensions = 3072
        
        logger.info("Initialized OpenAI embeddings", model=self.model_name)
    
    async def generate_embeddings(self, texts: List[str], 
                                 batch_size: int = 100) -> List[List[float]]:
        """Generate embeddings for a list of texts"""
        
        if not texts:
            return []
        
        logger.info("Generating embeddings", 
                   count=len(texts), 
                   provider=self.provider,
                   model=self.model_name)
        
        try:
            if self.provider == 'vertex':
                return await self._generate_vertex_embeddings(texts, batch_size)
            elif self.provider == 'openai':
                return await self._generate_openai_embeddings(texts, batch_size)
        except Exception as e:
            logger.error("Failed to generate embeddings", error=str(e))
            raise
    
    async def _generate_vertex_embeddings(self, texts: List[str], 
                                        batch_size: int) -> List[List[float]]:
        """Generate embeddings using Vertex AI"""
        
        from vertexai.language_models import TextEmbeddingModel
        
        model = TextEmbeddingModel.from_pretrained(self.model_name)
        all_embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            try:
                # Vertex AI batch embedding
                embeddings = model.get_embeddings(batch)
                batch_vectors = [emb.values for emb in embeddings]
                all_embeddings.extend(batch_vectors)
                
                logger.debug("Generated Vertex AI batch", 
                           batch_size=len(batch),
                           batch_num=i//batch_size + 1)
                
                # Rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error("Vertex AI batch failed", 
                           batch_start=i, 
                           batch_size=len(batch),
                           error=str(e))
                raise
        
        return all_embeddings
    
    async def _generate_openai_embeddings(self, texts: List[str], 
                                        batch_size: int) -> List[List[float]]:
        """Generate embeddings using OpenAI"""
        
        all_embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            try:
                response = await self.client.embeddings.create(
                    model=self.model_name,
                    input=batch,
                    encoding_format="float"
                )
                
                batch_vectors = [data.embedding for data in response.data]
                all_embeddings.extend(batch_vectors)
                
                logger.debug("Generated OpenAI batch", 
                           batch_size=len(batch),
                           batch_num=i//batch_size + 1)
                
                # Rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error("OpenAI batch failed", 
                           batch_start=i, 
                           batch_size=len(batch),
                           error=str(e))
                raise
        
        return all_embeddings
    
    async def generate_single_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        embeddings = await self.generate_embeddings([text])
        return embeddings[0] if embeddings else []
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        # Handle zero vectors
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(np.dot(v1, v2) / (norm1 * norm2))
    
    def find_most_similar(self, query_embedding: List[float], 
                         candidate_embeddings: List[List[float]], 
                         top_k: int = 5) -> List[Dict[str, Any]]:
        """Find most similar embeddings to query"""
        
        similarities = []
        
        for i, candidate in enumerate(candidate_embeddings):
            similarity = self.cosine_similarity(query_embedding, candidate)
            similarities.append({
                'index': i,
                'similarity': similarity
            })
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        return similarities[:top_k]


class PartEmbeddingService:
    """Specialized service for parts catalog embeddings"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
    
    async def create_part_embedding(self, part_data: Dict[str, Any]) -> List[float]:
        """Create embedding for a part using multiple fields"""
        
        # Combine multiple fields for richer embedding
        text_components = []
        
        # Part number
        if part_data.get('part_number'):
            text_components.append(f"Part: {part_data['part_number']}")
        
        # Description
        if part_data.get('description'):
            text_components.append(f"Description: {part_data['description']}")
        
        # Material
        if part_data.get('material'):
            text_components.append(f"Material: {part_data['material']}")
        
        # Specifications
        specs = part_data.get('specifications', {})
        for key, value in specs.items():
            if value:
                text_components.append(f"{key}: {value}")
        
        # Category/Type
        if part_data.get('category'):
            text_components.append(f"Category: {part_data['category']}")
        
        # Combine all components
        combined_text = " | ".join(text_components)
        
        return await self.embedding_service.generate_single_embedding(combined_text)
    
    async def create_query_embedding(self, query_text: str, 
                                   context: Optional[Dict[str, Any]] = None) -> List[float]:
        """Create embedding for search query with optional context"""
        
        # Enhance query with context if available
        enhanced_query = query_text
        
        if context:
            # Add quantity context
            if context.get('quantity'):
                enhanced_query += f" quantity {context['quantity']}"
            
            # Add material hints
            if context.get('material_hints'):
                enhanced_query += f" {' '.join(context['material_hints'])}"
            
            # Add dimension hints
            if context.get('dimensions'):
                enhanced_query += f" {context['dimensions']}"
        
        return await self.embedding_service.generate_single_embedding(enhanced_query)
    
    def normalize_part_description(self, description: str) -> str:
        """Normalize part description for better matching"""
        
        # Convert to lowercase
        desc = description.lower()
        
        # Common metal industry normalizations
        normalizations = {
            'stainless steel': 'ss',
            'carbon steel': 'cs',
            'aluminum': 'al',
            'aluminium': 'al',
            'steel': 'steel',
            'inch': 'in',
            'inches': 'in',
            'millimeter': 'mm',
            'millimeters': 'mm',
            'diameter': 'dia',
            'thickness': 'thick',
            'length': 'len',
            'width': 'width',
            'height': 'height',
        }
        
        for full_term, abbrev in normalizations.items():
            desc = desc.replace(full_term, abbrev)
        
        # Remove extra whitespace
        desc = ' '.join(desc.split())
        
        return desc
    
    def extract_dimensions(self, text: str) -> Dict[str, Any]:
        """Extract dimensional information from text"""
        
        dimensions = {}
        
        # Common dimension patterns
        patterns = {
            'length': r'(\d+(?:\.\d+)?)\s*(?:x|\*|by)\s*(\d+(?:\.\d+)?)\s*(?:x|\*|by)\s*(\d+(?:\.\d+)?)',
            'diameter': r'(?:dia|diameter|ø)\s*(\d+(?:\.\d+)?)',
            'thickness': r'(?:thick|thickness|t)\s*(\d+(?:\.\d+)?)',
            'gauge': r'(?:gauge|ga|g)\s*(\d+)',
        }
        
        import re
        
        for dim_type, pattern in patterns.items():
            matches = re.findall(pattern, text.lower())
            if matches:
                if dim_type == 'length' and len(matches[0]) == 3:
                    dimensions['length'] = float(matches[0][0])
                    dimensions['width'] = float(matches[0][1])
                    dimensions['height'] = float(matches[0][2])
                else:
                    dimensions[dim_type] = float(matches[0])
        
        return dimensions
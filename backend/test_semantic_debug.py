#!/usr/bin/env python3

import asyncio
import sys

# Add the backend directory to Python path
sys.path.insert(0, '/Users/riverscornelson/PycharmProjects/sales-order-system/backend')

from app.services.local_vector_store import LocalPartsCatalogVectorStore
from app.services.embeddings import PartEmbeddingService

async def debug_semantic_search():
    """Debug semantic search with different similarity thresholds"""
    
    print("🔍 DEBUGGING SEMANTIC SEARCH")
    print("=" * 50)
    
    # Initialize services
    vector_store = LocalPartsCatalogVectorStore()
    embedding_service = PartEmbeddingService()
    
    # Test query
    query = "4140 steel round bar"
    
    print(f"Query: '{query}'")
    print()
    
    # Generate query embedding
    print("1️⃣ Generating query embedding...")
    query_embedding = await embedding_service.create_query_embedding(query)
    print(f"   Query embedding generated: {query_embedding is not None}")
    print(f"   Embedding dimensions: {len(query_embedding) if query_embedding else 0}")
    
    # Test with different similarity thresholds
    thresholds = [0.9, 0.7, 0.5, 0.3, 0.1, 0.0]
    
    for threshold in thresholds:
        print(f"\n2️⃣ Testing similarity threshold: {threshold}")
        
        results = await vector_store.search_similar(
            query_vector=query_embedding,
            collection_name="parts_catalog",
            top_k=5,
            min_similarity=threshold
        )
        
        print(f"   Results found: {len(results)}")
        
        if results:
            print("   Top results:")
            for i, result in enumerate(results[:3]):
                metadata = result.get("metadata", {})
                similarity = result.get("similarity", 0)
                print(f"     {i+1}. {metadata.get('part_number', 'Unknown')}: {metadata.get('description', 'No description')} (similarity: {similarity:.4f})")
            break
    
    # Let's examine the vector data directly
    print("\n3️⃣ Examining vector data and similarities...")
    
    vectors = await vector_store.load_vectors("parts_catalog")
    print(f"   Total vectors loaded: {len(vectors)}")
    
    if vectors:
        # Check a few similarity calculations manually
        import numpy as np
        
        query_vec = np.array(query_embedding)
        
        print("   Manual similarity checks:")
        similarities = []
        
        for i, vector_data in enumerate(vectors):
            stored_vector = vector_data.get("vector", [])
            if stored_vector:
                stored_vec = np.array(stored_vector)
                
                # Calculate cosine similarity manually
                norm1 = np.linalg.norm(query_vec)
                norm2 = np.linalg.norm(stored_vec)
                
                if norm1 > 0 and norm2 > 0:
                    similarity = float(np.dot(query_vec, stored_vec) / (norm1 * norm2))
                else:
                    similarity = 0.0
                
                metadata = vector_data.get("metadata", {})
                part_number = metadata.get("part_number", f"Vector {i}")
                description = metadata.get("description", "")
                material = metadata.get("material", "")
                
                similarities.append((similarity, part_number, description, material))
                
                # Show if this contains 4140
                if "4140" in description or "4140" in material:
                    print(f"     *** 4140 PART FOUND: {part_number}: {description} (similarity: {similarity:.6f})")
        
        # Show top similarities
        similarities.sort(key=lambda x: x[0], reverse=True)
        print(f"\n   Top 5 similarities:")
        for i, (sim, part_num, desc, mat) in enumerate(similarities[:5]):
            print(f"     {i+1}. {part_num}: {desc[:60]}... (similarity: {sim:.6f})")
        
        print(f"\n   Similarity range: {similarities[-1][0]:.6f} to {similarities[0][0]:.6f}")
        print(f"   Average similarity: {sum(s[0] for s in similarities) / len(similarities):.6f}")
        
        # Count how many 4140 parts exist
        count_4140 = sum(1 for _, _, desc, mat in similarities if "4140" in desc or "4140" in mat)
        print(f"   Parts containing '4140': {count_4140}")
    
    print("\n4️⃣ CONCLUSION:")
    print("   The issue is that mock embeddings are random, so similarity scores are very low.")
    print("   With a reasonable threshold (0.3), no results are returned.")
    print("   The fuzzy search works because it doesn't depend on embeddings.")

if __name__ == "__main__":
    asyncio.run(debug_semantic_search())
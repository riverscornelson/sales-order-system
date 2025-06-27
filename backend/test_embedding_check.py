#!/usr/bin/env python3

import sys
sys.path.insert(0, '/Users/riverscornelson/PycharmProjects/sales-order-system/backend')

from app.services.embeddings import PartEmbeddingService

def test_embedding_service():
    """Test how to detect mock embeddings"""
    
    print("🔍 TESTING EMBEDDING SERVICE DETECTION")
    print("=" * 50)
    
    service = PartEmbeddingService()
    
    print(f"Provider: {service.provider}")
    print(f"Model name: {service.model_name}")
    print(f"Has client attribute: {hasattr(service, 'client')}")
    
    if hasattr(service, 'client'):
        print(f"Client value: {service.client}")
        print(f"Client is None: {service.client is None}")
        print(f"Client is False: {not service.client}")
    
    print("\nCondition checks:")
    print(f"hasattr(service, 'client'): {hasattr(service, 'client')}")
    print(f"not service.client: {not getattr(service, 'client', True)}")
    print(f"Combined check: {hasattr(service, 'client') and not service.client}")

if __name__ == "__main__":
    test_embedding_service()
import os
from .base import ERPProvider
from .mock_provider import MockERPProvider
from .dynamics_provider import DynamicsERPProvider

def get_erp_provider() -> ERPProvider:
    """Factory function to get the appropriate ERP provider"""
    provider_type = os.getenv('ERP_PROVIDER', 'mock').lower()
    
    if provider_type == 'dynamics365':
        return DynamicsERPProvider()
    else:
        return MockERPProvider()

__all__ = ['ERPProvider', 'MockERPProvider', 'DynamicsERPProvider', 'get_erp_provider']
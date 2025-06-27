from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from datetime import datetime
from ...models.schemas import OrderData, CustomerInfo, OrderLineItem

class ERPProvider(ABC):
    """Abstract base class for ERP integrations"""
    
    @abstractmethod
    async def validate_customer(self, customer_info: CustomerInfo) -> Dict[str, Any]:
        """Validate customer information against ERP system"""
        pass
    
    @abstractmethod
    async def check_inventory(self, part_numbers: List[str]) -> Dict[str, Dict[str, Any]]:
        """Check inventory availability for parts"""
        pass
    
    @abstractmethod
    async def get_pricing(self, customer_id: str, part_numbers: List[str]) -> Dict[str, float]:
        """Get pricing for parts for a specific customer"""
        pass
    
    @abstractmethod
    async def create_draft_order(self, order_data: OrderData) -> Dict[str, Any]:
        """Create a draft order in the ERP system"""
        pass
    
    @abstractmethod
    async def submit_order(self, draft_order_id: str, order_data: OrderData) -> Dict[str, Any]:
        """Submit a draft order to the ERP system"""
        pass
    
    @abstractmethod
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get the status of an order"""
        pass
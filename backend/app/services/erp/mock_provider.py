import asyncio
import random
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import os
import structlog

from .base import ERPProvider
from ...models.schemas import OrderData, CustomerInfo, OrderLineItem

logger = structlog.get_logger()

class MockERPProvider(ERPProvider):
    """Mock ERP provider for development and testing"""
    
    def __init__(self):
        self.mock_delay = float(os.getenv('ERP_MOCK_DELAY', '1.5'))
        self.mock_customers = {
            'ACME001': {
                'id': 'ACME001',
                'name': 'ACME Manufacturing',
                'email': 'orders@acme-mfg.com',
                'credit_limit': 50000.0,
                'payment_terms': 'NET30',
                'discount_rate': 0.05
            },
            'STEEL002': {
                'id': 'STEEL002', 
                'name': 'Steel Works Inc',
                'email': 'purchasing@steelworks.com',
                'credit_limit': 75000.0,
                'payment_terms': 'NET15',
                'discount_rate': 0.03
            }
        }
        
        self.mock_inventory = {
            'ST-304-12x8': {
                'part_number': 'ST-304-12x8',
                'description': 'Stainless Steel 304, 12" x 8" x 0.25"',
                'available_quantity': 150,
                'unit_price': 45.50,
                'lead_time_days': 3
            },
            'AL-6061-10x6': {
                'part_number': 'AL-6061-10x6',
                'description': 'Aluminum 6061, 10" x 6" x 0.5"',
                'available_quantity': 200,
                'unit_price': 32.75,
                'lead_time_days': 2
            },
            'CS-1018-8x4': {
                'part_number': 'CS-1018-8x4',
                'description': 'Carbon Steel 1018, 8" x 4" x 0.375"',
                'available_quantity': 300,
                'unit_price': 18.25,
                'lead_time_days': 1
            }
        }
        
        self.orders = {}  # In-memory order storage
        
    async def _simulate_api_delay(self):
        """Simulate API response time"""
        await asyncio.sleep(self.mock_delay + random.uniform(-0.5, 0.5))
    
    async def validate_customer(self, customer_info: CustomerInfo) -> Dict[str, Any]:
        """Validate customer information against mock ERP system"""
        await self._simulate_api_delay()
        
        # Try to find customer by various identifiers
        customer_id = None
        if customer_info.customer_id:
            customer_id = customer_info.customer_id
        elif customer_info.email:
            # Find by email
            for cid, cdata in self.mock_customers.items():
                if cdata['email'].lower() == customer_info.email.lower():
                    customer_id = cid
                    break
        elif customer_info.name:
            # Find by name (fuzzy match)
            for cid, cdata in self.mock_customers.items():
                if customer_info.name.lower() in cdata['name'].lower():
                    customer_id = cid
                    break
        
        if customer_id and customer_id in self.mock_customers:
            customer = self.mock_customers[customer_id]
            logger.info("Customer validated", customer_id=customer_id)
            return {
                'valid': True,
                'customer_id': customer_id,
                'customer_data': customer,
                'confidence': 0.95
            }
        else:
            # Create new customer for unrecognized ones
            new_customer_id = f"NEW{random.randint(1000, 9999)}"
            logger.info("New customer created", customer_id=new_customer_id)
            return {
                'valid': True,
                'customer_id': new_customer_id,
                'customer_data': {
                    'id': new_customer_id,
                    'name': customer_info.name or 'Unknown Customer',
                    'email': customer_info.email,
                    'credit_limit': 10000.0,
                    'payment_terms': 'NET30',
                    'discount_rate': 0.0,
                    'is_new': True
                },
                'confidence': 0.7,
                'requires_approval': True
            }
    
    async def check_inventory(self, part_numbers: List[str]) -> Dict[str, Dict[str, Any]]:
        """Check inventory availability for parts"""
        await self._simulate_api_delay()
        
        result = {}
        for part_number in part_numbers:
            if part_number in self.mock_inventory:
                inventory = self.mock_inventory[part_number].copy()
                # Add some randomness to simulate real inventory fluctuations
                inventory['available_quantity'] = max(0, inventory['available_quantity'] + random.randint(-10, 10))
                result[part_number] = {
                    'available': True,
                    **inventory
                }
            else:
                # Generate mock data for unknown parts
                result[part_number] = {
                    'available': random.choice([True, False]),
                    'part_number': part_number,
                    'description': f'Mock part: {part_number}',
                    'available_quantity': random.randint(0, 100) if random.choice([True, False]) else 0,
                    'unit_price': round(random.uniform(10.0, 100.0), 2),
                    'lead_time_days': random.randint(1, 14),
                    'is_mock': True
                }
        
        logger.info("Inventory checked", parts_count=len(part_numbers))
        return result
    
    async def get_pricing(self, customer_id: str, part_numbers: List[str]) -> Dict[str, float]:
        """Get pricing for parts for a specific customer"""
        await self._simulate_api_delay()
        
        customer = self.mock_customers.get(customer_id, {})
        discount_rate = customer.get('discount_rate', 0.0)
        
        pricing = {}
        inventory_data = await self.check_inventory(part_numbers)
        
        for part_number in part_numbers:
            base_price = inventory_data.get(part_number, {}).get('unit_price', 25.0)
            discounted_price = base_price * (1 - discount_rate)
            pricing[part_number] = round(discounted_price, 2)
        
        logger.info("Pricing retrieved", customer_id=customer_id, parts_count=len(part_numbers))
        return pricing
    
    async def create_draft_order(self, order_data: OrderData) -> Dict[str, Any]:
        """Create a draft order in the mock ERP system"""
        await self._simulate_api_delay()
        
        draft_order_id = f"DRAFT-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
        
        # Calculate totals
        total_amount = 0.0
        for item in order_data.line_items:
            if item.unit_price and item.quantity:
                total_amount += item.unit_price * item.quantity
        
        draft_order = {
            'draft_order_id': draft_order_id,
            'customer_id': order_data.customer_info.customer_id,
            'status': 'draft',
            'line_items': [item.dict() for item in order_data.line_items],
            'total_amount': total_amount,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(days=30)).isoformat()
        }
        
        self.orders[draft_order_id] = draft_order
        
        logger.info("Draft order created", draft_order_id=draft_order_id, total_amount=total_amount)
        return {
            'success': True,
            'draft_order_id': draft_order_id,
            'total_amount': total_amount,
            'status': 'draft',
            'expires_at': draft_order['expires_at']
        }
    
    async def submit_order(self, draft_order_id: str, order_data: OrderData) -> Dict[str, Any]:
        """Submit a draft order to the mock ERP system"""
        await self._simulate_api_delay()
        
        if draft_order_id not in self.orders:
            return {
                'success': False,
                'error': 'Draft order not found'
            }
        
        order_id = f"ORD-{datetime.now().strftime('%Y%m%d')}-{random.randint(10000, 99999)}"
        
        # Update order status
        order = self.orders[draft_order_id].copy()
        order.update({
            'order_id': order_id,
            'status': 'submitted',
            'submitted_at': datetime.now().isoformat(),
            'estimated_delivery': (datetime.now() + timedelta(days=7)).isoformat()
        })
        
        self.orders[order_id] = order
        
        logger.info("Order submitted", order_id=order_id, draft_order_id=draft_order_id)
        return {
            'success': True,
            'order_id': order_id,
            'status': 'submitted',
            'estimated_delivery': order['estimated_delivery'],
            'total_amount': order['total_amount']
        }
    
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get the status of an order"""
        await self._simulate_api_delay()
        
        if order_id not in self.orders:
            return {
                'found': False,
                'error': 'Order not found'
            }
        
        order = self.orders[order_id]
        
        # Simulate status progression
        statuses = ['submitted', 'confirmed', 'in_production', 'shipped', 'delivered']
        current_status = order.get('status', 'submitted')
        
        if current_status in statuses and random.random() < 0.3:  # 30% chance of status progression
            current_index = statuses.index(current_status)
            if current_index < len(statuses) - 1:
                current_status = statuses[current_index + 1]
                order['status'] = current_status
                order['last_updated'] = datetime.now().isoformat()
        
        logger.info("Order status retrieved", order_id=order_id, status=current_status)
        return {
            'found': True,
            'order_id': order_id,
            'status': current_status,
            'last_updated': order.get('last_updated', order.get('submitted_at')),
            'total_amount': order.get('total_amount'),
            'estimated_delivery': order.get('estimated_delivery')
        }
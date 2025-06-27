import os
import httpx
from typing import List, Dict, Optional, Any
from datetime import datetime
import structlog

from .base import ERPProvider
from ...models.schemas import OrderData, CustomerInfo, OrderLineItem

logger = structlog.get_logger()

class DynamicsERPProvider(ERPProvider):
    """Dynamics 365 ERP provider implementation"""
    
    def __init__(self):
        self.tenant_id = os.getenv('DYNAMICS_365_TENANT_ID')
        self.client_id = os.getenv('DYNAMICS_365_CLIENT_ID')
        self.client_secret = os.getenv('DYNAMICS_365_CLIENT_SECRET')
        self.resource_url = os.getenv('DYNAMICS_365_RESOURCE_URL')
        
        if not all([self.tenant_id, self.client_id, self.client_secret, self.resource_url]):
            logger.warning("Dynamics 365 credentials not fully configured")
        
        self.access_token = None
        self.token_expires_at = None
    
    async def _get_access_token(self) -> str:
        """Get OAuth2 access token for Dynamics 365"""
        if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
            return self.access_token
        
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/token"
        
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'resource': self.resource_url
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            expires_in = token_data.get('expires_in', 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)  # 5 min buffer
            
            logger.info("Dynamics 365 access token refreshed")
            return self.access_token
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to Dynamics 365 API"""
        token = await self._get_access_token()
        
        headers = kwargs.pop('headers', {})
        headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        url = f"{self.resource_url}/api/data/v9.2/{endpoint}"
        
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            
            if response.status_code == 204:  # No content
                return {}
            
            return response.json()
    
    async def validate_customer(self, customer_info: CustomerInfo) -> Dict[str, Any]:
        """Validate customer information against Dynamics 365"""
        try:
            # Search for customer by various criteria
            filters = []
            
            if customer_info.customer_id:
                filters.append(f"accountnumber eq '{customer_info.customer_id}'")
            
            if customer_info.email:
                filters.append(f"emailaddress1 eq '{customer_info.email}'")
            
            if customer_info.name:
                filters.append(f"contains(name, '{customer_info.name}')")
            
            if not filters:
                return {'valid': False, 'error': 'No customer identification provided'}
            
            filter_query = ' or '.join(filters)
            endpoint = f"accounts?$filter={filter_query}&$select=accountid,accountnumber,name,emailaddress1,creditlimit,paymenttermscode"
            
            result = await self._make_request('GET', endpoint)
            
            customers = result.get('value', [])
            
            if customers:
                customer = customers[0]  # Take first match
                logger.info("Customer found in Dynamics 365", customer_id=customer.get('accountnumber'))
                
                return {
                    'valid': True,
                    'customer_id': customer.get('accountnumber'),
                    'customer_data': {
                        'id': customer.get('accountnumber'),
                        'dynamics_id': customer.get('accountid'),
                        'name': customer.get('name'),
                        'email': customer.get('emailaddress1'),
                        'credit_limit': customer.get('creditlimit', 0),
                        'payment_terms': customer.get('paymenttermscode', 'NET30')
                    },
                    'confidence': 0.95
                }
            else:
                logger.info("Customer not found in Dynamics 365")
                return {
                    'valid': False,
                    'error': 'Customer not found',
                    'requires_creation': True
                }
                
        except Exception as e:
            logger.error("Error validating customer in Dynamics 365", error=str(e))
            return {
                'valid': False,
                'error': f'Validation error: {str(e)}'
            }
    
    async def check_inventory(self, part_numbers: List[str]) -> Dict[str, Dict[str, Any]]:
        """Check inventory availability in Dynamics 365"""
        try:
            result = {}
            
            for part_number in part_numbers:
                endpoint = f"products?$filter=productnumber eq '{part_number}'&$select=productid,productnumber,name,price,quantityonhand"
                
                product_result = await self._make_request('GET', endpoint)
                products = product_result.get('value', [])
                
                if products:
                    product = products[0]
                    result[part_number] = {
                        'available': True,
                        'part_number': product.get('productnumber'),
                        'description': product.get('name'),
                        'available_quantity': product.get('quantityonhand', 0),
                        'unit_price': product.get('price', 0),
                        'dynamics_product_id': product.get('productid')
                    }
                else:
                    result[part_number] = {
                        'available': False,
                        'part_number': part_number,
                        'error': 'Product not found'
                    }
            
            logger.info("Inventory checked in Dynamics 365", parts_count=len(part_numbers))
            return result
            
        except Exception as e:
            logger.error("Error checking inventory in Dynamics 365", error=str(e))
            return {part: {'available': False, 'error': str(e)} for part in part_numbers}
    
    async def get_pricing(self, customer_id: str, part_numbers: List[str]) -> Dict[str, float]:
        """Get customer-specific pricing from Dynamics 365"""
        try:
            pricing = {}
            
            # Get customer account ID
            customer_endpoint = f"accounts?$filter=accountnumber eq '{customer_id}'&$select=accountid"
            customer_result = await self._make_request('GET', customer_endpoint)
            customer_accounts = customer_result.get('value', [])
            
            if not customer_accounts:
                # Fall back to standard pricing
                inventory = await self.check_inventory(part_numbers)
                return {part: data.get('unit_price', 0) for part, data in inventory.items()}
            
            customer_dynamics_id = customer_accounts[0]['accountid']
            
            for part_number in part_numbers:
                # Check for customer-specific pricing
                pricing_endpoint = f"priceleveldetails?$filter=_productid_value eq (products?$filter=productnumber eq '{part_number}')&$select=amount"
                
                try:
                    pricing_result = await self._make_request('GET', pricing_endpoint)
                    price_details = pricing_result.get('value', [])
                    
                    if price_details:
                        pricing[part_number] = price_details[0].get('amount', 0)
                    else:
                        # Fall back to product standard price
                        inventory = await self.check_inventory([part_number])
                        pricing[part_number] = inventory.get(part_number, {}).get('unit_price', 0)
                        
                except Exception:
                    # Fall back to standard pricing on error
                    inventory = await self.check_inventory([part_number])
                    pricing[part_number] = inventory.get(part_number, {}).get('unit_price', 0)
            
            logger.info("Pricing retrieved from Dynamics 365", customer_id=customer_id)
            return pricing
            
        except Exception as e:
            logger.error("Error getting pricing from Dynamics 365", error=str(e))
            return {part: 0.0 for part in part_numbers}
    
    async def create_draft_order(self, order_data: OrderData) -> Dict[str, Any]:
        """Create a draft sales order in Dynamics 365"""
        try:
            # Get customer account ID
            customer_endpoint = f"accounts?$filter=accountnumber eq '{order_data.customer_info.customer_id}'&$select=accountid"
            customer_result = await self._make_request('GET', customer_endpoint)
            customer_accounts = customer_result.get('value', [])
            
            if not customer_accounts:
                return {'success': False, 'error': 'Customer not found'}
            
            customer_dynamics_id = customer_accounts[0]['accountid']
            
            # Create sales order
            order_payload = {
                '_customerid_value': customer_dynamics_id,
                'name': f"Order from {order_data.customer_info.name or 'Customer'}",
                'statecode': 0,  # Draft
                'statuscode': 1,  # New
                'requestdeliveryby': order_data.delivery_date,
                'description': order_data.special_instructions
            }
            
            order_result = await self._make_request('POST', 'salesorders', json=order_payload)
            sales_order_id = order_result.get('salesorderid')
            
            # Add line items
            total_amount = 0.0
            for item in order_data.line_items:
                if item.matched_part_id:
                    line_payload = {
                        '_salesorderid_value': sales_order_id,
                        '_productid_value': item.matched_part_id,
                        'quantity': item.quantity,
                        'priceperunit': item.unit_price or 0,
                        'description': item.description
                    }
                    
                    await self._make_request('POST', 'salesorderdetails', json=line_payload)
                    total_amount += (item.unit_price or 0) * item.quantity
            
            logger.info("Draft order created in Dynamics 365", sales_order_id=sales_order_id)
            return {
                'success': True,
                'draft_order_id': sales_order_id,
                'total_amount': total_amount,
                'status': 'draft'
            }
            
        except Exception as e:
            logger.error("Error creating draft order in Dynamics 365", error=str(e))
            return {'success': False, 'error': str(e)}
    
    async def submit_order(self, draft_order_id: str, order_data: OrderData) -> Dict[str, Any]:
        """Submit a draft order in Dynamics 365"""
        try:
            # Update order status to submitted
            update_payload = {
                'statecode': 1,  # Active
                'statuscode': 100000001  # Submitted (custom status)
            }
            
            await self._make_request('PATCH', f'salesorders({draft_order_id})', json=update_payload)
            
            logger.info("Order submitted in Dynamics 365", order_id=draft_order_id)
            return {
                'success': True,
                'order_id': draft_order_id,
                'status': 'submitted'
            }
            
        except Exception as e:
            logger.error("Error submitting order in Dynamics 365", error=str(e))
            return {'success': False, 'error': str(e)}
    
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get order status from Dynamics 365"""
        try:
            endpoint = f"salesorders({order_id})?$select=salesorderid,statecode,statuscode,totalamount,requestdeliveryby"
            order_result = await self._make_request('GET', endpoint)
            
            status_map = {
                0: 'draft',
                1: 'active',
                2: 'won',
                3: 'canceled'
            }
            
            state_code = order_result.get('statecode')
            status = status_map.get(state_code, 'unknown')
            
            logger.info("Order status retrieved from Dynamics 365", order_id=order_id, status=status)
            return {
                'found': True,
                'order_id': order_id,
                'status': status,
                'total_amount': order_result.get('totalamount'),
                'estimated_delivery': order_result.get('requestdeliveryby')
            }
            
        except Exception as e:
            logger.error("Error getting order status from Dynamics 365", error=str(e))
            return {'found': False, 'error': str(e)}
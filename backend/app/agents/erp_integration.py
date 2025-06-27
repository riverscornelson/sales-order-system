from typing import Dict, Any, List, Optional
import asyncio
import structlog

from ..services.erp import get_erp_provider

logger = structlog.get_logger()

class ERPIntegrationAgent:
    """Agent responsible for ERP system integration and validation"""
    
    def __init__(self):
        self.erp_provider = get_erp_provider()
    
    async def validate_order(self, customer_info: Dict[str, Any], 
                           line_items: List[Dict[str, Any]],
                           part_matches: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Validate order information against ERP system"""
        
        logger.info("Starting ERP validation", 
                   customer=customer_info.get("name", "Unknown"),
                   line_items_count=len(line_items))
        
        try:
            # Step 1: Validate customer information
            customer_validation = await self._validate_customer(customer_info)
            
            # Step 2: Check inventory for matched parts
            inventory_check = await self._check_inventory(line_items, part_matches)
            
            # Step 3: Get pricing information
            pricing_info = await self._get_pricing(customer_validation, inventory_check)
            
            # Step 4: Calculate order totals
            order_totals = self._calculate_order_totals(line_items, inventory_check, pricing_info)
            
            # Step 5: Validate business rules
            business_rules_check = await self._validate_business_rules(
                customer_validation, inventory_check, order_totals
            )
            
            result = {
                "customer_validation": customer_validation,
                "inventory_check": inventory_check,
                "pricing_info": pricing_info,
                "order_totals": order_totals,
                "business_rules": business_rules_check,
                "overall_status": self._determine_overall_status(
                    customer_validation, inventory_check, business_rules_check
                ),
                "agent": "erp_integration"
            }
            
            logger.info("ERP validation completed", 
                       customer_valid=customer_validation.get("valid", False),
                       total_amount=order_totals.get("total_amount", 0))
            
            return result
            
        except Exception as e:
            logger.error("ERP validation failed", error=str(e))
            raise Exception(f"ERP validation failed: {str(e)}")
    
    async def _validate_customer(self, customer_info: Dict[str, Any]) -> Dict[str, Any]:
        """Validate customer information with ERP"""
        
        try:
            # Convert to CustomerInfo object format expected by ERP
            from ..models.schemas import CustomerInfo
            
            customer_obj = CustomerInfo(
                name=customer_info.get("name"),
                email=customer_info.get("email"),
                phone=customer_info.get("phone"),
                company=customer_info.get("company"),
                address=customer_info.get("address"),
                customer_id=customer_info.get("customer_id")
            )
            
            validation_result = await self.erp_provider.validate_customer(customer_obj)
            
            # Enhance result with additional processing
            validation_result.update({
                "validation_timestamp": asyncio.get_event_loop().time(),
                "validation_method": type(self.erp_provider).__name__
            })
            
            logger.debug("Customer validation completed", 
                        customer_id=validation_result.get("customer_id"),
                        valid=validation_result.get("valid", False))
            
            return validation_result
            
        except Exception as e:
            logger.error("Customer validation failed", error=str(e))
            return {
                "valid": False,
                "error": str(e),
                "validation_timestamp": asyncio.get_event_loop().time()
            }
    
    async def _check_inventory(self, line_items: List[Dict[str, Any]], 
                             part_matches: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Check inventory availability for all parts"""
        
        try:
            # Collect all part numbers to check
            part_numbers = set()
            
            # From direct part numbers in line items
            for item in line_items:
                if item.get("part_number"):
                    part_numbers.add(item["part_number"])
            
            # From matched parts
            for item_matches in part_matches.values():
                for match in item_matches:
                    if match.get("part_number"):
                        part_numbers.add(match["part_number"])
            
            if not part_numbers:
                return {
                    "status": "no_parts_to_check",
                    "parts": {},
                    "available_count": 0,
                    "unavailable_count": 0
                }
            
            # Check inventory with ERP
            inventory_result = await self.erp_provider.check_inventory(list(part_numbers))
            
            # Process results
            available_count = 0
            unavailable_count = 0
            
            for part_number, part_info in inventory_result.items():
                if part_info.get("available", False):
                    available_count += 1
                else:
                    unavailable_count += 1
            
            result = {
                "status": "completed",
                "parts": inventory_result,
                "available_count": available_count,
                "unavailable_count": unavailable_count,
                "total_parts_checked": len(part_numbers),
                "check_timestamp": asyncio.get_event_loop().time()
            }
            
            logger.debug("Inventory check completed", 
                        total_parts=len(part_numbers),
                        available=available_count,
                        unavailable=unavailable_count)
            
            return result
            
        except Exception as e:
            logger.error("Inventory check failed", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "parts": {},
                "available_count": 0,
                "unavailable_count": 0
            }
    
    async def _get_pricing(self, customer_validation: Dict[str, Any], 
                          inventory_check: Dict[str, Any]) -> Dict[str, Any]:
        """Get pricing information for available parts"""
        
        try:
            customer_id = customer_validation.get("customer_id")
            if not customer_id:
                return {
                    "status": "no_customer_id",
                    "pricing": {},
                    "error": "Customer ID required for pricing"
                }
            
            # Get part numbers for available parts only
            available_parts = []
            parts_data = inventory_check.get("parts", {})
            
            for part_number, part_info in parts_data.items():
                if part_info.get("available", False):
                    available_parts.append(part_number)
            
            if not available_parts:
                return {
                    "status": "no_available_parts",
                    "pricing": {}
                }
            
            # Get pricing from ERP
            pricing_result = await self.erp_provider.get_pricing(customer_id, available_parts)
            
            result = {
                "status": "completed",
                "customer_id": customer_id,
                "pricing": pricing_result,
                "parts_priced": len(pricing_result),
                "pricing_timestamp": asyncio.get_event_loop().time()
            }
            
            logger.debug("Pricing retrieval completed", 
                        customer_id=customer_id,
                        parts_priced=len(pricing_result))
            
            return result
            
        except Exception as e:
            logger.error("Pricing retrieval failed", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "pricing": {}
            }
    
    def _calculate_order_totals(self, line_items: List[Dict[str, Any]], 
                               inventory_check: Dict[str, Any],
                               pricing_info: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate order totals based on available parts and pricing"""
        
        try:
            parts_data = inventory_check.get("parts", {})
            pricing_data = pricing_info.get("pricing", {})
            
            line_totals = []
            subtotal = 0.0
            total_quantity = 0
            available_items = 0
            unavailable_items = 0
            
            for i, item in enumerate(line_items):
                quantity = item.get("quantity", 1)
                
                # Find best available part for this item
                best_part = None
                best_price = None
                
                # Check if item has direct part number
                if item.get("part_number") and item["part_number"] in parts_data:
                    part_info = parts_data[item["part_number"]]
                    if part_info.get("available"):
                        best_part = item["part_number"]
                        best_price = pricing_data.get(best_part)
                
                # If no direct match, this would require checking part_matches
                # For now, we'll use the direct approach
                
                line_total_data = {
                    "line_number": i + 1,
                    "description": item.get("description", ""),
                    "quantity": quantity,
                    "part_number": best_part,
                    "unit_price": best_price,
                    "line_total": (best_price * quantity) if best_price else 0.0,
                    "available": best_part is not None
                }
                
                line_totals.append(line_total_data)
                
                if best_part:
                    subtotal += line_total_data["line_total"]
                    total_quantity += quantity
                    available_items += 1
                else:
                    unavailable_items += 1
            
            # Calculate taxes and fees (mock calculation)
            tax_rate = 0.08  # 8% tax
            tax_amount = subtotal * tax_rate
            shipping_fee = 15.0 if subtotal < 100 else 0.0  # Free shipping over $100
            total_amount = subtotal + tax_amount + shipping_fee
            
            result = {
                "line_totals": line_totals,
                "subtotal": round(subtotal, 2),
                "tax_amount": round(tax_amount, 2),
                "shipping_fee": round(shipping_fee, 2),
                "total_amount": round(total_amount, 2),
                "total_quantity": total_quantity,
                "available_items": available_items,
                "unavailable_items": unavailable_items,
                "calculation_timestamp": asyncio.get_event_loop().time()
            }
            
            logger.debug("Order totals calculated", 
                        subtotal=subtotal,
                        total_amount=total_amount,
                        available_items=available_items)
            
            return result
            
        except Exception as e:
            logger.error("Order totals calculation failed", error=str(e))
            return {
                "error": str(e),
                "subtotal": 0.0,
                "total_amount": 0.0,
                "available_items": 0,
                "unavailable_items": len(line_items)
            }
    
    async def _validate_business_rules(self, customer_validation: Dict[str, Any],
                                     inventory_check: Dict[str, Any],
                                     order_totals: Dict[str, Any]) -> Dict[str, Any]:
        """Validate business rules for the order"""
        
        try:
            rules_results = []
            overall_status = "passed"
            
            # Rule 1: Customer must be valid
            customer_valid = customer_validation.get("valid", False)
            rules_results.append({
                "rule": "customer_validation",
                "status": "passed" if customer_valid else "failed",
                "message": "Customer validation passed" if customer_valid else "Customer validation failed"
            })
            
            if not customer_valid:
                overall_status = "failed"
            
            # Rule 2: At least one item must be available
            available_items = order_totals.get("available_items", 0)
            if available_items == 0:
                rules_results.append({
                    "rule": "item_availability",
                    "status": "failed",
                    "message": "No items are available for order"
                })
                overall_status = "failed"
            else:
                rules_results.append({
                    "rule": "item_availability", 
                    "status": "passed",
                    "message": f"{available_items} items available for order"
                })
            
            # Rule 3: Order total must meet minimum
            minimum_order = 25.0
            total_amount = order_totals.get("total_amount", 0.0)
            if total_amount < minimum_order:
                rules_results.append({
                    "rule": "minimum_order_value",
                    "status": "warning",
                    "message": f"Order total ${total_amount:.2f} is below minimum ${minimum_order:.2f}"
                })
                if overall_status == "passed":
                    overall_status = "warning"
            else:
                rules_results.append({
                    "rule": "minimum_order_value",
                    "status": "passed",
                    "message": f"Order total ${total_amount:.2f} meets minimum requirement"
                })
            
            # Rule 4: Check credit limit (if available)
            customer_data = customer_validation.get("customer_data", {})
            credit_limit = customer_data.get("credit_limit")
            if credit_limit and total_amount > credit_limit:
                rules_results.append({
                    "rule": "credit_limit",
                    "status": "failed",
                    "message": f"Order total ${total_amount:.2f} exceeds credit limit ${credit_limit:.2f}"
                })
                overall_status = "failed"
            elif credit_limit:
                rules_results.append({
                    "rule": "credit_limit",
                    "status": "passed",
                    "message": f"Order within credit limit ${credit_limit:.2f}"
                })
            
            # Rule 5: Check for new customer approval requirement
            requires_approval = customer_validation.get("requires_approval", False)
            if requires_approval:
                rules_results.append({
                    "rule": "new_customer_approval",
                    "status": "requires_approval",
                    "message": "New customer requires manual approval"
                })
                if overall_status == "passed":
                    overall_status = "requires_approval"
            
            result = {
                "overall_status": overall_status,
                "rules": rules_results,
                "validation_timestamp": asyncio.get_event_loop().time()
            }
            
            logger.debug("Business rules validation completed", 
                        overall_status=overall_status,
                        rules_count=len(rules_results))
            
            return result
            
        except Exception as e:
            logger.error("Business rules validation failed", error=str(e))
            return {
                "overall_status": "error",
                "error": str(e),
                "rules": []
            }
    
    def _determine_overall_status(self, customer_validation: Dict[str, Any],
                                 inventory_check: Dict[str, Any],
                                 business_rules: Dict[str, Any]) -> str:
        """Determine overall ERP validation status"""
        
        # Check for critical failures
        if not customer_validation.get("valid", False):
            return "failed"
        
        if inventory_check.get("available_count", 0) == 0:
            return "failed"
        
        business_status = business_rules.get("overall_status", "failed")
        if business_status == "failed":
            return "failed"
        
        # Check for warnings or approval requirements
        if business_status in ["warning", "requires_approval"]:
            return business_status
        
        # All checks passed
        return "passed"
    
    async def create_draft_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a draft order in the ERP system"""
        
        try:
            logger.info("Creating draft order in ERP")
            
            # Convert to OrderData format
            from ..models.schemas import OrderData, CustomerInfo, OrderLineItem
            
            customer_info = CustomerInfo(**order_data.get("customer_info", {}))
            
            line_items = []
            for item_data in order_data.get("line_items", []):
                line_item = OrderLineItem(**item_data)
                line_items.append(line_item)
            
            order_obj = OrderData(
                customer_info=customer_info,
                line_items=line_items,
                order_date=order_data.get("order_date"),
                delivery_date=order_data.get("delivery_date"),
                special_instructions=order_data.get("special_instructions"),
                total_amount=order_data.get("total_amount")
            )
            
            # Create draft order via ERP provider
            result = await self.erp_provider.create_draft_order(order_obj)
            
            logger.info("Draft order created", 
                       draft_order_id=result.get("draft_order_id"),
                       success=result.get("success", False))
            
            return result
            
        except Exception as e:
            logger.error("Failed to create draft order", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
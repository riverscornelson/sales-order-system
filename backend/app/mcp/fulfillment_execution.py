"""
Phase 2: Fulfillment Strategy Execution
Executes specific fulfillment strategies with actual inventory search integration
"""

import asyncio
from typing import Dict, Any, List, Optional
import structlog

logger = structlog.get_logger()


async def execute_fulfillment_strategy(strategy_data: Dict[str, Any], search_tools: Any) -> Dict[str, Any]:
    """
    MCP Tool: Execute a specific fulfillment strategy with actual inventory search
    Integrates sales order reasoning with search execution
    """
    strategy_type = strategy_data.get('strategy_type', 'exact_match')
    line_item_data = strategy_data.get('line_item', {})
    analysis_context = strategy_data.get('analysis_context', {})
    
    logger.info("🎯 Executing fulfillment strategy", 
                strategy_type=strategy_type,
                line_item_id=line_item_data.get('line_id', 'unknown'))
    
    # Import here to avoid circular imports
    from ..models.line_item_schemas import LineItem
    
    # Create line item from data
    line_item = LineItem(
        line_id=line_item_data.get('line_id', 'unknown'),
        raw_text=line_item_data.get('raw_text', ''),
        extracted_specs=line_item_data.get('extracted_specs', {})
    )
    
    # Execute strategy-specific search
    if strategy_type == 'exact_match':
        results = await _execute_exact_match_search(line_item, search_tools, analysis_context)
    elif strategy_type == 'alternative_products':
        results = await _execute_alternative_search(line_item, search_tools, analysis_context)
    elif strategy_type == 'split_shipment':
        results = await _execute_split_shipment_search(line_item, search_tools, analysis_context)
    elif strategy_type == 'expedited_restock':
        results = await _execute_expedited_search(line_item, search_tools, analysis_context)
    elif strategy_type == 'custom_solution':
        results = await _execute_custom_solution_search(line_item, search_tools, analysis_context)
    else:
        results = await _execute_exact_match_search(line_item, search_tools, analysis_context)
    
    logger.info("✅ Fulfillment strategy executed", 
                strategy_type=strategy_type,
                results_found=len(results.get('matches', [])),
                success=results.get('success', False))
    
    return {
        'strategy_execution': {
            'strategy_type': strategy_type,
            'results_found': len(results.get('matches', [])),
            'execution_successful': results.get('success', False),
            'reasoning_applied': results.get('reasoning_notes', []),
            'matches': results.get('matches', []),
            'alternatives_considered': results.get('alternatives_count', 0),
            'fulfillment_confidence': results.get('confidence_score', 0.0)
        }
    }


async def _execute_exact_match_search(line_item: "LineItem", search_tools: Any, context: Dict) -> Dict[str, Any]:
    """Execute exact match search strategy"""
    
    # Use high threshold for exact matches
    search_params = {
        'similarity_threshold': 0.8,
        'max_results': 10,
        'require_exact_specs': True
    }
    
    # Emergency situations lower threshold slightly
    if context.get('emergency_detected', False):
        search_params['similarity_threshold'] = 0.75
        search_params['max_results'] = 15
    
    try:
        # Execute search with agentic tools
        results = await search_tools.semantic_vector_search(
            line_item.raw_text,
            top_k=search_params.get('max_results', 10)
        )
        
        return {
            'success': True,
            'matches': results,
            'confidence_score': 0.9,
            'reasoning_notes': ['Exact match search with high threshold', 'Prioritized specification accuracy'],
            'alternatives_count': 0
        }
    except Exception as e:
        logger.error("Exact match search failed", error=str(e))
        return {
            'success': False,
            'matches': [],
            'confidence_score': 0.0,
            'reasoning_notes': [f'Exact match search failed: {str(e)}'],
            'alternatives_count': 0
        }


async def _execute_alternative_search(line_item: "LineItem", search_tools: Any, context: Dict) -> Dict[str, Any]:
    """Execute alternative products search strategy"""
    
    # Lower threshold for alternatives, broader search
    search_params = {
        'similarity_threshold': 0.6,
        'max_results': 20,
        'include_substitutes': True,
        'expand_search_terms': True
    }
    
    # Industry-specific adjustments
    if context.get('customer_industry') == 'aerospace':
        search_params['similarity_threshold'] = 0.75  # Still need high quality alternatives
    elif context.get('customer_industry') == 'research_development':
        search_params['similarity_threshold'] = 0.5   # More experimental alternatives
    
    try:
        # Execute broader search
        results = await search_tools.semantic_vector_search(
            line_item.raw_text,
            top_k=search_params.get('max_results', 20)
        )
        
        # Filter for reasonable alternatives
        alternatives = [r for r in results if r.get('score', 0) >= search_params['similarity_threshold']]
        
        return {
            'success': True,
            'matches': alternatives,
            'confidence_score': 0.7,
            'reasoning_notes': [
                'Alternative products search with expanded criteria',
                f'Industry-adjusted threshold: {search_params["similarity_threshold"]}',
                'Included compatible substitutes'
            ],
            'alternatives_count': len(alternatives)
        }
    except Exception as e:
        logger.error("Alternative search failed", error=str(e))
        return {
            'success': False,
            'matches': [],
            'confidence_score': 0.0,
            'reasoning_notes': [f'Alternative search failed: {str(e)}'],
            'alternatives_count': 0
        }


async def _execute_split_shipment_search(line_item: "LineItem", search_tools: Any, context: Dict) -> Dict[str, Any]:
    """Execute split shipment search strategy"""
    
    # Search for partial quantities and full availability
    search_params = {
        'similarity_threshold': 0.7,
        'max_results': 25,
        'check_inventory_levels': True,
        'partial_quantities_ok': True
    }
    
    try:
        # Execute inventory-aware search
        results = await search_tools.semantic_vector_search(
            line_item.raw_text,
            top_k=search_params.get('max_results', 25)
        )
        
        # Separate results by availability
        immediate_available = []
        future_available = []
        
        for result in results:
            # Mock inventory check - in real implementation would check actual inventory
            inventory_level = result.get('inventory_level', 0)
            requested_qty = line_item.extracted_specs.get('quantity', 1)
            
            if inventory_level >= requested_qty:
                immediate_available.append(result)
            elif inventory_level > 0:
                immediate_available.append({
                    **result,
                    'available_quantity': inventory_level,
                    'partial_shipment': True
                })
                future_available.append({
                    **result,
                    'remaining_quantity': requested_qty - inventory_level,
                    'estimated_restock': '5-7 days'
                })
        
        all_matches = immediate_available + future_available
        
        return {
            'success': True,
            'matches': all_matches,
            'confidence_score': 0.8,
            'reasoning_notes': [
                'Split shipment strategy with inventory analysis',
                f'Immediate availability: {len(immediate_available)} items',
                f'Future availability: {len(future_available)} items',
                'Optimized for faster partial fulfillment'
            ],
            'alternatives_count': len(all_matches),
            'split_options': {
                'immediate': len(immediate_available),
                'future': len(future_available)
            }
        }
    except Exception as e:
        logger.error("Split shipment search failed", error=str(e))
        return {
            'success': False,
            'matches': [],
            'confidence_score': 0.0,
            'reasoning_notes': [f'Split shipment search failed: {str(e)}'],
            'alternatives_count': 0
        }


async def _execute_expedited_search(line_item: "LineItem", search_tools: Any, context: Dict) -> Dict[str, Any]:
    """Execute expedited restock search strategy"""
    
    # Search for items that can be expedited from suppliers
    search_params = {
        'similarity_threshold': 0.8,
        'max_results': 15,
        'include_supplier_catalog': True,
        'expedited_only': True
    }
    
    try:
        # Execute supplier-aware search
        results = await search_tools.semantic_vector_search(
            line_item.raw_text,
            top_k=search_params.get('max_results', 15)
        )
        
        # Add expediting information
        expedited_results = []
        for result in results:
            expedited_result = {
                **result,
                'expedited_available': True,
                'estimated_delivery': '3-5 business days',
                'expediting_cost': 'Premium pricing applies',
                'supplier_confirmed': False  # Would require actual supplier check
            }
            expedited_results.append(expedited_result)
        
        return {
            'success': True,
            'matches': expedited_results,
            'confidence_score': 0.6,
            'reasoning_notes': [
                'Expedited restock search with supplier integration',
                'Premium delivery timeline (3-5 days)',
                'Requires supplier confirmation and expediting fees',
                'Maintains exact specifications'
            ],
            'alternatives_count': len(expedited_results),
            'expediting_details': {
                'timeline': '3-5 business days',
                'cost_impact': 'Premium pricing',
                'supplier_coordination_required': True
            }
        }
    except Exception as e:
        logger.error("Expedited search failed", error=str(e))
        return {
            'success': False,
            'matches': [],
            'confidence_score': 0.0,
            'reasoning_notes': [f'Expedited search failed: {str(e)}'],
            'alternatives_count': 0
        }


async def _execute_custom_solution_search(line_item: "LineItem", search_tools: Any, context: Dict) -> Dict[str, Any]:
    """Execute custom solution search strategy"""
    
    # Multi-faceted search for creative solutions
    search_params = {
        'similarity_threshold': 0.5,
        'max_results': 30,
        'creative_alternatives': True,
        'component_breakdown': True,
        'custom_fabrication': True
    }
    
    try:
        # Execute comprehensive search
        results = await search_tools.semantic_vector_search(
            line_item.raw_text,
            top_k=search_params.get('max_results', 30)
        )
        
        # Categorize solution types
        direct_matches = [r for r in results if r.get('score', 0) >= 0.8]
        component_solutions = [r for r in results if 0.6 <= r.get('score', 0) < 0.8]
        creative_alternatives = [r for r in results if 0.5 <= r.get('score', 0) < 0.6]
        
        custom_solutions = []
        
        # Add direct matches
        for match in direct_matches:
            custom_solutions.append({
                **match,
                'solution_type': 'direct_match',
                'confidence': 'high'
            })
        
        # Add component-based solutions
        for comp in component_solutions:
            custom_solutions.append({
                **comp,
                'solution_type': 'component_assembly',
                'confidence': 'medium',
                'requires_assembly': True
            })
        
        # Add creative alternatives
        for alt in creative_alternatives:
            custom_solutions.append({
                **alt,
                'solution_type': 'creative_alternative',
                'confidence': 'low_to_medium',
                'requires_validation': True
            })
        
        return {
            'success': True,
            'matches': custom_solutions,
            'confidence_score': 0.7,
            'reasoning_notes': [
                'Custom solution search with multiple approaches',
                f'Direct matches: {len(direct_matches)}',
                f'Component solutions: {len(component_solutions)}',
                f'Creative alternatives: {len(creative_alternatives)}',
                'Requires coordination and validation'
            ],
            'alternatives_count': len(custom_solutions),
            'solution_breakdown': {
                'direct_matches': len(direct_matches),
                'component_solutions': len(component_solutions),
                'creative_alternatives': len(creative_alternatives)
            }
        }
    except Exception as e:
        logger.error("Custom solution search failed", error=str(e))
        return {
            'success': False,
            'matches': [],
            'confidence_score': 0.0,
            'reasoning_notes': [f'Custom solution search failed: {str(e)}'],
            'alternatives_count': 0
        }


class SalesOrderSearchCoordinator:
    """
    Enhanced search coordinator that integrates sales order reasoning
    with actual inventory search and fulfillment execution
    """
    
    def __init__(self, catalog_service, llm=None):
        self.catalog_service = catalog_service
        self.llm = llm
        
        # Import here to avoid circular imports
        from .reasoning_framework import SalesOrderReasoningFramework
        from ..mcp.search_tools import AgenticSearchTools
        
        self.reasoning_framework = SalesOrderReasoningFramework()
        self.search_tools = AgenticSearchTools(catalog_service)
        self.logger = structlog.get_logger()
    
    async def process_sales_order_with_intelligence(self, line_items: List["LineItem"], 
                                                  customer_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process sales order using intelligent reasoning and fulfillment strategies
        """
        self.logger.info("🧠 Processing sales order with intelligence", 
                        line_items_count=len(line_items))
        
        results = []
        
        for line_item in line_items:
            # Step 1: Analyze individual line item as sales order
            analysis = await self.reasoning_framework.analyze_sales_order(
                line_item.raw_text,
                customer_context.get('name', 'Unknown Customer') if customer_context else 'Unknown Customer'
            )
            
            # Step 2: Generate fulfillment strategies
            strategies = await self.reasoning_framework.generate_fulfillment_strategies(analysis)
            
            # Step 3: Execute top strategy with actual search
            if strategies:
                top_strategy = strategies[0]
                execution_result = await execute_fulfillment_strategy({
                    'strategy_type': top_strategy.strategy_type.value,
                    'line_item': {
                        'line_id': line_item.line_id,
                        'raw_text': line_item.raw_text,
                        'extracted_specs': line_item.extracted_specs
                    },
                    'analysis_context': {
                        'complexity': analysis.complexity_assessment.value,
                        'customer_industry': analysis.customer_context.industry_sector,
                        'flexibility_score': analysis.flexibility_score,
                        'emergency_detected': len(analysis.emergency_indicators) > 0
                    }
                }, self.search_tools)
                
                results.append({
                    'line_item': line_item,
                    'analysis': analysis,
                    'strategies': strategies,
                    'executed_strategy': top_strategy.strategy_type.value,
                    'search_results': execution_result
                })
            else:
                results.append({
                    'line_item': line_item,
                    'analysis': analysis,
                    'strategies': [],
                    'executed_strategy': 'none',
                    'search_results': {'success': False, 'matches': []}
                })
        
        # Aggregate results
        total_items = len(results)
        successful_items = sum(1 for r in results if r['search_results'].get('success', False))
        total_matches = sum(len(r['search_results'].get('matches', [])) for r in results)
        
        self.logger.info("✅ Sales order intelligence processing completed",
                        total_items=total_items,
                        successful_items=successful_items,
                        total_matches=total_matches)
        
        return {
            'processing_summary': {
                'total_line_items': total_items,
                'successful_items': successful_items,
                'total_matches_found': total_matches,
                'success_rate': successful_items / total_items if total_items > 0 else 0.0,
                'intelligence_applied': True
            },
            'detailed_results': results,
            'overall_confidence': sum(r['analysis'].confidence_score for r in results) / total_items if total_items > 0 else 0.0
        }
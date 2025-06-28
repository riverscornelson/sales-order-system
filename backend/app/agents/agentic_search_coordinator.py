"""
Agentic Search Coordinator
AI-powered autonomous search orchestrator that intelligently selects and combines
multiple search strategies to find the best parts matches.
"""

import asyncio
import json
from typing import List, Dict, Any, Optional
import structlog
from langchain_openai import ChatOpenAI

from ..models.line_item_schemas import LineItem, SearchResult, MatchConfidence
from ..mcp.search_tools import AgenticSearchTools
from ..mcp.contextual_intelligence import ContextualIntelligenceServer, assess_complexity_factors, dynamic_threshold_adjustment
from ..services.parts_catalog import PartsCatalogService

logger = structlog.get_logger()

class AgenticSearchCoordinator:
    """
    AI-powered search orchestrator with tool autonomy
    Replaces rigid search patterns with intelligent decision-making
    """
    
    def __init__(self, catalog_service: PartsCatalogService, llm: Optional[ChatOpenAI] = None):
        self.catalog_service = catalog_service
        self.llm = llm
        self.search_tools = AgenticSearchTools(catalog_service)
        
        # Phase 1: Contextual Intelligence Integration
        self.contextual_intelligence = ContextualIntelligenceServer()
        
        # Track search patterns for learning
        self.search_history = []
        self.successful_patterns = []
        
    async def search_for_line_item(self, line_item: LineItem) -> List[SearchResult]:
        """
        Autonomously search for line item using intelligent strategy selection
        
        Args:
            line_item: The line item to search for
            
        Returns:
            List of search results from best matching strategy
        """
        logger.info("🤖 Starting agentic search coordination", 
                   line_id=line_item.line_id,
                   raw_text=line_item.raw_text[:100])
        
        try:
            # If no LLM available, use fallback strategy
            if not self.llm:
                logger.warning("No LLM available, using contextual fallback search strategy")
                return await self._contextual_fallback_search_strategy(line_item)
            
            # Phase 1 Enhanced: Contextual Intelligence Analysis
            contextual_insights = await self._analyze_contextual_intelligence(line_item)
            
            # Phase 2: Catalog exploration with contextual awareness
            catalog_context = await self._gather_catalog_context(line_item)
            
            # Phase 3: Context-aware search strategy planning
            search_plan = await self._plan_contextual_search_strategy(line_item, catalog_context, contextual_insights)
            
            # Phase 4: Execute search strategies with dynamic thresholds
            search_results = await self._execute_contextual_search_plan(line_item, search_plan, contextual_insights)
            
            # Phase 5: Context-aware result analysis and refinement
            refined_results = await self._refine_and_rank_results_with_context(line_item, search_results, contextual_insights)
            
            # Track successful patterns for learning
            if refined_results:
                await self._record_successful_pattern(line_item, search_plan, refined_results)
            
            logger.info("✅ Agentic search completed", 
                       line_id=line_item.line_id,
                       results_found=len(refined_results),
                       strategies_used=len(search_plan.get("strategies", [])))
            
            return refined_results
            
        except Exception as e:
            logger.error("❌ Agentic search failed", 
                        line_id=line_item.line_id, 
                        error=str(e))
            # Fallback to basic search
            return await self._contextual_fallback_search_strategy(line_item)
    
    async def _analyze_contextual_intelligence(self, line_item: LineItem) -> Dict[str, Any]:
        """
        Phase 1: Analyze contextual intelligence for the line item
        Determines complexity, business context, and provides strategic guidance
        """
        logger.debug("🧠 Analyzing contextual intelligence", line_id=line_item.line_id)
        
        try:
            # Create order data structure for contextual analysis
            order_data = {
                "line_items": [self._line_item_to_dict(line_item)],
                "customer": {"name": "unknown"},  # Would be populated from order context
                "delivery_date": None,
                "urgency": line_item.urgency or "medium"
            }
            
            # Analyze procurement context
            contextual_insights = await self.contextual_intelligence.analyze_procurement_context(order_data)
            
            # Assess complexity factors for this specific line item
            complexity_assessment = await assess_complexity_factors(self._line_item_to_dict(line_item))
            
            # Get dynamic threshold adjustments
            context_for_thresholds = {
                "urgency_level": contextual_insights.urgency_factors.get("delivery_urgency", {}).get("urgency_level", "medium"),
                "quality_requirements": contextual_insights.business_context.value,
                "cost_sensitivity": "medium"  # Would be derived from customer context
            }
            
            adjusted_thresholds = await dynamic_threshold_adjustment(context_for_thresholds)
            
            result = {
                "contextual_insights": contextual_insights,
                "complexity_assessment": complexity_assessment,
                "adjusted_thresholds": adjusted_thresholds,
                "recommended_approach": contextual_insights.recommended_approach
            }
            
            logger.info("✅ Contextual intelligence analysis completed",
                       line_id=line_item.line_id,
                       complexity=contextual_insights.complexity_level.value,
                       business_context=contextual_insights.business_context.value,
                       approach=contextual_insights.recommended_approach)
            
            return result
            
        except Exception as e:
            logger.error("❌ Contextual intelligence analysis failed", 
                        line_id=line_item.line_id, error=str(e))
            # Return minimal context as fallback
            return {
                "contextual_insights": None,
                "complexity_assessment": {"complexity_level": "moderate"},
                "adjusted_thresholds": {},
                "recommended_approach": "standard_search"
            }
    
    def _line_item_to_dict(self, line_item: LineItem) -> Dict[str, Any]:
        """Convert LineItem to dictionary format for contextual analysis"""
        return {
            "line_id": line_item.line_id,
            "raw_text": line_item.raw_text,
            "description": line_item.raw_text,  # Use raw_text as description
            "project": line_item.project,
            "urgency": line_item.urgency,
            "special_requirements": line_item.special_requirements or [],
            "extracted_specs": line_item.extracted_specs.dict() if line_item.extracted_specs else {}
        }
    
    async def _plan_contextual_search_strategy(self, line_item: LineItem, 
                                             catalog_context: Dict[str, Any],
                                             contextual_insights: Dict[str, Any]) -> Dict[str, Any]:
        """Plan search strategy enhanced with contextual intelligence"""
        
        logger.debug("🎯 Planning contextual search strategy", line_id=line_item.line_id)
        
        # Get the recommended approach from contextual intelligence
        recommended_approach = contextual_insights.get("recommended_approach", "standard_search")
        complexity_level = contextual_insights.get("complexity_assessment", {}).get("complexity_level", "moderate")
        
        # Use enhanced planning based on contextual insights
        if recommended_approach == "multi_agent_collaboration":
            return await self._plan_multi_agent_strategy(line_item, catalog_context, contextual_insights)
        elif recommended_approach == "enhanced_reasoning_chain":
            return await self._plan_enhanced_reasoning_strategy(line_item, catalog_context, contextual_insights)
        elif recommended_approach == "contextual_search":
            return await self._plan_enhanced_contextual_strategy(line_item, catalog_context, contextual_insights)
        else:
            # Enhanced standard search with contextual awareness
            return await self._plan_enhanced_standard_strategy(line_item, catalog_context, contextual_insights)
    
    async def _plan_enhanced_standard_strategy(self, line_item: LineItem, 
                                             catalog_context: Dict[str, Any],
                                             contextual_insights: Dict[str, Any]) -> Dict[str, Any]:
        """Plan enhanced standard search strategy with contextual awareness"""
        
        # Get adjusted thresholds from contextual intelligence
        adjusted_thresholds = contextual_insights.get("adjusted_thresholds", {})
        
        # Create contextually-aware search plan
        strategies = []
        
        # Strategy 1: Enhanced semantic search with adjusted thresholds
        semantic_params = {
            "query": line_item.raw_text,
            "top_k": 10,
            "min_similarity": adjusted_thresholds.get("semantic_similarity", 0.7)
        }
        strategies.append({
            "tool": "semantic_vector_search",
            "priority": 1,
            "parameters": semantic_params,
            "reasoning": "Contextually-adjusted semantic search"
        })
        
        # Strategy 2: Enhanced material search if materials detected
        if contextual_insights.get("complexity_assessment", {}).get("specialized_requirements"):
            material_params = {
                "material": "detected_material",  # Would extract from line item
                "strict": False
            }
            strategies.append({
                "tool": "material_category_search", 
                "priority": 2,
                "parameters": material_params,
                "reasoning": "Material-specific search with contextual adjustment"
            })
        
        # Strategy 3: Fuzzy search with adjusted thresholds
        fuzzy_params = {
            "terms": line_item.raw_text.split()[:5],
            "fuzzy_threshold": int(adjusted_thresholds.get("fuzzy_match", 0.8) * 100)
        }
        strategies.append({
            "tool": "fuzzy_text_search",
            "priority": 3, 
            "parameters": fuzzy_params,
            "reasoning": "Fuzzy search with contextual threshold adjustment"
        })
        
        return {
            "analysis": "Enhanced standard search with contextual intelligence",
            "strategies": strategies,
            "approach": "contextual_standard",
            "contextual_adjustments": adjusted_thresholds
        }
    
    async def _plan_enhanced_contextual_strategy(self, line_item: LineItem,
                                               catalog_context: Dict[str, Any], 
                                               contextual_insights: Dict[str, Any]) -> Dict[str, Any]:
        """Plan enhanced contextual search strategy"""
        # For now, use enhanced standard strategy
        # In future phases, this would include more sophisticated contextual reasoning
        return await self._plan_enhanced_standard_strategy(line_item, catalog_context, contextual_insights)
    
    async def _plan_enhanced_reasoning_strategy(self, line_item: LineItem,
                                              catalog_context: Dict[str, Any],
                                              contextual_insights: Dict[str, Any]) -> Dict[str, Any]:
        """Plan enhanced reasoning strategy - placeholder for Phase 2"""
        logger.info("🧠 Enhanced reasoning strategy requested - using enhanced standard for now")
        return await self._plan_enhanced_standard_strategy(line_item, catalog_context, contextual_insights)
    
    async def _plan_multi_agent_strategy(self, line_item: LineItem,
                                       catalog_context: Dict[str, Any],
                                       contextual_insights: Dict[str, Any]) -> Dict[str, Any]:
        """Plan multi-agent strategy - placeholder for Phase 4"""
        logger.info("🤝 Multi-agent strategy requested - using enhanced standard for now") 
        return await self._plan_enhanced_standard_strategy(line_item, catalog_context, contextual_insights)
    
    async def _execute_contextual_search_plan(self, line_item: LineItem,
                                            search_plan: Dict[str, Any],
                                            contextual_insights: Dict[str, Any]) -> List[SearchResult]:
        """Execute search plan with contextual intelligence enhancements"""
        
        logger.debug("⚡ Executing contextual search plan",
                    line_id=line_item.line_id,
                    strategies_count=len(search_plan.get("strategies", [])),
                    approach=search_plan.get("approach", "unknown"))
        
        # Use the existing execution logic with contextual enhancements
        all_results = await self._execute_search_plan(line_item, search_plan)
        
        # Add contextual metadata to results
        for result in all_results:
            if hasattr(result, 'notes'):
                result.notes.append(f"Processed with contextual intelligence")
                if contextual_insights.get("contextual_insights"):
                    complexity = contextual_insights["contextual_insights"].complexity_level.value
                    business_context = contextual_insights["contextual_insights"].business_context.value
                    result.notes.append(f"Complexity: {complexity}, Context: {business_context}")
        
        return all_results
    
    async def _refine_and_rank_results_with_context(self, line_item: LineItem,
                                                  all_results: List[SearchResult],
                                                  contextual_insights: Dict[str, Any]) -> List[SearchResult]:
        """Refine and rank results with contextual intelligence"""
        
        logger.debug("🎯 Refining results with contextual intelligence",
                    line_id=line_item.line_id,
                    total_results=len(all_results))
        
        if not all_results:
            return []
        
        # Use existing refinement logic as base
        refined_results = await self._refine_and_rank_results(line_item, all_results)
        
        # Apply contextual adjustments to scoring
        contextual_adjustments = contextual_insights.get("adjusted_thresholds", {})
        
        for result in refined_results:
            # Apply contextual scoring adjustments
            original_score = result.similarity_score
            
            # Adjust based on business context
            if contextual_insights.get("contextual_insights"):
                business_context = contextual_insights["contextual_insights"].business_context.value
                
                if business_context == "emergency" and result.availability and result.availability > 0:
                    result.similarity_score = min(1.0, result.similarity_score * 1.15)  # Boost available items for emergencies
                elif business_context == "cost_optimization" and result.unit_price:
                    # Slight penalty for expensive items in cost optimization context
                    if result.unit_price > 100:  # Arbitrary threshold
                        result.similarity_score = max(0.1, result.similarity_score * 0.95)
            
            # Add contextual reasoning to notes
            if hasattr(result, 'notes') and result.similarity_score != original_score:
                result.notes.append(f"Score adjusted by contextual intelligence: {original_score:.3f} → {result.similarity_score:.3f}")
        
        # Re-sort by adjusted scores
        refined_results.sort(key=lambda x: x.similarity_score, reverse=True)
        
        # Re-assign ranks
        for i, result in enumerate(refined_results):
            result.rank = i + 1
        
        logger.info("✨ Results refined with contextual intelligence",
                   line_id=line_item.line_id,
                   final_results=len(refined_results))
        
        return refined_results
    
    async def _contextual_fallback_search_strategy(self, line_item: LineItem) -> List[SearchResult]:
        """Enhanced fallback search strategy with basic contextual intelligence"""
        
        logger.info("🔄 Using contextual fallback search strategy", line_id=line_item.line_id)
        
        try:
            # Basic complexity assessment without full contextual intelligence
            complexity_assessment = await assess_complexity_factors(self._line_item_to_dict(line_item))
            
            # Adjust search based on basic complexity
            if complexity_assessment.get("complexity_level") == "critical":
                # More aggressive search for critical items
                results = await self.search_tools.semantic_vector_search(
                    query=line_item.raw_text,
                    top_k=15,  # More results for critical items
                    min_similarity=0.5  # Lower threshold for critical items
                )
            else:
                # Standard search
                results = await self.search_tools.semantic_vector_search(
                    query=line_item.raw_text,
                    top_k=10
                )
            
            if results:
                # Add contextual fallback notes
                for result in results:
                    if hasattr(result, 'notes'):
                        result.notes.append("Found via contextual fallback strategy")
                        result.notes.append(f"Assessed complexity: {complexity_assessment.get('complexity_level', 'unknown')}")
                
                return results
            
            # If semantic search fails, try fuzzy search
            words = line_item.raw_text.split()[:5]
            results = await self.search_tools.fuzzy_text_search(
                terms=words,
                fuzzy_threshold=50
            )
            
            return results
            
        except Exception as e:
            logger.error("❌ Contextual fallback search failed", error=str(e), line_id=line_item.line_id)
            # Final fallback to original fallback strategy
            return await self._fallback_search_strategy(line_item)
    
    async def _gather_catalog_context(self, line_item: LineItem) -> Dict[str, Any]:
        """Gather context about catalog to inform search strategy"""
        
        logger.debug("📊 Gathering catalog context", line_id=line_item.line_id)
        
        # Get catalog overview
        overview = await self.search_tools.catalog_exploration("overview")
        materials = await self.search_tools.catalog_exploration("materials")
        categories = await self.search_tools.catalog_exploration("categories")
        
        return {
            "catalog_overview": overview,
            "available_materials": materials.get("materials_breakdown", {}),
            "available_categories": categories.get("categories_breakdown", {}),
            "total_parts": overview.get("total_parts", 0)
        }
    
    async def _plan_search_strategy(self, line_item: LineItem, 
                                  catalog_context: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to plan optimal search strategy"""
        
        logger.debug("🧠 Planning search strategy with AI", line_id=line_item.line_id)
        
        # Prepare context for AI planning
        planning_prompt = self._create_planning_prompt(line_item, catalog_context)
        
        try:
            response = await asyncio.to_thread(self.llm.invoke, planning_prompt)
            search_plan = json.loads(response.content)
            
            logger.info("📋 AI search plan generated", 
                       line_id=line_item.line_id,
                       strategies=len(search_plan.get("strategies", [])))
            
            return search_plan
            
        except Exception as e:
            logger.warning("AI planning failed, using heuristic approach", 
                          error=str(e), line_id=line_item.line_id)
            return self._heuristic_search_plan(line_item, catalog_context)
    
    def _create_planning_prompt(self, line_item: LineItem, 
                              catalog_context: Dict[str, Any]) -> str:
        """Create prompt for AI search strategy planning"""
        
        available_materials = list(catalog_context.get("available_materials", {}).keys())
        available_categories = list(catalog_context.get("available_categories", {}).keys())
        
        prompt = f"""
        You are an expert procurement agent planning a search strategy for industrial parts.
        
        LINE ITEM TO SEARCH:
        Raw Text: {line_item.raw_text}
        Project: {line_item.project}
        Urgency: {line_item.urgency}
        Special Requirements: {line_item.special_requirements}
        
        CATALOG CONTEXT:
        Total Parts Available: {catalog_context.get('total_parts', 0)}
        Available Materials: {available_materials[:10]}  # Show first 10
        Available Categories: {available_categories}
        
        AVAILABLE SEARCH TOOLS:
        1. semantic_vector_search - Best for general similarity matching
        2. fuzzy_text_search - Good for part numbers and exact terms
        3. material_category_search - Ideal when material/form is clear
        4. dimensional_search - Use when size is critical
        5. alternative_materials_search - Find substitutes when primary not available
        6. catalog_exploration - Understand what's available
        
        SEARCH STRATEGY PLANNING:
        Plan 3-5 search strategies to maximize finding relevant parts.
        Consider:
        - Start broad, then narrow down
        - Try alternative materials if primary not available
        - Use multiple approaches for better coverage
        - Prioritize strategies based on line item characteristics
        
        Return your plan as JSON:
        {{
            "analysis": "Your reasoning about the line item and search approach",
            "primary_material": "Main material you identified",
            "form_factor": "Shape/form if identifiable", 
            "key_dimensions": {{"dimension": "value"}},
            "strategies": [
                {{
                    "tool": "search_tool_name",
                    "priority": 1-5,
                    "parameters": {{"param": "value"}},
                    "reasoning": "Why this strategy"
                }}
            ],
            "expected_challenges": ["potential issues"],
            "success_criteria": "What would constitute success"
        }}
        
        Focus on finding the best matches even if not perfect. Be creative and thorough.
        """
        
        return prompt
    
    def _heuristic_search_plan(self, line_item: LineItem, 
                             catalog_context: Dict[str, Any]) -> Dict[str, Any]:
        """Create search plan using heuristic rules when AI is unavailable"""
        
        logger.debug("🔧 Creating heuristic search plan", line_id=line_item.line_id)
        
        raw_text = line_item.raw_text.lower()
        strategies = []
        
        # Strategy 1: Always start with semantic search
        strategies.append({
            "tool": "semantic_vector_search",
            "priority": 1,
            "parameters": {"query": line_item.raw_text, "top_k": 10},
            "reasoning": "Broad semantic matching to capture similar parts"
        })
        
        # Strategy 2: If material terms detected, use material search
        material_terms = ["steel", "aluminum", "brass", "copper", "titanium", "4140", "6061", "304", "316"]
        detected_materials = [term for term in material_terms if term in raw_text]
        
        if detected_materials:
            strategies.append({
                "tool": "material_category_search",
                "priority": 2,
                "parameters": {"material": detected_materials[0]},
                "reasoning": f"Material '{detected_materials[0]}' detected in line item"
            })
        
        # Strategy 3: If size/dimensions mentioned, try dimensional search
        dimension_patterns = ["diameter", "length", "width", "thickness", "size", '"', "inch", "mm"]
        if any(pattern in raw_text for pattern in dimension_patterns):
            strategies.append({
                "tool": "dimensional_search",
                "priority": 3,
                "parameters": {"target_dims": {}, "tolerance": 0.3},
                "reasoning": "Dimensional information detected"
            })
        
        # Strategy 4: Fuzzy text search for specific terms
        specific_terms = raw_text.split()[:5]  # First 5 words
        strategies.append({
            "tool": "fuzzy_text_search",
            "priority": 4,
            "parameters": {"terms": specific_terms, "fuzzy_threshold": 60},
            "reasoning": "Fuzzy matching for specific terms"
        })
        
        # Strategy 5: Alternative materials if urgency is high
        if line_item.urgency == "HIGH" and detected_materials:
            strategies.append({
                "tool": "alternative_materials_search",
                "priority": 5,
                "parameters": {"primary_material": detected_materials[0], "application": "urgent"},
                "reasoning": "High urgency - search for alternative materials"
            })
        
        return {
            "analysis": "Heuristic analysis of line item",
            "strategies": strategies,
            "approach": "heuristic"
        }
    
    async def _execute_search_plan(self, line_item: LineItem, 
                                 search_plan: Dict[str, Any]) -> List[SearchResult]:
        """Execute search strategies according to plan"""
        
        logger.debug("⚡ Executing search plan", 
                    line_id=line_item.line_id,
                    strategies_count=len(search_plan.get("strategies", [])))
        
        all_results = []
        strategies = search_plan.get("strategies", [])
        
        # Sort strategies by priority
        strategies.sort(key=lambda x: x.get("priority", 999))
        
        for i, strategy in enumerate(strategies):
            tool_name = strategy.get("tool")
            parameters = strategy.get("parameters", {})
            
            logger.debug(f"🔍 Executing strategy {i+1}/{len(strategies)}: {tool_name}", 
                        line_id=line_item.line_id)
            
            try:
                # Execute the appropriate search tool
                if tool_name == "semantic_vector_search":
                    results = await self.search_tools.semantic_vector_search(**parameters)
                elif tool_name == "fuzzy_text_search":
                    results = await self.search_tools.fuzzy_text_search(**parameters)
                elif tool_name == "material_category_search":
                    results = await self.search_tools.material_category_search(**parameters)
                elif tool_name == "dimensional_search":
                    results = await self.search_tools.dimensional_search(**parameters)
                elif tool_name == "alternative_materials_search":
                    results = await self.search_tools.alternative_materials_search(**parameters)
                else:
                    logger.warning(f"Unknown search tool: {tool_name}")
                    continue
                
                # Tag results with strategy info
                for result in results:
                    result.notes.append(f"Strategy {i+1}: {strategy.get('reasoning', tool_name)}")
                
                all_results.extend(results)
                
                logger.debug(f"✅ Strategy {i+1} completed", 
                           line_id=line_item.line_id,
                           results_found=len(results))
                
                # If we found good results early, we might stop here
                if len(results) >= 5 and any(r.similarity_score > 0.8 for r in results):
                    logger.info("🎯 High-quality results found early, stopping search", 
                               line_id=line_item.line_id)
                    break
                    
            except Exception as e:
                logger.warning(f"Strategy {i+1} failed", 
                             strategy=tool_name, 
                             error=str(e),
                             line_id=line_item.line_id)
                continue
        
        return all_results
    
    async def _refine_and_rank_results(self, line_item: LineItem, 
                                     all_results: List[SearchResult]) -> List[SearchResult]:
        """Refine and rank all search results"""
        
        logger.debug("🎯 Refining and ranking results", 
                    line_id=line_item.line_id,
                    total_results=len(all_results))
        
        if not all_results:
            return []
        
        # Remove duplicates based on part number
        unique_results = {}
        for result in all_results:
            part_num = result.part_number
            if part_num not in unique_results or result.similarity_score > unique_results[part_num].similarity_score:
                unique_results[part_num] = result
        
        # Convert back to list
        refined_results = list(unique_results.values())
        
        # Enhanced ranking algorithm
        for result in refined_results:
            result.similarity_score = self._calculate_enhanced_score(result, line_item)
        
        # Sort by enhanced score
        refined_results.sort(key=lambda x: x.similarity_score, reverse=True)
        
        # Limit to top results and re-rank
        top_results = refined_results[:15]
        for i, result in enumerate(top_results):
            result.rank = i + 1
        
        logger.info("✨ Results refined and ranked", 
                   line_id=line_item.line_id,
                   unique_results=len(top_results))
        
        return top_results
    
    def _calculate_enhanced_score(self, result: SearchResult, line_item: LineItem) -> float:
        """Calculate enhanced similarity score considering multiple factors"""
        
        base_score = result.similarity_score
        
        # Boost for material matches
        if line_item.extracted_specs and line_item.extracted_specs.material_grade:
            material_grade = line_item.extracted_specs.material_grade.lower()
            description_lower = result.description.lower()
            
            if material_grade in description_lower:
                base_score *= 1.2  # 20% boost for material match
        
        # Boost for form factor matches
        if line_item.extracted_specs and line_item.extracted_specs.form:
            form = line_item.extracted_specs.form.lower()
            description_lower = result.description.lower()
            
            if form in description_lower:
                base_score *= 1.1  # 10% boost for form match
        
        # Penalty for very low base scores
        if base_score < 0.3:
            base_score *= 0.8
        
        # Boost for high availability
        if result.availability and result.availability > 100:
            base_score *= 1.05
        
        return min(base_score, 1.0)  # Cap at 1.0
    
    async def _record_successful_pattern(self, line_item: LineItem, 
                                       search_plan: Dict[str, Any], 
                                       results: List[SearchResult]):
        """Record successful search patterns for learning"""
        
        pattern = {
            "line_item_type": self._classify_line_item(line_item),
            "successful_strategies": [s["tool"] for s in search_plan.get("strategies", [])],
            "best_result_score": max(r.similarity_score for r in results) if results else 0,
            "timestamp": logger._context.get("timestamp", "unknown")
        }
        
        self.successful_patterns.append(pattern)
        
        # Keep only recent patterns (last 100)
        if len(self.successful_patterns) > 100:
            self.successful_patterns = self.successful_patterns[-100:]
    
    def _classify_line_item(self, line_item: LineItem) -> str:
        """Classify line item type for pattern learning"""
        
        raw_text = line_item.raw_text.lower()
        
        if any(term in raw_text for term in ["steel", "metal", "alloy"]):
            return "metal_parts"
        elif any(term in raw_text for term in ["aluminum", "aluminium"]):
            return "aluminum_parts"
        elif any(term in raw_text for term in ["diameter", "round", "rod", "bar"]):
            return "cylindrical_parts"
        elif any(term in raw_text for term in ["sheet", "plate"]):
            return "flat_parts"
        else:
            return "general_parts"
    
    async def _fallback_search_strategy(self, line_item: LineItem) -> List[SearchResult]:
        """Fallback search when AI is unavailable"""
        
        logger.info("🔄 Using fallback search strategy", line_id=line_item.line_id)
        
        try:
            # Try semantic search first
            results = await self.search_tools.semantic_vector_search(
                query=line_item.raw_text,
                top_k=10
            )
            
            if results:
                return results
            
            # If no semantic results, try fuzzy search
            words = line_item.raw_text.split()[:5]
            results = await self.search_tools.fuzzy_text_search(
                terms=words,
                fuzzy_threshold=50
            )
            
            if results:
                return results
            
            # Last resort: debug the search pipeline
            debug_info = await self.search_tools.debug_search_pipeline(line_item.raw_text)
            logger.info("🔧 Search debug info", debug_info=debug_info)
            
            return []
            
        except Exception as e:
            logger.error("❌ Fallback search failed", error=str(e), line_id=line_item.line_id)
            return []
    
    async def get_search_statistics(self) -> Dict[str, Any]:
        """Get statistics about search patterns and success"""
        
        return {
            "total_searches": len(self.search_history),
            "successful_patterns": len(self.successful_patterns),
            "pattern_types": {},  # Could analyze patterns by type
            "average_success_rate": 0.0  # Could calculate from history
        }
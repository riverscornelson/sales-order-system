"""
Enhanced MCP Contextual Intelligence Layer
Provides situational awareness and business context understanding for intelligent procurement
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import structlog

logger = structlog.get_logger()

class SituationComplexity(Enum):
    """Situation complexity levels"""
    SIMPLE = "simple"           # Standard part, clear specs
    MODERATE = "moderate"       # Some ambiguity or special requirements
    COMPLEX = "complex"         # Multiple requirements, custom specs
    CRITICAL = "critical"       # High urgency, safety-critical, or regulatory

class BusinessContext(Enum):
    """Business context types"""
    ROUTINE_PROCUREMENT = "routine"
    EMERGENCY_REPLACEMENT = "emergency"
    NEW_PROJECT_STARTUP = "new_project"
    PRODUCTION_LINE_DOWN = "production_down"
    REGULATORY_COMPLIANCE = "regulatory"
    COST_OPTIMIZATION = "cost_optimization"
    SUPPLIER_EVALUATION = "supplier_evaluation"

@dataclass
class ContextualInsights:
    """Comprehensive contextual analysis results"""
    complexity_level: SituationComplexity
    business_context: BusinessContext
    urgency_factors: Dict[str, Any]
    risk_assessment: Dict[str, float]
    recommended_approach: str
    confidence_adjustments: Dict[str, float]
    escalation_triggers: List[str]
    specialized_requirements: List[str]

class ContextualIntelligenceServer:
    """
    MCP server providing contextual intelligence for procurement situations
    Analyzes business context, complexity, and provides strategic guidance
    """
    
    def __init__(self):
        self.customer_patterns = {}  # Will be populated from historical data
        self.industry_profiles = self._load_industry_profiles()
        self.complexity_indicators = self._load_complexity_indicators()
        self.seasonal_patterns = {}
        
    def _load_industry_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Load industry-specific procurement patterns and requirements"""
        return {
            "aerospace": {
                "typical_materials": ["titanium", "aluminum", "composite", "inconel"],
                "certification_requirements": ["AS9100", "NADCAP", "FAA"],
                "quality_standards": "extremely_high",
                "traceability_required": True,
                "typical_lead_times": {"standard": 12, "expedited": 6, "emergency": 2},
                "cost_sensitivity": "low",
                "regulatory_complexity": "high"
            },
            "automotive": {
                "typical_materials": ["steel", "aluminum", "polymer", "composite"],
                "certification_requirements": ["TS16949", "ISO14001"],
                "quality_standards": "high",
                "traceability_required": True,
                "typical_lead_times": {"standard": 8, "expedited": 4, "emergency": 1},
                "cost_sensitivity": "high",
                "regulatory_complexity": "medium"
            },
            "medical": {
                "typical_materials": ["stainless_steel", "titanium", "biocompatible_polymer"],
                "certification_requirements": ["FDA", "ISO13485", "CE_marking"],
                "quality_standards": "extremely_high",
                "traceability_required": True,
                "typical_lead_times": {"standard": 16, "expedited": 8, "emergency": 3},
                "cost_sensitivity": "low",
                "regulatory_complexity": "extremely_high"
            },
            "construction": {
                "typical_materials": ["steel", "concrete", "aluminum", "timber"],
                "certification_requirements": ["ASTM", "local_building_codes"],
                "quality_standards": "medium",
                "traceability_required": False,
                "typical_lead_times": {"standard": 6, "expedited": 3, "emergency": 1},
                "cost_sensitivity": "very_high",
                "regulatory_complexity": "medium"
            },
            "oil_gas": {
                "typical_materials": ["carbon_steel", "stainless_steel", "inconel", "monel"],
                "certification_requirements": ["API", "ASME", "NACE"],
                "quality_standards": "very_high",
                "traceability_required": True,
                "typical_lead_times": {"standard": 14, "expedited": 7, "emergency": 2},
                "cost_sensitivity": "medium",
                "regulatory_complexity": "high"
            }
        }
    
    def _load_complexity_indicators(self) -> Dict[str, List[str]]:
        """Load complexity indicators for different aspects"""
        return {
            "technical_complexity": [
                "custom_specifications", "tight_tolerances", "special_surface_finish",
                "heat_treatment_required", "non_standard_dimensions", "composite_materials",
                "multi_material_assembly", "specialized_coating"
            ],
            "regulatory_complexity": [
                "FDA_approval_required", "aerospace_certification", "pressure_vessel_code",
                "environmental_compliance", "safety_critical_application", "export_controlled",
                "nuclear_qualified", "explosive_atmosphere"
            ],
            "supply_complexity": [
                "limited_suppliers", "long_lead_time", "volatile_pricing", "allocation_risk",
                "geopolitical_risk", "single_source", "custom_tooling_required",
                "minimum_order_quantities"
            ],
            "urgency_indicators": [
                "production_line_down", "safety_issue", "regulatory_deadline",
                "customer_commitment", "project_milestone", "inventory_stockout",
                "equipment_failure", "seasonal_window"
            ]
        }
    
    async def analyze_procurement_context(self, order_data: Dict[str, Any]) -> ContextualInsights:
        """
        Comprehensive contextual analysis of procurement situation
        
        Args:
            order_data: Complete order information including line items, customer, timing
            
        Returns:
            ContextualInsights with full situational analysis
        """
        logger.info("🧠 Analyzing procurement context", 
                   customer=order_data.get("customer", {}).get("name"),
                   line_items_count=len(order_data.get("line_items", [])))
        
        try:
            # Multi-dimensional context analysis
            customer_context = await self._analyze_customer_context(order_data)
            temporal_context = await self._analyze_temporal_context(order_data)
            technical_context = await self._analyze_technical_context(order_data)
            business_context = await self._analyze_business_context(order_data)
            
            # Determine overall complexity
            complexity_level = self._assess_overall_complexity(
                customer_context, temporal_context, technical_context, business_context
            )
            
            # Generate strategic recommendations
            strategic_insights = await self._generate_strategic_insights(
                complexity_level, customer_context, temporal_context, 
                technical_context, business_context
            )
            
            insights = ContextualInsights(
                complexity_level=complexity_level,
                business_context=business_context["primary_context"],
                urgency_factors=temporal_context["urgency_factors"],
                risk_assessment=strategic_insights["risk_assessment"],
                recommended_approach=strategic_insights["recommended_approach"],
                confidence_adjustments=strategic_insights["confidence_adjustments"],
                escalation_triggers=strategic_insights["escalation_triggers"],
                specialized_requirements=technical_context["specialized_requirements"]
            )
            
            logger.info("✅ Contextual analysis completed",
                       complexity=complexity_level.value,
                       business_context=business_context["primary_context"].value,
                       recommended_approach=insights.recommended_approach)
            
            return insights
            
        except Exception as e:
            logger.error("❌ Contextual analysis failed", error=str(e))
            # Return basic insights as fallback
            return ContextualInsights(
                complexity_level=SituationComplexity.MODERATE,
                business_context=BusinessContext.ROUTINE_PROCUREMENT,
                urgency_factors={},
                risk_assessment={},
                recommended_approach="standard_search",
                confidence_adjustments={},
                escalation_triggers=[],
                specialized_requirements=[]
            )
    
    async def _analyze_customer_context(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze customer-specific context and patterns"""
        
        customer_info = order_data.get("customer", {})
        customer_name = customer_info.get("name", "unknown")
        
        # Get customer's historical patterns (would integrate with CRM/ERP)
        customer_profile = self.customer_patterns.get(customer_name, {})
        
        # Determine industry from customer profile or infer from order
        industry = self._identify_customer_industry(customer_info, order_data)
        industry_profile = self.industry_profiles.get(industry, {})
        
        return {
            "customer_name": customer_name,
            "industry": industry,
            "industry_profile": industry_profile,
            "procurement_history": customer_profile.get("procurement_history", {}),
            "preferred_suppliers": customer_profile.get("preferred_suppliers", []),
            "quality_requirements": industry_profile.get("quality_standards", "medium"),
            "certification_needs": industry_profile.get("certification_requirements", []),
            "cost_sensitivity": industry_profile.get("cost_sensitivity", "medium"),
            "typical_lead_times": industry_profile.get("typical_lead_times", {})
        }
    
    async def _analyze_temporal_context(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze time-related factors and urgency"""
        
        current_time = datetime.now()
        urgency_factors = {}
        
        # Analyze delivery requirements
        delivery_date = order_data.get("delivery_date")
        if delivery_date:
            try:
                target_date = datetime.fromisoformat(delivery_date)
                days_available = (target_date - current_time).days
                
                urgency_factors["delivery_urgency"] = {
                    "days_available": days_available,
                    "urgency_level": self._classify_delivery_urgency(days_available)
                }
            except:
                urgency_factors["delivery_urgency"] = {"urgency_level": "unknown"}
        
        # Check for urgency keywords
        urgency_keywords = order_data.get("urgency_indicators", [])
        for item in order_data.get("line_items", []):
            raw_text = item.get("raw_text", "").lower()
            
            if any(keyword in raw_text for keyword in ["urgent", "asap", "rush", "emergency"]):
                urgency_keywords.append("explicit_urgency_request")
            
            if any(keyword in raw_text for keyword in ["production down", "line down", "critical"]):
                urgency_keywords.append("production_impact")
        
        urgency_factors["keyword_indicators"] = urgency_keywords
        
        # Seasonal factors
        seasonal_impact = self._assess_seasonal_impact(current_time)
        urgency_factors["seasonal_factors"] = seasonal_impact
        
        return {
            "current_time": current_time,
            "urgency_factors": urgency_factors,
            "business_hours": self._is_business_hours(current_time),
            "holiday_impact": self._assess_holiday_impact(current_time)
        }
    
    async def _analyze_technical_context(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze technical complexity and requirements"""
        
        technical_indicators = {
            "complexity_score": 0,
            "specialized_requirements": [],
            "regulatory_requirements": [],
            "quality_indicators": []
        }
        
        for item in order_data.get("line_items", []):
            raw_text = item.get("raw_text", "").lower()
            extracted_specs = item.get("extracted_specs", {})
            
            # Check technical complexity indicators
            for category, indicators in self.complexity_indicators.items():
                for indicator in indicators:
                    if indicator.lower().replace("_", " ") in raw_text:
                        technical_indicators["complexity_score"] += 1
                        
                        if category == "technical_complexity":
                            technical_indicators["specialized_requirements"].append(indicator)
                        elif category == "regulatory_complexity":
                            technical_indicators["regulatory_requirements"].append(indicator)
            
            # Analyze specifications complexity
            if extracted_specs:
                if extracted_specs.get("tolerances"):
                    technical_indicators["complexity_score"] += 2
                    technical_indicators["specialized_requirements"].append("tight_tolerances")
                
                if extracted_specs.get("certifications"):
                    technical_indicators["complexity_score"] += 1
                    technical_indicators["regulatory_requirements"].extend(
                        extracted_specs["certifications"]
                    )
                
                if extracted_specs.get("special_requirements"):
                    technical_indicators["complexity_score"] += 1
                    technical_indicators["specialized_requirements"].extend(
                        extracted_specs["special_requirements"]
                    )
        
        return technical_indicators
    
    async def _analyze_business_context(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Determine primary business context and implications"""
        
        # Analyze order characteristics to determine business context
        urgency_indicators = []
        project_indicators = []
        cost_indicators = []
        
        for item in order_data.get("line_items", []):
            raw_text = item.get("raw_text", "").lower()
            
            # Urgency/emergency context
            if any(word in raw_text for word in ["emergency", "breakdown", "failure", "asap"]):
                urgency_indicators.append("emergency_replacement")
            
            if any(word in raw_text for word in ["production", "line down", "shutdown"]):
                urgency_indicators.append("production_impact")
            
            # Project context
            if any(word in raw_text for word in ["project", "new installation", "startup"]):
                project_indicators.append("new_project")
            
            # Cost context
            if any(word in raw_text for word in ["quote", "budget", "cost effective", "economic"]):
                cost_indicators.append("cost_optimization")
        
        # Determine primary business context
        if urgency_indicators:
            if "production_impact" in urgency_indicators:
                primary_context = BusinessContext.PRODUCTION_LINE_DOWN
            else:
                primary_context = BusinessContext.EMERGENCY_REPLACEMENT
        elif project_indicators:
            primary_context = BusinessContext.NEW_PROJECT_STARTUP
        elif cost_indicators:
            primary_context = BusinessContext.COST_OPTIMIZATION
        else:
            primary_context = BusinessContext.ROUTINE_PROCUREMENT
        
        return {
            "primary_context": primary_context,
            "urgency_indicators": urgency_indicators,
            "project_indicators": project_indicators,
            "cost_indicators": cost_indicators
        }
    
    def _assess_overall_complexity(self, customer_context: Dict, temporal_context: Dict,
                                 technical_context: Dict, business_context: Dict) -> SituationComplexity:
        """Assess overall situation complexity based on all factors"""
        
        complexity_score = 0
        
        # Technical complexity
        complexity_score += technical_context["complexity_score"]
        
        # Urgency complexity
        urgency_factors = temporal_context["urgency_factors"]
        if urgency_factors.get("delivery_urgency", {}).get("urgency_level") == "critical":
            complexity_score += 3
        elif urgency_factors.get("delivery_urgency", {}).get("urgency_level") == "high":
            complexity_score += 2
        
        # Business context complexity
        if business_context["primary_context"] in [BusinessContext.PRODUCTION_LINE_DOWN, 
                                                   BusinessContext.EMERGENCY_REPLACEMENT]:
            complexity_score += 3
        elif business_context["primary_context"] == BusinessContext.REGULATORY_COMPLIANCE:
            complexity_score += 2
        
        # Industry complexity
        industry_profile = customer_context.get("industry_profile", {})
        if industry_profile.get("regulatory_complexity") == "extremely_high":
            complexity_score += 3
        elif industry_profile.get("regulatory_complexity") == "high":
            complexity_score += 2
        
        # Map score to complexity level
        if complexity_score >= 8:
            return SituationComplexity.CRITICAL
        elif complexity_score >= 5:
            return SituationComplexity.COMPLEX
        elif complexity_score >= 2:
            return SituationComplexity.MODERATE
        else:
            return SituationComplexity.SIMPLE
    
    async def _generate_strategic_insights(self, complexity_level: SituationComplexity,
                                         customer_context: Dict, temporal_context: Dict,
                                         technical_context: Dict, business_context: Dict) -> Dict[str, Any]:
        """Generate strategic insights and recommendations"""
        
        insights = {
            "risk_assessment": {},
            "recommended_approach": "standard_search",
            "confidence_adjustments": {},
            "escalation_triggers": []
        }
        
        # Risk assessment
        insights["risk_assessment"] = {
            "technical_risk": min(technical_context["complexity_score"] / 10, 1.0),
            "time_risk": self._assess_time_risk(temporal_context),
            "supplier_risk": self._assess_supplier_risk(customer_context),
            "regulatory_risk": len(technical_context["regulatory_requirements"]) / 5
        }
        
        # Recommended approach based on complexity
        if complexity_level == SituationComplexity.CRITICAL:
            insights["recommended_approach"] = "multi_agent_collaboration"
            insights["escalation_triggers"].append("critical_complexity")
        elif complexity_level == SituationComplexity.COMPLEX:
            insights["recommended_approach"] = "enhanced_reasoning_chain"
        elif complexity_level == SituationComplexity.MODERATE:
            insights["recommended_approach"] = "contextual_search"
        else:
            insights["recommended_approach"] = "standard_search"
        
        # Confidence adjustments based on context
        if business_context["primary_context"] == BusinessContext.EMERGENCY_REPLACEMENT:
            insights["confidence_adjustments"]["speed_over_precision"] = 0.8
        elif business_context["primary_context"] == BusinessContext.COST_OPTIMIZATION:
            insights["confidence_adjustments"]["cost_sensitivity"] = 1.2
        
        # Escalation triggers
        if technical_context["regulatory_requirements"]:
            insights["escalation_triggers"].append("regulatory_requirements")
        
        if insights["risk_assessment"]["time_risk"] > 0.8:
            insights["escalation_triggers"].append("time_critical")
        
        return insights
    
    # Helper methods
    def _identify_customer_industry(self, customer_info: Dict, order_data: Dict) -> str:
        """Identify customer industry from available information"""
        # Could integrate with CRM data or use ML classification
        # For now, use simple keyword matching
        
        customer_name = customer_info.get("name", "").lower()
        
        if any(keyword in customer_name for keyword in ["aerospace", "aviation", "boeing", "airbus"]):
            return "aerospace"
        elif any(keyword in customer_name for keyword in ["automotive", "ford", "gm", "toyota"]):
            return "automotive"
        elif any(keyword in customer_name for keyword in ["medical", "hospital", "pharmaceutical"]):
            return "medical"
        elif any(keyword in customer_name for keyword in ["construction", "building", "concrete"]):
            return "construction"
        elif any(keyword in customer_name for keyword in ["oil", "gas", "petroleum", "refinery"]):
            return "oil_gas"
        else:
            return "general_manufacturing"  # Default
    
    def _classify_delivery_urgency(self, days_available: int) -> str:
        """Classify delivery urgency based on days available"""
        if days_available < 1:
            return "critical"
        elif days_available < 3:
            return "high"
        elif days_available < 7:
            return "medium"
        else:
            return "low"
    
    def _assess_seasonal_impact(self, current_time: datetime) -> Dict[str, Any]:
        """Assess seasonal factors affecting procurement"""
        month = current_time.month
        
        seasonal_factors = {}
        
        # Year-end factors
        if month == 12:
            seasonal_factors["year_end_budget_push"] = True
            seasonal_factors["holiday_supply_constraints"] = True
        
        # Summer manufacturing slowdown
        if month in [7, 8]:
            seasonal_factors["summer_vacation_impact"] = True
        
        # Q1 budget constraints
        if month in [1, 2]:
            seasonal_factors["q1_budget_constraints"] = True
        
        return seasonal_factors
    
    def _is_business_hours(self, current_time: datetime) -> bool:
        """Check if current time is within business hours"""
        return 8 <= current_time.hour <= 17 and current_time.weekday() < 5
    
    def _assess_holiday_impact(self, current_time: datetime) -> Dict[str, Any]:
        """Assess impact of holidays on procurement"""
        # Simplified holiday detection - in production would use holiday calendar
        holiday_impact = {}
        
        # Major US holidays that affect manufacturing
        month_day = (current_time.month, current_time.day)
        
        major_holidays = [
            (1, 1),   # New Year's Day
            (7, 4),   # Independence Day
            (12, 25), # Christmas
        ]
        
        if month_day in major_holidays:
            holiday_impact["major_holiday"] = True
            holiday_impact["supply_chain_impact"] = "high"
        
        return holiday_impact
    
    def _assess_time_risk(self, temporal_context: Dict) -> float:
        """Assess time-related risk factors"""
        urgency_factors = temporal_context.get("urgency_factors", {})
        
        delivery_urgency = urgency_factors.get("delivery_urgency", {})
        urgency_level = delivery_urgency.get("urgency_level", "low")
        
        urgency_risk_map = {
            "critical": 1.0,
            "high": 0.8,
            "medium": 0.5,
            "low": 0.2,
            "unknown": 0.3
        }
        
        base_risk = urgency_risk_map.get(urgency_level, 0.3)
        
        # Adjust for keyword indicators
        keyword_indicators = urgency_factors.get("keyword_indicators", [])
        if "production_impact" in keyword_indicators:
            base_risk += 0.2
        if "explicit_urgency_request" in keyword_indicators:
            base_risk += 0.1
        
        return min(base_risk, 1.0)
    
    def _assess_supplier_risk(self, customer_context: Dict) -> float:
        """Assess supplier-related risk factors"""
        # Simplified risk assessment - in production would integrate with supplier data
        industry = customer_context.get("industry", "general_manufacturing")
        
        # Some industries have more supplier constraints
        high_risk_industries = ["aerospace", "medical", "oil_gas"]
        
        if industry in high_risk_industries:
            return 0.7
        else:
            return 0.3


# MCP Tool Functions
async def assess_complexity_factors(line_item: Dict[str, Any]) -> Dict[str, Any]:
    """
    MCP Tool: Evaluate complexity indicators for a line item
    
    Args:
        line_item: Line item data with specifications
        
    Returns:
        Complexity assessment with factors and recommendations
    """
    contextual_intelligence = ContextualIntelligenceServer()
    
    # Create a minimal order structure for analysis
    order_data = {
        "line_items": [line_item],
        "customer": {},
        "delivery_date": None
    }
    
    insights = await contextual_intelligence.analyze_procurement_context(order_data)
    
    return {
        "complexity_level": insights.complexity_level.value,
        "specialized_requirements": insights.specialized_requirements,
        "recommended_approach": insights.recommended_approach,
        "risk_factors": insights.risk_assessment,
        "escalation_needed": len(insights.escalation_triggers) > 0,
        "escalation_triggers": insights.escalation_triggers
    }


async def dynamic_threshold_adjustment(context: Dict[str, Any]) -> Dict[str, float]:
    """
    MCP Tool: Adjust search thresholds based on contextual factors
    
    Args:
        context: Contextual information including urgency, quality requirements
        
    Returns:
        Adjusted threshold values for different search strategies
    """
    base_thresholds = {
        "semantic_similarity": 0.7,
        "fuzzy_match": 0.8,
        "dimensional_tolerance": 0.1,
        "material_match": 0.9
    }
    
    adjusted_thresholds = base_thresholds.copy()
    
    # Adjust based on urgency
    urgency_level = context.get("urgency_level", "medium")
    if urgency_level == "critical":
        # Lower thresholds for critical urgency
        for key in adjusted_thresholds:
            adjusted_thresholds[key] *= 0.7
    elif urgency_level == "low":
        # Raise thresholds for non-urgent requests
        for key in adjusted_thresholds:
            adjusted_thresholds[key] *= 1.1
    
    # Adjust based on quality requirements
    quality_level = context.get("quality_requirements", "medium")
    if quality_level in ["extremely_high", "very_high"]:
        # Raise thresholds for high quality requirements
        adjusted_thresholds["material_match"] = min(0.95, adjusted_thresholds["material_match"] * 1.1)
        adjusted_thresholds["dimensional_tolerance"] *= 0.5  # Tighter tolerance
    
    # Adjust based on cost sensitivity
    cost_sensitivity = context.get("cost_sensitivity", "medium")
    if cost_sensitivity in ["high", "very_high"]:
        # Be more flexible on exact matches to find cost alternatives
        adjusted_thresholds["semantic_similarity"] *= 0.9
        adjusted_thresholds["material_match"] *= 0.9
    
    return adjusted_thresholds
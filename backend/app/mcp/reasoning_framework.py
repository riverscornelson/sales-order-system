"""
Phase 2: Multi-Step Reasoning Framework for Sales Order Intelligence
Provides intelligent requirement decomposition, hypothesis generation, and fulfillment strategy validation
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import structlog
import re

logger = structlog.get_logger()
import re
import structlog
from datetime import datetime

logger = structlog.get_logger()

class ReasoningStage(Enum):
    """Stages in the reasoning process"""
    REQUIREMENT_ANALYSIS = "requirement_analysis"
    DECOMPOSITION = "decomposition"
    HYPOTHESIS_GENERATION = "hypothesis_generation"
    EVIDENCE_GATHERING = "evidence_gathering"
    VALIDATION = "validation"
    SYNTHESIS = "synthesis"

class RequirementType(Enum):
    """Types of requirements identified"""
    PRIMARY_FUNCTIONAL = "primary_functional"      # Core material/part function
    SECONDARY_COMPATIBILITY = "secondary_compatibility"  # Compatibility constraints
    ENVIRONMENTAL = "environmental"               # Operating environment
    REGULATORY = "regulatory"                    # Standards and certifications
    DIMENSIONAL = "dimensional"                  # Size and geometry
    QUALITY = "quality"                         # Quality and surface finish
    ECONOMIC = "economic"                       # Cost and lead time

class HypothesisType(Enum):
    """Types of procurement hypotheses"""
    DIRECT_MATCH = "direct_match"               # Exact specification match
    SUBSTITUTE_MATERIAL = "substitute_material"  # Alternative material
    EQUIVALENT_PART = "equivalent_part"         # Functionally equivalent
    MULTI_PART_SOLUTION = "multi_part_solution" # Multiple parts assembly
    CUSTOM_FABRICATION = "custom_fabrication"   # Custom manufacturing

@dataclass
class RequirementComponent:
    """Individual requirement component"""
    component_id: str
    type: RequirementType
    description: str
    priority: float  # 0-1, higher is more critical
    constraints: Dict[str, Any]
    source_text: str
    confidence: float  # 0-1, confidence in extraction
    alternatives: List[str] = field(default_factory=list)

@dataclass
class ProcurementHypothesis:
    """A potential procurement approach"""
    hypothesis_id: str
    type: HypothesisType
    description: str
    target_requirements: List[str]  # requirement_component_ids
    search_strategy: str
    parameters: Dict[str, Any]
    expected_confidence: float
    risk_factors: List[str]
    advantages: List[str]
    disadvantages: List[str]

@dataclass
class ReasoningChain:
    """Complete reasoning chain for a procurement decision"""
    chain_id: str
    original_requirement: str
    requirement_components: List[RequirementComponent]
    hypotheses: List[ProcurementHypothesis]
    evidence: Dict[str, Any]
    conclusions: List[str]
    confidence: float
    reasoning_path: List[str]
    validation_results: Dict[str, Any]

class ReasoningChainServer:
    """
    MCP server for complex reasoning workflows
    Decomposes requirements, generates hypotheses, validates reasoning
    """
    
    def __init__(self):
        self.material_equivalencies = self._load_material_equivalencies()
        self.technical_patterns = self._load_technical_patterns()
        self.reasoning_templates = self._load_reasoning_templates()
        self.validation_rules = self._load_validation_rules()
        
    def _load_material_equivalencies(self) -> Dict[str, List[str]]:
        """Load material equivalency mappings"""
        return {
            "4140": ["4340", "4130", "8620", "4320"],
            "6061": ["6063", "6082", "6005"],
            "304": ["316", "316L", "321", "347"],
            "A36": ["A572", "A992", "A588"],
            "aluminum": ["6061", "2024", "7075", "5052"],
            "steel": ["carbon_steel", "alloy_steel", "tool_steel"],
            "stainless": ["304", "316", "316L", "410", "420"]
        }
    
    def _load_technical_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load patterns for technical requirement identification"""
        return {
            "dimensional_patterns": {
                "diameter": [r"(\d+\.?\d*)\s*(?:inch|in|\")\s*(?:dia|diameter)", 
                           r"(\d+\.?\d*)\s*mm\s*(?:dia|diameter)"],
                "length": [r"(\d+\.?\d*)\s*(?:inch|in|\")\s*(?:long|length)",
                          r"(\d+\.?\d*)\s*mm\s*(?:long|length)"],
                "thickness": [r"(\d+\.?\d*)\s*(?:inch|in|\")\s*(?:thick|thickness)",
                            r"(\d+\.?\d*)\s*mm\s*(?:thick|thickness)"],
                "width": [r"(\d+\.?\d*)\s*(?:inch|in|\")\s*(?:wide|width)",
                         r"(\d+\.?\d*)\s*mm\s*(?:wide|width)"]
            },
            "material_patterns": {
                "steel_grades": [r"(?:AISI\s*)?(\d{4})", r"A(\d{2,3})", r"(A\d{2,3})"],
                "aluminum_grades": [r"(\d{4})", r"Al\s*(\d{4})"],
                "stainless_grades": [r"(3\d{2}L?)", r"SS\s*(3\d{2}L?)"],
                "material_forms": [r"\b(bar|rod|sheet|plate|tube|pipe|angle|channel)\b"]
            },
            "tolerance_patterns": {
                "plus_minus": [r"±\s*(\d+\.?\d*)", r"\+/-\s*(\d+\.?\d*)"],
                "decimal_places": [r"(\d+\.\d{3,})", r"to\s*(\d+\.\d{3,})"]
            },
            "surface_finish_patterns": {
                "ra_values": [r"(\d+\.?\d*)\s*(?:Ra|RA|ra)", r"(\d+\.?\d*)\s*μin"],
                "finish_types": [r"\b(mill|machined|polished|ground|turned)\b"]
            }
        }
    
    def _load_reasoning_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load reasoning templates for different scenarios"""
        return {
            "standard_material_search": {
                "description": "Standard approach for common materials with clear specifications",
                "steps": [
                    "identify_primary_material",
                    "extract_dimensions",
                    "determine_form_factor",
                    "check_availability",
                    "validate_specifications"
                ],
                "decision_points": ["material_substitution_acceptable", "dimensional_tolerance"]
            },
            "complex_assembly": {
                "description": "Multi-component analysis for complex assemblies",
                "steps": [
                    "decompose_assembly",
                    "identify_critical_interfaces",
                    "analyze_individual_components",
                    "evaluate_assembly_constraints",
                    "synthesize_solution"
                ],
                "decision_points": ["component_interdependencies", "assembly_feasibility"]
            },
            "regulatory_compliance": {
                "description": "Analysis requiring regulatory compliance verification",
                "steps": [
                    "identify_regulatory_requirements",
                    "map_compliance_standards",
                    "verify_certification_needs",
                    "validate_traceability",
                    "confirm_documentation"
                ],
                "decision_points": ["compliance_criticality", "certification_availability"]
            }
        }
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules for reasoning quality"""
        return {
            "completeness_check": {
                "min_requirements_identified": 3,
                "min_hypotheses_generated": 2,
                "required_evidence_types": ["technical", "availability", "compatibility"]
            },
            "consistency_check": {
                "material_consistency": True,
                "dimensional_consistency": True,
                "regulatory_consistency": True
            },
            "feasibility_check": {
                "technical_feasibility": 0.7,
                "commercial_feasibility": 0.6,
                "timeline_feasibility": 0.8
            }
        }
    
    async def decompose_complex_requirement(self, requirement: str) -> List[RequirementComponent]:
        """
        MCP Tool: Break down complex specs into searchable components
        
        Args:
            requirement: Raw text requirement description
            
        Returns:
            List of identified requirement components
        """
        logger.info("🔍 Decomposing complex requirement", 
                   requirement_length=len(requirement))
        
        try:
            # Phase 1: Initial parsing and pattern recognition
            parsed_elements = await self._parse_requirement_elements(requirement)
            
            # Phase 2: Classify and prioritize components
            requirement_components = await self._classify_requirements(
                parsed_elements, requirement
            )
            
            # Phase 3: Identify relationships and constraints
            enhanced_components = await self._enhance_with_relationships(
                requirement_components
            )
            
            # Phase 4: Validate completeness
            validated_components = await self._validate_requirement_completeness(
                enhanced_components, requirement
            )
            
            logger.info("✅ Requirement decomposition completed",
                       components_identified=len(validated_components),
                       primary_components=len([c for c in validated_components 
                                             if c.type == RequirementType.PRIMARY_FUNCTIONAL]))
            
            return validated_components
            
        except Exception as e:
            logger.error("❌ Requirement decomposition failed", error=str(e))
            # Return basic component as fallback
            return [RequirementComponent(
                component_id="fallback_001",
                type=RequirementType.PRIMARY_FUNCTIONAL,
                description=requirement,
                priority=1.0,
                constraints={},
                source_text=requirement,
                confidence=0.3
            )]
    
    async def generate_hypothesis_space(self, problem: Dict[str, Any]) -> List[ProcurementHypothesis]:
        """
        MCP Tool: Generate multiple procurement hypotheses
        
        Args:
            problem: Problem definition with line_item, context, components
            
        Returns:
            List of procurement hypotheses to explore
        """
        logger.info("🧠 Generating procurement hypothesis space",
                   line_item=problem.get("line_item", {}).get("raw_text", "")[:50])
        
        try:
            line_item = problem.get("line_item", {})
            complexity = problem.get("complexity", {})
            components = problem.get("components", [])
            
            hypotheses = []
            
            # Hypothesis 1: Direct Match Strategy
            if complexity.get("complexity_level", "moderate") in ["simple", "moderate"]:
                direct_match = await self._generate_direct_match_hypothesis(
                    line_item, components
                )
                hypotheses.append(direct_match)
            
            # Hypothesis 2: Material Substitution Strategy
            material_sub = await self._generate_substitution_hypothesis(
                line_item, components
            )
            if material_sub:
                hypotheses.append(material_sub)
            
            # Hypothesis 3: Equivalent Part Strategy
            equivalent_part = await self._generate_equivalent_part_hypothesis(
                line_item, components
            )
            if equivalent_part:
                hypotheses.append(equivalent_part)
            
            # Hypothesis 4: Multi-Part Solution (for complex requirements)
            if complexity.get("complexity_level", "moderate") in ["complex", "critical"]:
                multi_part = await self._generate_multi_part_hypothesis(
                    line_item, components
                )
                if multi_part:
                    hypotheses.append(multi_part)
            
            # Hypothesis 5: Custom Fabrication (last resort)
            if len(hypotheses) < 2 or complexity.get("complexity_level") == "critical":
                custom_fab = await self._generate_custom_fabrication_hypothesis(
                    line_item, components
                )
                hypotheses.append(custom_fab)
            
            # Rank hypotheses by expected success
            ranked_hypotheses = await self._rank_hypotheses(hypotheses, problem)
            
            logger.info("✅ Hypothesis generation completed",
                       hypotheses_generated=len(ranked_hypotheses),
                       primary_strategy=ranked_hypotheses[0].type.value if ranked_hypotheses else "none")
            
            return ranked_hypotheses
            
        except Exception as e:
            logger.error("❌ Hypothesis generation failed", error=str(e))
            return []
    
    async def validate_reasoning_path(self, reasoning_chain: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        MCP Tool: Validate reasoning quality and identify gaps
        
        Args:
            reasoning_chain: Chain of reasoning steps and decisions
            
        Returns:
            Validation results with quality assessment and recommendations
        """
        logger.info("✅ Validating reasoning path", steps=len(reasoning_chain))
        
        try:
            validation_results = {
                "overall_quality": "unknown",
                "completeness_score": 0.0,
                "consistency_score": 0.0,
                "feasibility_score": 0.0,
                "gaps_identified": [],
                "strengths": [],
                "recommendations": []
            }
            
            # Validate completeness
            completeness = await self._validate_completeness(reasoning_chain)
            validation_results["completeness_score"] = completeness["score"]
            validation_results["gaps_identified"].extend(completeness["gaps"])
            
            # Validate consistency
            consistency = await self._validate_consistency(reasoning_chain)
            validation_results["consistency_score"] = consistency["score"]
            
            # Validate feasibility
            feasibility = await self._validate_feasibility(reasoning_chain)
            validation_results["feasibility_score"] = feasibility["score"]
            
            # Calculate overall quality
            overall_score = (
                validation_results["completeness_score"] * 0.4 +
                validation_results["consistency_score"] * 0.3 +
                validation_results["feasibility_score"] * 0.3
            )
            
            if overall_score >= 0.8:
                validation_results["overall_quality"] = "high"
            elif overall_score >= 0.6:
                validation_results["overall_quality"] = "medium"
            elif overall_score >= 0.4:
                validation_results["overall_quality"] = "low"
            else:
                validation_results["overall_quality"] = "insufficient"
            
            # Generate recommendations
            recommendations = await self._generate_validation_recommendations(
                validation_results
            )
            validation_results["recommendations"] = recommendations
            
            logger.info("✅ Reasoning validation completed",
                       overall_quality=validation_results["overall_quality"],
                       completeness=validation_results["completeness_score"],
                       gaps=len(validation_results["gaps_identified"]))
            
            return validation_results
            
        except Exception as e:
            logger.error("❌ Reasoning validation failed", error=str(e))
            return {
                "overall_quality": "error",
                "error": str(e),
                "recommendations": ["Manual review required due to validation error"]
            }
    
    # Implementation methods
    
    async def _parse_requirement_elements(self, requirement: str) -> Dict[str, Any]:
        """Parse requirement text to extract structured elements"""
        
        elements = {
            "materials": [],
            "dimensions": {},
            "tolerances": {},
            "surface_finish": [],
            "quantities": [],
            "special_requirements": [],
            "regulatory_requirements": []
        }
        
        requirement_lower = requirement.lower()
        
        # Extract materials using patterns
        for material_type, patterns in self.technical_patterns["material_patterns"].items():
            for pattern in patterns:
                matches = re.findall(pattern, requirement, re.IGNORECASE)
                if matches:
                    elements["materials"].extend(matches)
        
        # Extract dimensions
        for dim_type, patterns in self.technical_patterns["dimensional_patterns"].items():
            for pattern in patterns:
                matches = re.findall(pattern, requirement, re.IGNORECASE)
                if matches:
                    elements["dimensions"][dim_type] = matches[0]  # Take first match
        
        # Extract tolerances
        for tol_type, patterns in self.technical_patterns["tolerance_patterns"].items():
            for pattern in patterns:
                matches = re.findall(pattern, requirement, re.IGNORECASE)
                if matches:
                    elements["tolerances"][tol_type] = matches[0]
        
        # Extract surface finish
        for finish_type, patterns in self.technical_patterns["surface_finish_patterns"].items():
            for pattern in patterns:
                matches = re.findall(pattern, requirement, re.IGNORECASE)
                if matches:
                    elements["surface_finish"].extend(matches)
        
        # Extract quantities
        quantity_patterns = [r"(\d+)\s*(?:pieces|pcs|each|ea)", r"qty:?\s*(\d+)"]
        for pattern in quantity_patterns:
            matches = re.findall(pattern, requirement, re.IGNORECASE)
            if matches:
                elements["quantities"].extend([int(m) for m in matches])
        
        # Identify special requirements
        special_keywords = [
            "heat treat", "anodized", "plated", "certified", "traceable",
            "mil-spec", "aerospace", "medical grade", "food grade"
        ]
        for keyword in special_keywords:
            if keyword in requirement_lower:
                elements["special_requirements"].append(keyword)
        
        # Identify regulatory requirements
        regulatory_keywords = [
            "astm", "asme", "api", "iso", "din", "fda", "ce marking",
            "rohs", "reach", "mil-std", "nist"
        ]
        for keyword in regulatory_keywords:
            if keyword in requirement_lower:
                elements["regulatory_requirements"].append(keyword)
        
        return elements
    
    async def _classify_requirements(self, parsed_elements: Dict[str, Any], 
                                   original_text: str) -> List[RequirementComponent]:
        """Classify parsed elements into requirement components"""
        
        components = []
        component_id_counter = 1
        
        # Primary functional requirements (materials)
        if parsed_elements["materials"]:
            for material in parsed_elements["materials"]:
                component = RequirementComponent(
                    component_id=f"req_{component_id_counter:03d}",
                    type=RequirementType.PRIMARY_FUNCTIONAL,
                    description=f"Material requirement: {material}",
                    priority=1.0,
                    constraints={"material": material},
                    source_text=original_text,
                    confidence=0.9,
                    alternatives=self.material_equivalencies.get(material.lower(), [])
                )
                components.append(component)
                component_id_counter += 1
        
        # Dimensional requirements
        if parsed_elements["dimensions"]:
            for dim_type, value in parsed_elements["dimensions"].items():
                component = RequirementComponent(
                    component_id=f"req_{component_id_counter:03d}",
                    type=RequirementType.DIMENSIONAL,
                    description=f"Dimensional requirement: {dim_type} = {value}",
                    priority=0.8,
                    constraints={dim_type: value},
                    source_text=original_text,
                    confidence=0.8
                )
                components.append(component)
                component_id_counter += 1
        
        # Quality requirements (tolerances, surface finish)
        if parsed_elements["tolerances"] or parsed_elements["surface_finish"]:
            quality_constraints = {}
            quality_constraints.update(parsed_elements["tolerances"])
            
            if parsed_elements["surface_finish"]:
                quality_constraints["surface_finish"] = parsed_elements["surface_finish"]
            
            component = RequirementComponent(
                component_id=f"req_{component_id_counter:03d}",
                type=RequirementType.QUALITY,
                description="Quality and precision requirements",
                priority=0.7,
                constraints=quality_constraints,
                source_text=original_text,
                confidence=0.7
            )
            components.append(component)
            component_id_counter += 1
        
        # Regulatory requirements
        if parsed_elements["regulatory_requirements"]:
            component = RequirementComponent(
                component_id=f"req_{component_id_counter:03d}",
                type=RequirementType.REGULATORY,
                description="Regulatory compliance requirements",
                priority=0.9,
                constraints={"standards": parsed_elements["regulatory_requirements"]},
                source_text=original_text,
                confidence=0.8
            )
            components.append(component)
            component_id_counter += 1
        
        return components
    
    async def _enhance_with_relationships(self, components: List[RequirementComponent]) -> List[RequirementComponent]:
        """Enhance components with relationship analysis"""
        
        # For now, return components as-is
        # In full implementation, would analyze interdependencies
        return components
    
    async def _validate_requirement_completeness(self, components: List[RequirementComponent], 
                                               original_text: str) -> List[RequirementComponent]:
        """Validate that requirement decomposition is complete"""
        
        # Check for missing critical components
        component_types = {comp.type for comp in components}
        
        # If no primary functional requirement identified, create one
        if RequirementType.PRIMARY_FUNCTIONAL not in component_types:
            fallback_component = RequirementComponent(
                component_id="req_fallback_001",
                type=RequirementType.PRIMARY_FUNCTIONAL,
                description="General part requirement",
                priority=1.0,
                constraints={"description": original_text},
                source_text=original_text,
                confidence=0.5
            )
            components.append(fallback_component)
        
        return components
    
    async def _generate_direct_match_hypothesis(self, line_item: Dict[str, Any], 
                                              components: List[RequirementComponent]) -> ProcurementHypothesis:
        """Generate direct match hypothesis"""
        
        return ProcurementHypothesis(
            hypothesis_id="hyp_direct_001",
            type=HypothesisType.DIRECT_MATCH,
            description="Search for exact specification match",
            target_requirements=[comp.component_id for comp in components],
            search_strategy="semantic_vector_search",
            parameters={"top_k": 10, "min_similarity": 0.8},
            expected_confidence=0.9,
            risk_factors=["exact_match_may_not_exist"],
            advantages=["highest_confidence", "fastest_procurement"],
            disadvantages=["limited_flexibility", "may_miss_alternatives"]
        )
    
    async def _generate_substitution_hypothesis(self, line_item: Dict[str, Any], 
                                              components: List[RequirementComponent]) -> Optional[ProcurementHypothesis]:
        """Generate material substitution hypothesis"""
        
        # Check if any components have material alternatives
        has_alternatives = any(comp.alternatives for comp in components 
                             if comp.type == RequirementType.PRIMARY_FUNCTIONAL)
        
        if not has_alternatives:
            return None
        
        return ProcurementHypothesis(
            hypothesis_id="hyp_substitute_001",
            type=HypothesisType.SUBSTITUTE_MATERIAL,
            description="Search using alternative materials",
            target_requirements=[comp.component_id for comp in components 
                               if comp.type == RequirementType.PRIMARY_FUNCTIONAL],
            search_strategy="alternative_materials_search",
            parameters={"include_alternatives": True},
            expected_confidence=0.7,
            risk_factors=["performance_differences", "approval_requirements"],
            advantages=["better_availability", "potential_cost_savings"],
            disadvantages=["requires_validation", "performance_uncertainty"]
        )
    
    async def _generate_equivalent_part_hypothesis(self, line_item: Dict[str, Any], 
                                                 components: List[RequirementComponent]) -> Optional[ProcurementHypothesis]:
        """Generate equivalent part hypothesis"""
        
        return ProcurementHypothesis(
            hypothesis_id="hyp_equivalent_001",
            type=HypothesisType.EQUIVALENT_PART,
            description="Search for functionally equivalent parts",
            target_requirements=[comp.component_id for comp in components],
            search_strategy="fuzzy_text_search",
            parameters={"fuzzy_threshold": 70, "include_similar": True},
            expected_confidence=0.6,
            risk_factors=["functional_differences", "interface_compatibility"],
            advantages=["increased_options", "potential_improvements"],
            disadvantages=["requires_engineering_review", "longer_validation"]
        )
    
    async def _generate_multi_part_hypothesis(self, line_item: Dict[str, Any], 
                                            components: List[RequirementComponent]) -> Optional[ProcurementHypothesis]:
        """Generate multi-part solution hypothesis"""
        
        if len(components) < 3:  # Only for complex requirements
            return None
        
        return ProcurementHypothesis(
            hypothesis_id="hyp_multipart_001",
            type=HypothesisType.MULTI_PART_SOLUTION,
            description="Break into multiple procurable components",
            target_requirements=[comp.component_id for comp in components],
            search_strategy="component_search",
            parameters={"decompose": True, "assembly_required": True},
            expected_confidence=0.5,
            risk_factors=["assembly_complexity", "increased_cost", "coordination"],
            advantages=["higher_availability", "proven_components"],
            disadvantages=["assembly_required", "multiple_suppliers", "quality_control"]
        )
    
    async def _generate_custom_fabrication_hypothesis(self, line_item: Dict[str, Any], 
                                                    components: List[RequirementComponent]) -> ProcurementHypothesis:
        """Generate custom fabrication hypothesis"""
        
        return ProcurementHypothesis(
            hypothesis_id="hyp_custom_001",
            type=HypothesisType.CUSTOM_FABRICATION,
            description="Custom manufacturing solution",
            target_requirements=[comp.component_id for comp in components],
            search_strategy="supplier_search",
            parameters={"custom_manufacturing": True, "quote_required": True},
            expected_confidence=0.8,
            risk_factors=["long_lead_time", "high_cost", "minimum_quantities"],
            advantages=["exact_specifications", "guaranteed_availability"],
            disadvantages=["expensive", "long_lead_time", "tooling_costs"]
        )
    
    async def _rank_hypotheses(self, hypotheses: List[ProcurementHypothesis], 
                             problem: Dict[str, Any]) -> List[ProcurementHypothesis]:
        """Rank hypotheses by expected success probability"""
        
        # Simple ranking based on expected confidence and risk factors
        def rank_score(hypothesis):
            base_score = hypothesis.expected_confidence
            
            # Adjust for urgency
            complexity = problem.get("complexity", {})
            if complexity.get("urgency_level") == "critical":
                # Favor faster solutions
                if hypothesis.type == HypothesisType.DIRECT_MATCH:
                    base_score += 0.2
                elif hypothesis.type == HypothesisType.CUSTOM_FABRICATION:
                    base_score -= 0.3
            
            # Adjust for risk factors
            risk_penalty = len(hypothesis.risk_factors) * 0.05
            return base_score - risk_penalty
        
        return sorted(hypotheses, key=rank_score, reverse=True)
    
    async def _validate_completeness(self, reasoning_chain: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate completeness of reasoning chain"""
        
        required_stages = {"requirement_analysis", "hypothesis_generation", "evidence_gathering"}
        present_stages = {step.get("stage", "") for step in reasoning_chain}
        
        missing_stages = required_stages - present_stages
        completeness_score = 1.0 - (len(missing_stages) / len(required_stages))
        
        return {
            "score": completeness_score,
            "gaps": list(missing_stages),
            "present_stages": list(present_stages)
        }
    
    async def _validate_consistency(self, reasoning_chain: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate internal consistency of reasoning"""
        
        # Simple consistency check - in full implementation would be more sophisticated
        consistency_score = 0.8  # Placeholder
        
        return {
            "score": consistency_score,
            "issues": []
        }
    
    async def _validate_feasibility(self, reasoning_chain: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate practical feasibility of reasoning"""
        
        # Simple feasibility check - in full implementation would be more sophisticated
        feasibility_score = 0.7  # Placeholder
        
        return {
            "score": feasibility_score,
            "constraints": []
        }
    
    async def _generate_validation_recommendations(self, validation_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation results"""
        
        recommendations = []
        
        if validation_results["completeness_score"] < 0.7:
            recommendations.append("Consider additional requirement analysis")
        
        if validation_results["overall_quality"] == "low":
            recommendations.append("Manual expert review recommended")
        
        if len(validation_results["gaps_identified"]) > 2:
            recommendations.append("Significant gaps identified - consider re-analysis")
        
        return recommendations


# Phase 2: Sales Order Intelligence Enhancement
# Additional classes and functionality specifically for sales order reasoning

class OrderComplexity(str, Enum):
    """Sales order complexity levels (extends existing reasoning framework)"""
    SIMPLE = "simple"              # Single item, standard specs
    MODERATE = "moderate"          # Multiple items, some alternatives possible
    COMPLEX = "complex"            # Multiple items, tight specs, timing constraints
    CRITICAL = "critical"          # Emergency orders, production impact


class FulfillmentStrategy(str, Enum):
    """Order fulfillment strategy types"""
    EXACT_MATCH = "exact_match"                    # Perfect inventory match
    ALTERNATIVE_PRODUCTS = "alternative_products"  # Compatible substitutes
    SPLIT_SHIPMENT = "split_shipment"             # Partial now, remainder later
    CUSTOM_SOLUTION = "custom_solution"           # Creative fulfillment approach
    EXPEDITED_RESTOCK = "expedited_restock"       # Fast reorder for customer


class CustomerFlexibility(str, Enum):
    """Customer flexibility levels for alternatives"""
    VERY_LOW = "very_low"      # Aerospace, medical - exact specs only
    LOW = "low"                # Automotive - limited alternatives
    MEDIUM = "medium"          # General manufacturing - some flexibility
    HIGH = "high"              # Research, prototyping - alternatives welcomed


@dataclass
class SalesOrderRequirement:
    """Sales order specific requirement (extends RequirementComponent)"""
    description: str
    material_specs: Dict[str, Any] = field(default_factory=dict)
    dimensions: Dict[str, Any] = field(default_factory=dict)
    quantity: int = 1
    tolerance_requirements: List[str] = field(default_factory=list)
    certifications_needed: List[str] = field(default_factory=list)
    application_context: Optional[str] = None
    urgency_level: str = "standard"
    flexibility_indicators: List[str] = field(default_factory=list)
    customer_industry: str = "general_manufacturing"
    delivery_timeline: Optional[datetime] = None


@dataclass
class CustomerContext:
    """Customer-specific context for order reasoning"""
    customer_name: str
    industry_sector: str = "general_manufacturing"
    customer_tier: str = "standard"  # standard, preferred, key_account
    typical_flexibility: CustomerFlexibility = CustomerFlexibility.MEDIUM
    previous_alternative_acceptance: float = 0.5  # 0-1 scale
    production_sensitivity: str = "medium"  # low, medium, high, critical
    quality_requirements: str = "standard"  # standard, high, aerospace, medical
    cost_sensitivity: str = "medium"  # low, medium, high
    relationship_history: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FulfillmentOption:
    """Individual fulfillment option for order requirements"""
    strategy_type: FulfillmentStrategy
    description: str
    products_offered: List[Dict[str, Any]]
    availability_status: str  # in_stock, partial_stock, out_of_stock, expedited
    delivery_timeline: str
    confidence_score: float
    customer_fit_score: float  # How well this fits customer needs
    business_value_score: float  # Revenue/margin impact
    risk_factors: List[str] = field(default_factory=list)
    advantages: List[str] = field(default_factory=list)
    trade_offs: List[str] = field(default_factory=list)
    recommendation_reasoning: str = ""


@dataclass
class SalesOrderAnalysis:
    """Complete analysis of a sales order request"""
    order_id: str
    raw_request: str
    customer_context: CustomerContext
    product_requirements: List[SalesOrderRequirement]
    complexity_assessment: OrderComplexity
    business_impact: str = "standard"  # standard, high, critical
    flexibility_score: float = 0.5  # 0-1 scale
    reasoning_notes: List[str] = field(default_factory=list)
    confidence_score: float = 0.8
    emergency_indicators: List[str] = field(default_factory=list)


class SalesOrderReasoningFramework:
    """
    Sales Order Intelligence Framework (extends ReasoningChainServer)
    Specialized for sales order fulfillment reasoning
    """
    
    def __init__(self, base_reasoning_server: Optional[ReasoningChainServer] = None):
        self.logger = structlog.get_logger()
        self.base_reasoning = base_reasoning_server or ReasoningChainServer()
        self.industry_patterns = self._initialize_sales_industry_patterns()
        self.customer_profiles = {}
        
    def _initialize_sales_industry_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize sales-focused industry patterns"""
        return {
            "automotive": {
                "flexibility": CustomerFlexibility.LOW,
                "critical_specs": ["material_grade", "dimensions", "tolerances"],
                "acceptable_alternatives": ["same_grade_different_supplier", "equivalent_grade"],
                "timeline_sensitivity": "high",
                "quality_requirements": "high",
                "typical_order_characteristics": ["high_volume", "repeat_orders", "production_critical"],
                "emergency_indicators": ["production", "line", "downtime", "critical"]
            },
            "aerospace": {
                "flexibility": CustomerFlexibility.VERY_LOW,
                "critical_specs": ["material_grade", "certifications", "traceability", "dimensions"],
                "acceptable_alternatives": ["certified_equivalent_only"],
                "timeline_sensitivity": "variable",
                "quality_requirements": "aerospace",
                "typical_order_characteristics": ["exact_specifications", "certification_required", "traceability_critical"],
                "emergency_indicators": ["flight", "aog", "aircraft on ground", "grounded"]
            },
            "general_manufacturing": {
                "flexibility": CustomerFlexibility.MEDIUM,
                "critical_specs": ["basic_material", "approximate_dimensions"],
                "acceptable_alternatives": ["compatible_materials", "similar_dimensions", "different_suppliers"],
                "timeline_sensitivity": "medium",
                "quality_requirements": "standard",
                "typical_order_characteristics": ["cost_sensitive", "flexible_specifications"],
                "emergency_indicators": ["urgent", "rush", "immediate"]
            },
            "research_development": {
                "flexibility": CustomerFlexibility.HIGH,
                "critical_specs": ["basic_material_properties"],
                "acceptable_alternatives": ["similar_properties", "experimental_grades", "prototype_suitable"],
                "timeline_sensitivity": "low",
                "quality_requirements": "standard",
                "typical_order_characteristics": ["small_quantities", "experimental", "cost_sensitive"],
                "emergency_indicators": ["deadline", "presentation", "demo"]
            },
            "medical_device": {
                "flexibility": CustomerFlexibility.VERY_LOW,
                "critical_specs": ["biocompatibility", "medical_grade", "certifications", "traceability"],
                "acceptable_alternatives": ["certified_medical_equivalent_only"],
                "timeline_sensitivity": "medium",
                "quality_requirements": "medical",
                "typical_order_characteristics": ["exact_specifications", "FDA_compliance", "biocompatible_only"],
                "emergency_indicators": ["patient", "surgery", "clinical", "medical", "fda deadline", "submission deadline", "regulatory deadline"]
            }
        }
    
    async def analyze_sales_order(self, order_request: str, customer_name: str = "Unknown Customer") -> SalesOrderAnalysis:
        """
        Main entry point: Analyze sales order for intelligent fulfillment
        Integrates with existing reasoning framework
        """
        self.logger.info("🧠 Analyzing sales order for intelligent fulfillment", 
                        customer=customer_name, request_length=len(order_request))
        
        # Step 1: Extract customer context
        customer_context = await self._analyze_customer_context(customer_name, order_request)
        
        # Step 2: Use base reasoning framework for requirement decomposition
        requirement_components = await self.base_reasoning.decompose_complex_requirement(order_request)
        
        # Step 3: Convert to sales order requirements
        sales_requirements = await self._convert_to_sales_requirements(
            requirement_components, customer_context, order_request
        )
        
        # Step 4: Assess sales order complexity
        complexity = await self._assess_sales_order_complexity(
            sales_requirements, customer_context, order_request
        )
        
        # Step 5: Calculate customer flexibility
        flexibility_score = await self._calculate_customer_flexibility(
            customer_context, sales_requirements, order_request
        )
        
        # Step 6: Detect emergency indicators
        emergency_indicators = await self._detect_emergency_indicators(
            order_request, customer_context
        )
        
        # Step 7: Generate reasoning notes
        reasoning_notes = await self._generate_sales_reasoning_notes(
            sales_requirements, customer_context, complexity, emergency_indicators
        )
        
        analysis = SalesOrderAnalysis(
            order_id=f"SO-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            raw_request=order_request,
            customer_context=customer_context,
            product_requirements=sales_requirements,
            complexity_assessment=complexity,
            flexibility_score=flexibility_score,
            reasoning_notes=reasoning_notes,
            emergency_indicators=emergency_indicators,
            confidence_score=0.85
        )
        
        self.logger.info("✅ Sales order analysis completed",
                        order_id=analysis.order_id,
                        complexity=complexity.value,
                        customer_industry=customer_context.industry_sector,
                        flexibility_score=f"{flexibility_score:.2f}",
                        emergency_detected=len(emergency_indicators) > 0)
        
        return analysis
    
    async def generate_fulfillment_strategies(self, analysis: SalesOrderAnalysis) -> List[FulfillmentOption]:
        """
        Generate multiple fulfillment strategies based on order analysis
        Uses reasoning framework to create intelligent options
        """
        self.logger.info("🎯 Generating fulfillment strategies", 
                        order_id=analysis.order_id,
                        complexity=analysis.complexity_assessment.value)
        
        strategies = []
        
        # Strategy 1: Exact Match (if customer flexibility allows)
        if analysis.flexibility_score >= 0.3:  # Even low flexibility customers need exact matches
            exact_match = await self._generate_exact_match_strategy(analysis)
            strategies.append(exact_match)
        
        # Strategy 2: Alternative Products (if customer has flexibility)
        if analysis.flexibility_score >= 0.5:
            alternatives = await self._generate_alternative_products_strategy(analysis)
            if alternatives:
                strategies.append(alternatives)
        
        # Strategy 3: Split Shipment (for large orders or partial availability)
        if self._should_consider_split_shipment(analysis):
            split_shipment = await self._generate_split_shipment_strategy(analysis)
            strategies.append(split_shipment)
        
        # Strategy 4: Expedited Restock (for key customers or critical items)
        if analysis.customer_context.customer_tier in ["preferred", "key_account"] or analysis.emergency_indicators:
            expedited = await self._generate_expedited_restock_strategy(analysis)
            strategies.append(expedited)
        
        # Strategy 5: Custom Solution (for complex requirements)
        if analysis.complexity_assessment in [OrderComplexity.COMPLEX, OrderComplexity.CRITICAL]:
            custom = await self._generate_custom_solution_strategy(analysis)
            strategies.append(custom)
        
        # Rank strategies by customer fit and business value
        ranked_strategies = await self._rank_fulfillment_strategies(strategies, analysis)
        
        self.logger.info("✅ Fulfillment strategies generated",
                        strategies_count=len(ranked_strategies),
                        top_strategy=ranked_strategies[0].strategy_type.value if ranked_strategies else "none")
        
        return ranked_strategies
    
    async def _analyze_customer_context(self, customer_name: str, order_request: str) -> CustomerContext:
        """Analyze customer context for sales order intelligence"""
        
        # Industry detection based on customer name and order content
        industry = "general_manufacturing"
        for industry_key, patterns in self.industry_patterns.items():
            industry_keywords = patterns.get("typical_order_characteristics", [])
            
            # Check customer name
            if any(keyword in customer_name.lower() for keyword in 
                  ["ford", "gm", "toyota", "automotive", "motor"] if industry_key == "automotive"):
                industry = "automotive"
                break
            elif any(keyword in customer_name.lower() for keyword in 
                    ["boeing", "airbus", "aerospace", "aircraft"] if industry_key == "aerospace"):
                industry = "aerospace"
                break
            elif any(keyword in customer_name.lower() for keyword in 
                    ["university", "research", "lab", "mit"] if industry_key == "research_development"):
                industry = "research_development"
                break
            elif any(keyword in customer_name.lower() for keyword in 
                    ["medical", "hospital", "surgical", "medtronic", "biomed", "implant"] if industry_key == "medical_device"):
                industry = "medical_device"
                break
        
        # Customer tier assessment
        tier = "standard"
        key_account_indicators = ["ford", "boeing", "general motors", "airbus", "spacex", "tesla"]
        preferred_indicators = ["corporation", "corp", "inc", "ltd", "manufacturing", "systems"]
        small_business_indicators = ["joe's", "bob's", "family", "small", "shop", "home", "garage"]
        
        if any(indicator in customer_name.lower() for indicator in key_account_indicators):
            tier = "key_account"
        elif any(indicator in customer_name.lower() for indicator in preferred_indicators):
            tier = "preferred"
        elif any(indicator in customer_name.lower() for indicator in small_business_indicators):
            tier = "small_business"
        
        # Get industry-specific patterns
        industry_pattern = self.industry_patterns.get(industry, self.industry_patterns["general_manufacturing"])
        
        return CustomerContext(
            customer_name=customer_name,
            industry_sector=industry,
            customer_tier=tier,
            typical_flexibility=industry_pattern["flexibility"],
            quality_requirements=industry_pattern["quality_requirements"],
            production_sensitivity="high" if any(keyword in order_request.lower() 
                                               for keyword in ["production", "line", "critical"]) else "medium"
        )
    
    async def _convert_to_sales_requirements(self, requirement_components: List[RequirementComponent], 
                                           customer_context: CustomerContext, 
                                           order_request: str) -> List[SalesOrderRequirement]:
        """Convert generic requirements to sales order specific requirements"""
        
        sales_requirements = []
        
        for comp in requirement_components:
            # Determine urgency from original request
            urgency = "critical" if any(indicator in order_request.lower() 
                                     for indicator in ["emergency", "urgent", "asap", "critical"]) else "standard"
            
            # Extract quantity if possible
            quantity = 1
            quantity_match = re.search(r'(\d+)\s*(?:pieces?|pcs?|each)', order_request, re.IGNORECASE)
            if quantity_match:
                quantity = int(quantity_match.group(1))
            
            # Extract delivery timeline
            delivery_timeline = None
            timeline_patterns = [
                r'(?:need|require).*?(?:by|within)\s*(\d+)\s*(days?|hours?|weeks?)',
                r'(\d+)\s*(days?|hours?|weeks?).*?delivery'
            ]
            
            for pattern in timeline_patterns:
                match = re.search(pattern, order_request, re.IGNORECASE)
                if match:
                    number = int(match.group(1))
                    unit = match.group(2).lower()
                    
                    if "hour" in unit:
                        delivery_timeline = datetime.now() + timedelta(hours=number)
                    elif "day" in unit:
                        delivery_timeline = datetime.now() + timedelta(days=number)
                    elif "week" in unit:
                        delivery_timeline = datetime.now() + timedelta(weeks=number)
                    break
            
            sales_req = SalesOrderRequirement(
                description=comp.description,
                material_specs=comp.constraints,
                quantity=quantity,
                urgency_level=urgency,
                customer_industry=customer_context.industry_sector,
                delivery_timeline=delivery_timeline
            )
            
            sales_requirements.append(sales_req)
        
        return sales_requirements
    
    async def _assess_sales_order_complexity(self, requirements: List[SalesOrderRequirement], 
                                           customer_context: CustomerContext, 
                                           order_request: str) -> OrderComplexity:
        """Assess complexity specific to sales order fulfillment"""
        
        complexity_score = 0
        
        # Base complexity factors (be more lenient for simple customer types)
        if customer_context.industry_sector == "research_development":
            requirement_threshold = 8  # Research often has multiple samples
        elif customer_context.customer_tier == "small_business":
            requirement_threshold = 10  # Small businesses have simple orders despite over-decomposition
        elif customer_context.industry_sector == "general_manufacturing" and customer_context.customer_tier == "standard":
            requirement_threshold = 6  # Small shops tend to have simple orders
        else:
            requirement_threshold = 5
            
        if len(requirements) > requirement_threshold:
            complexity_score += 1
        
        # Customer industry complexity
        if customer_context.industry_sector in ["aerospace", "medical_device"]:
            complexity_score += 2
        elif customer_context.industry_sector == "automotive":
            complexity_score += 1
        
        # Urgency complexity
        if any(req.urgency_level == "critical" for req in requirements):
            complexity_score += 2
        
        # Timeline complexity
        if any(req.delivery_timeline and req.delivery_timeline < datetime.now() + timedelta(days=1) 
               for req in requirements):
            complexity_score += 1
        
        # Emergency indicators
        emergency_keywords = ["emergency", "production down", "critical", "asap", "urgent"]
        critical_emergency_keywords = ["production down", "line down", "plant shutdown", "production critical", "fda deadline", "submission deadline"]
        
        if any(keyword in order_request.lower() for keyword in critical_emergency_keywords):
            complexity_score += 2  # Critical production emergencies get higher score
        elif any(keyword in order_request.lower() for keyword in emergency_keywords):
            complexity_score += 1
        
        # Map to complexity levels
        if complexity_score >= 5:
            return OrderComplexity.CRITICAL
        elif complexity_score >= 3:
            return OrderComplexity.COMPLEX
        elif complexity_score >= 1:
            return OrderComplexity.MODERATE
        else:
            return OrderComplexity.SIMPLE
    
    async def _calculate_customer_flexibility(self, customer_context: CustomerContext, 
                                            requirements: List[SalesOrderRequirement],
                                            order_request: str) -> float:
        """Calculate customer flexibility for alternative products"""
        
        # Start with industry-based flexibility
        flexibility_map = {
            CustomerFlexibility.VERY_LOW: 0.1,
            CustomerFlexibility.LOW: 0.3,
            CustomerFlexibility.MEDIUM: 0.5,
            CustomerFlexibility.HIGH: 0.8
        }
        
        flexibility_score = flexibility_map[customer_context.typical_flexibility]
        
        # Emergency increases flexibility
        if any(keyword in order_request.lower() for keyword in ["emergency", "critical", "production down"]):
            flexibility_score = min(1.0, flexibility_score + 0.3)
        
        # R&D customers are more flexible
        if customer_context.industry_sector == "research_development":
            flexibility_score = min(1.0, flexibility_score + 0.2)
        
        # Key accounts may be more flexible due to relationship
        if customer_context.customer_tier == "key_account":
            flexibility_score = min(1.0, flexibility_score + 0.1)
        
        return flexibility_score
    
    async def _detect_emergency_indicators(self, order_request: str, customer_context: CustomerContext) -> List[str]:
        """Detect emergency indicators in sales order"""
        
        indicators = []
        
        # Get industry-specific emergency keywords
        industry_pattern = self.industry_patterns.get(
            customer_context.industry_sector, 
            self.industry_patterns["general_manufacturing"]
        )
        
        emergency_keywords = industry_pattern.get("emergency_indicators", [])
        emergency_keywords.extend(["emergency", "urgent", "asap", "critical", "immediate", "rush"])
        
        # Check for emergency keywords
        order_lower = order_request.lower()
        for keyword in emergency_keywords:
            if keyword in order_lower:
                indicators.append(keyword)
        
        # Check for timeline indicators
        timeline_urgency = ["within.*hours?", "same day", "today", "immediately", "now"]
        for pattern in timeline_urgency:
            if re.search(pattern, order_lower):
                indicators.append("urgent_timeline")
                break
        
        # Check for production impact
        production_impact = ["production.*down", "line.*down", "shutdown", "stopped", "halted"]
        for pattern in production_impact:
            if re.search(pattern, order_lower):
                indicators.append("production_impact")
                break
        
        return list(set(indicators))  # Remove duplicates
    
    async def _generate_sales_reasoning_notes(self, requirements: List[SalesOrderRequirement],
                                            customer_context: CustomerContext,
                                            complexity: OrderComplexity,
                                            emergency_indicators: List[str]) -> List[str]:
        """Generate sales-focused reasoning notes"""
        
        notes = []
        
        # Customer analysis
        notes.append(f"Customer: {customer_context.customer_name} ({customer_context.industry_sector})")
        notes.append(f"Customer tier: {customer_context.customer_tier} - Flexibility: {customer_context.typical_flexibility.value}")
        
        # Order characteristics
        notes.append(f"Products requested: {len(requirements)}")
        notes.append(f"Order complexity: {complexity.value}")
        
        # Emergency handling
        if emergency_indicators:
            notes.append(f"Emergency indicators detected: {', '.join(emergency_indicators)}")
            notes.append("Emergency processing protocols activated")
        
        # Industry-specific notes
        if customer_context.industry_sector == "automotive":
            notes.append("Automotive customer - production sensitivity high, alternatives limited")
        elif customer_context.industry_sector == "aerospace":
            notes.append("Aerospace customer - exact specifications required, certifications critical")
        elif customer_context.industry_sector == "research_development":
            notes.append("R&D customer - alternatives acceptable, cost optimization important")
        
        # Fulfillment strategy hints
        if complexity in [OrderComplexity.COMPLEX, OrderComplexity.CRITICAL]:
            notes.append("Complex order - multiple fulfillment strategies recommended")
        
        if customer_context.customer_tier == "key_account":
            notes.append("Key account - prioritize customer satisfaction and service level")
        
        return notes
    
    # Fulfillment strategy generation methods
    
    async def _generate_exact_match_strategy(self, analysis: SalesOrderAnalysis) -> FulfillmentOption:
        """Generate exact match fulfillment strategy"""
        
        return FulfillmentOption(
            strategy_type=FulfillmentStrategy.EXACT_MATCH,
            description="Find exact specification matches in current inventory",
            products_offered=[],  # Will be populated during execution
            availability_status="to_be_determined",
            delivery_timeline="Standard delivery" if not analysis.emergency_indicators else "Expedited delivery",
            confidence_score=0.9,
            customer_fit_score=1.0,  # Perfect fit for customer needs
            business_value_score=0.8,  # Good margin, standard processing
            advantages=["Exact specifications", "Fastest fulfillment", "No alternatives needed"],
            trade_offs=["May not be available", "Limited options"],
            recommendation_reasoning="Exact match provides highest customer satisfaction and fastest delivery"
        )
    
    async def _generate_alternative_products_strategy(self, analysis: SalesOrderAnalysis) -> Optional[FulfillmentOption]:
        """Generate alternative products strategy"""
        
        if analysis.flexibility_score < 0.4:
            return None  # Customer too inflexible for alternatives
        
        confidence = 0.7 if analysis.flexibility_score > 0.6 else 0.5
        
        return FulfillmentOption(
            strategy_type=FulfillmentStrategy.ALTERNATIVE_PRODUCTS,
            description="Offer compatible alternative products from available inventory",
            products_offered=[],
            availability_status="alternatives_available",
            delivery_timeline="Standard delivery",
            confidence_score=confidence,
            customer_fit_score=analysis.flexibility_score,
            business_value_score=0.9,  # Potentially better margins
            advantages=["Better availability", "Potential cost savings", "Proven alternatives"],
            trade_offs=["Requires customer approval", "May need specification validation"],
            recommendation_reasoning=f"Customer flexibility ({analysis.flexibility_score:.1f}) allows alternatives"
        )
    
    async def _generate_split_shipment_strategy(self, analysis: SalesOrderAnalysis) -> FulfillmentOption:
        """Generate split shipment strategy"""
        
        return FulfillmentOption(
            strategy_type=FulfillmentStrategy.SPLIT_SHIPMENT,
            description="Partial shipment from current stock + remainder when available",
            products_offered=[],
            availability_status="partial_availability",
            delivery_timeline="Immediate partial + scheduled completion",
            confidence_score=0.8,
            customer_fit_score=0.7,  # Acceptable for most customers
            business_value_score=0.7,  # Additional handling costs
            advantages=["Immediate partial fulfillment", "Reduces customer wait time", "Maintains order"],
            trade_offs=["Multiple shipments", "Additional logistics", "Partial satisfaction"],
            recommendation_reasoning="Split shipment reduces customer impact when full order unavailable"
        )
    
    async def _generate_expedited_restock_strategy(self, analysis: SalesOrderAnalysis) -> FulfillmentOption:
        """Generate expedited restock strategy"""
        
        return FulfillmentOption(
            strategy_type=FulfillmentStrategy.EXPEDITED_RESTOCK,
            description="Expedited reorder from suppliers for customer delivery",
            products_offered=[],
            availability_status="expedited_restock",
            delivery_timeline="Expedited (premium timeline)",
            confidence_score=0.6,
            customer_fit_score=0.8,  # Good for emergency situations
            business_value_score=0.6,  # Lower margins due to expediting costs
            advantages=["Guaranteed availability", "Maintains customer relationship", "Exact specifications"],
            trade_offs=["Higher costs", "Longer timeline", "Supplier dependency"],
            recommendation_reasoning="Expedited restock for key customers or emergency situations"
        )
    
    async def _generate_custom_solution_strategy(self, analysis: SalesOrderAnalysis) -> FulfillmentOption:
        """Generate custom solution strategy"""
        
        return FulfillmentOption(
            strategy_type=FulfillmentStrategy.CUSTOM_SOLUTION,
            description="Creative fulfillment approach combining multiple options",
            products_offered=[],
            availability_status="custom_approach",
            delivery_timeline="Variable based on solution",
            confidence_score=0.7,
            customer_fit_score=0.9,  # Tailored to customer needs
            business_value_score=0.8,  # Premium for custom service
            advantages=["Tailored solution", "High customer satisfaction", "Premium service"],
            trade_offs=["Complex coordination", "Higher effort", "Variable timeline"],
            recommendation_reasoning="Custom solution for complex requirements or key accounts"
        )
    
    def _should_consider_split_shipment(self, analysis: SalesOrderAnalysis) -> bool:
        """Determine if split shipment should be considered"""
        
        # Consider split shipment for:
        # 1. Multiple products (higher chance of partial availability)
        # 2. Large quantities
        # 3. Non-critical industries (automotive/aerospace prefer complete orders)
        # 4. Emergency situations where partial is better than nothing
        
        if len(analysis.product_requirements) > 1:
            return True
        
        if any(req.quantity > 10 for req in analysis.product_requirements):
            return True
        
        if analysis.emergency_indicators and analysis.customer_context.industry_sector not in ["aerospace"]:
            return True
        
        if analysis.customer_context.industry_sector in ["research_development", "general_manufacturing"]:
            return True
        
        return False
    
    async def _rank_fulfillment_strategies(self, strategies: List[FulfillmentOption], 
                                         analysis: SalesOrderAnalysis) -> List[FulfillmentOption]:
        """Rank fulfillment strategies by overall value"""
        
        def strategy_score(strategy: FulfillmentOption) -> float:
            # Weighted scoring based on customer fit, confidence, and business value
            score = (
                strategy.customer_fit_score * 0.4 +
                strategy.confidence_score * 0.3 +
                strategy.business_value_score * 0.3
            )
            
            # Boost for emergency situations
            if analysis.emergency_indicators:
                if strategy.strategy_type in [FulfillmentStrategy.EXACT_MATCH, FulfillmentStrategy.EXPEDITED_RESTOCK]:
                    score += 0.2
            
            # Boost for key accounts
            if analysis.customer_context.customer_tier == "key_account":
                if strategy.strategy_type in [FulfillmentStrategy.CUSTOM_SOLUTION, FulfillmentStrategy.EXPEDITED_RESTOCK]:
                    score += 0.1
            
            return score
        
        return sorted(strategies, key=strategy_score, reverse=True)


# MCP Tool Functions for Sales Order Intelligence

async def analyze_sales_order_intelligence(order_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    MCP Tool: Analyze sales order with multi-step reasoning
    Integrates with existing contextual intelligence
    """
    framework = SalesOrderReasoningFramework()
    
    order_request = order_data.get('raw_text', '')
    customer_name = order_data.get('customer', {}).get('name', 'Unknown Customer')
    
    analysis = await framework.analyze_sales_order(order_request, customer_name)
    
    return {
        'sales_order_analysis': {
            'order_id': analysis.order_id,
            'complexity': analysis.complexity_assessment.value,
            'customer_industry': analysis.customer_context.industry_sector,
            'customer_tier': analysis.customer_context.customer_tier,
            'flexibility_score': analysis.flexibility_score,
            'emergency_detected': len(analysis.emergency_indicators) > 0,
            'emergency_indicators': analysis.emergency_indicators,
            'product_count': len(analysis.product_requirements),
            'reasoning_notes': analysis.reasoning_notes,
            'confidence_score': analysis.confidence_score
        },
        'fulfillment_ready': True,
        'reasoning_framework_active': True
    }


async def generate_fulfillment_strategies(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    MCP Tool: Generate intelligent fulfillment strategies
    """
    framework = SalesOrderReasoningFramework()
    
    # Extract analysis data
    order_request = analysis_data.get('order_request', '')
    customer_name = analysis_data.get('customer_name', 'Unknown Customer')
    
    # Generate full analysis
    analysis = await framework.analyze_sales_order(order_request, customer_name)
    
    # Generate fulfillment strategies
    strategies = await framework.generate_fulfillment_strategies(analysis)
    
    return {
        'fulfillment_strategies': {
            'strategy_count': len(strategies),
            'recommended_strategy': strategies[0].strategy_type.value if strategies else 'none',
            'strategies': [{
                'type': strategy.strategy_type.value,
                'description': strategy.description,
                'confidence_score': strategy.confidence_score,
                'customer_fit_score': strategy.customer_fit_score,
                'business_value_score': strategy.business_value_score,
                'advantages': strategy.advantages,
                'trade_offs': strategy.trade_offs,
                'recommendation_reasoning': strategy.recommendation_reasoning
            } for strategy in strategies],
            'reasoning_applied': True,
            'analysis_context': {
                'complexity': analysis.complexity_assessment.value,
                'customer_industry': analysis.customer_context.industry_sector,
                'flexibility_score': analysis.flexibility_score,
                'emergency_detected': len(analysis.emergency_indicators) > 0
            }
        }
    }
"""
Enhanced MCP Cross-Domain Knowledge Integration
Provides industry standards, regulatory compliance, and material science expertise
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import structlog
from datetime import datetime

logger = structlog.get_logger()

class IndustryStandard(Enum):
    """Major industry standards"""
    ASTM = "astm"
    ISO = "iso"
    ASME = "asme"
    API = "api"
    DIN = "din"
    JIS = "jis"
    BS = "bs"
    ANSI = "ansi"
    SAE = "sae"
    NIST = "nist"

class RegulatoryDomain(Enum):
    """Regulatory compliance domains"""
    FDA = "fda"                    # Food and Drug Administration
    OSHA = "osha"                  # Occupational Safety and Health
    EPA = "epa"                    # Environmental Protection Agency
    DOT = "dot"                    # Department of Transportation
    ITAR = "itar"                  # International Traffic in Arms
    EAR = "ear"                    # Export Administration Regulations
    CE_MARKING = "ce_marking"      # European Conformity
    RoHS = "rohs"                  # Restriction of Hazardous Substances
    REACH = "reach"                # Registration, Evaluation, Authorization

class MaterialProperty(Enum):
    """Material properties for engineering analysis"""
    TENSILE_STRENGTH = "tensile_strength"
    YIELD_STRENGTH = "yield_strength"
    HARDNESS = "hardness"
    CORROSION_RESISTANCE = "corrosion_resistance"
    THERMAL_CONDUCTIVITY = "thermal_conductivity"
    ELECTRICAL_CONDUCTIVITY = "electrical_conductivity"
    DENSITY = "density"
    MELTING_POINT = "melting_point"
    MAGNETIC_PROPERTIES = "magnetic_properties"
    CHEMICAL_COMPATIBILITY = "chemical_compatibility"

@dataclass
class StandardSpecification:
    """Industry standard specification"""
    standard_id: str
    organization: IndustryStandard
    title: str
    scope: str
    applicable_materials: List[str]
    key_requirements: Dict[str, Any]
    testing_methods: List[str]
    certification_required: bool
    revision_date: str

@dataclass
class RegulatoryRequirement:
    """Regulatory compliance requirement"""
    regulation_id: str
    domain: RegulatoryDomain
    title: str
    applicability: Dict[str, Any]
    requirements: List[str]
    documentation_needed: List[str]
    penalties: str
    compliance_timeline: str

@dataclass
class MaterialDatabase:
    """Material properties and characteristics"""
    material_id: str
    common_names: List[str]
    chemical_composition: Dict[str, float]
    mechanical_properties: Dict[MaterialProperty, Any]
    applications: List[str]
    limitations: List[str]
    equivalent_materials: List[str]
    processing_requirements: List[str]

class DomainKnowledgeServer:
    """
    MCP server for domain expertise integration
    Provides industry standards, regulatory compliance, and material science knowledge
    """
    
    def __init__(self):
        self.industry_standards = self._load_industry_standards()
        self.regulatory_database = self._load_regulatory_requirements()
        self.material_database = self._load_material_database()
        self.compatibility_matrix = self._load_compatibility_matrix()
        self.substitution_rules = self._load_substitution_rules()
        
    def _load_industry_standards(self) -> Dict[str, StandardSpecification]:
        """Load industry standards database"""
        return {
            "astm_a36": StandardSpecification(
                standard_id="ASTM A36",
                organization=IndustryStandard.ASTM,
                title="Standard Specification for Carbon Structural Steel",
                scope="Covers carbon structural steel for general construction",
                applicable_materials=["carbon_steel", "structural_steel"],
                key_requirements={
                    "tensile_strength": {"min": 400, "max": 550, "unit": "MPa"},
                    "yield_strength": {"min": 250, "unit": "MPa"},
                    "elongation": {"min": 20, "unit": "%"}
                },
                testing_methods=["tensile_test", "chemical_analysis"],
                certification_required=True,
                revision_date="2019"
            ),
            "astm_b221": StandardSpecification(
                standard_id="ASTM B221",
                organization=IndustryStandard.ASTM,
                title="Standard Specification for Aluminum and Aluminum-Alloy Extruded Bars, Rods, Wire, Profiles, and Tubes",
                scope="Covers aluminum alloy extruded products",
                applicable_materials=["6061", "6063", "2024", "7075"],
                key_requirements={
                    "tensile_strength": {"varies_by_alloy": True},
                    "dimensional_tolerance": {"per_specification": True}
                },
                testing_methods=["tensile_test", "hardness_test"],
                certification_required=True,
                revision_date="2020"
            ),
            "asme_b31.3": StandardSpecification(
                standard_id="ASME B31.3",
                organization=IndustryStandard.ASME,
                title="Process Piping Code",
                scope="Covers piping typically found in petroleum refineries, chemical plants",
                applicable_materials=["carbon_steel", "stainless_steel", "alloy_steel"],
                key_requirements={
                    "pressure_rating": {"calculated_per_code": True},
                    "material_traceability": {"required": True},
                    "ndt_requirements": {"per_service": True}
                },
                testing_methods=["hydrostatic_test", "ndt"],
                certification_required=True,
                revision_date="2020"
            ),
            "iso_9001": StandardSpecification(
                standard_id="ISO 9001",
                organization=IndustryStandard.ISO,
                title="Quality Management Systems - Requirements",
                scope="Specifies requirements for quality management system",
                applicable_materials=["all"],
                key_requirements={
                    "quality_management": {"systematic_approach": True},
                    "documentation": {"controlled": True},
                    "continuous_improvement": {"required": True}
                },
                testing_methods=["audit", "review"],
                certification_required=True,
                revision_date="2015"
            )
        }
    
    def _load_regulatory_requirements(self) -> Dict[str, RegulatoryRequirement]:
        """Load regulatory requirements database"""
        return {
            "fda_medical_device": RegulatoryRequirement(
                regulation_id="FDA 21 CFR 820",
                domain=RegulatoryDomain.FDA,
                title="Quality System Regulation for Medical Devices",
                applicability={
                    "industries": ["medical", "pharmaceutical"],
                    "product_types": ["medical_devices", "implants"],
                    "risk_classes": ["Class I", "Class II", "Class III"]
                },
                requirements=[
                    "Design controls required",
                    "Material biocompatibility testing",
                    "Sterilization validation",
                    "Clinical evaluation if required"
                ],
                documentation_needed=[
                    "510(k) submission or PMA",
                    "Biocompatibility test reports",
                    "Sterilization validation reports"
                ],
                penalties="Warning letters, consent decrees, injunctions",
                compliance_timeline="Before market introduction"
            ),
            "osha_hazcom": RegulatoryRequirement(
                regulation_id="OSHA 29 CFR 1910.1200",
                domain=RegulatoryDomain.OSHA,
                title="Hazard Communication Standard",
                applicability={
                    "industries": ["all_manufacturing"],
                    "materials": ["hazardous_chemicals"],
                    "workplace_exposure": True
                },
                requirements=[
                    "Safety Data Sheets (SDS) available",
                    "Hazard labeling required",
                    "Employee training mandatory"
                ],
                documentation_needed=[
                    "Safety Data Sheets",
                    "Training records",
                    "Hazard assessment"
                ],
                penalties="Fines up to $13,653 per violation",
                compliance_timeline="Immediate for new chemicals"
            ),
            "itar_export": RegulatoryRequirement(
                regulation_id="ITAR 22 CFR 120-130",
                domain=RegulatoryDomain.ITAR,
                title="International Traffic in Arms Regulations",
                applicability={
                    "industries": ["defense", "aerospace"],
                    "products": ["defense_articles", "dual_use"],
                    "export_activities": True
                },
                requirements=[
                    "Export license required",
                    "Registration with DDTC",
                    "Foreign person access restrictions"
                ],
                documentation_needed=[
                    "DSP-5 export license",
                    "DDTC registration",
                    "Technical Assistance Agreement"
                ],
                penalties="Up to $1M fine and 20 years imprisonment",
                compliance_timeline="Before any export activity"
            )
        }
    
    def _load_material_database(self) -> Dict[str, MaterialDatabase]:
        """Load comprehensive material properties database"""
        return {
            "4140": MaterialDatabase(
                material_id="4140",
                common_names=["AISI 4140", "SAE 4140", "Chromoly"],
                chemical_composition={
                    "C": 0.40, "Mn": 0.85, "P": 0.035, "S": 0.035,
                    "Si": 0.25, "Cr": 0.95, "Mo": 0.20
                },
                mechanical_properties={
                    MaterialProperty.TENSILE_STRENGTH: {"value": 655, "unit": "MPa", "condition": "normalized"},
                    MaterialProperty.YIELD_STRENGTH: {"value": 415, "unit": "MPa", "condition": "normalized"},
                    MaterialProperty.HARDNESS: {"value": 197, "unit": "HB", "condition": "normalized"}
                },
                applications=[
                    "Aircraft landing gear", "Power transmission shafts", 
                    "Automotive axles", "Oil drilling equipment"
                ],
                limitations=[
                    "Limited weldability without preheating",
                    "Susceptible to hydrogen embrittlement"
                ],
                equivalent_materials=["4340", "4130", "8620"],
                processing_requirements=[
                    "Stress relief after machining",
                    "Preheating for welding (300-400°F)"
                ]
            ),
            "6061": MaterialDatabase(
                material_id="6061",
                common_names=["6061-T6", "Al 6061"],
                chemical_composition={
                    "Al": 97.9, "Mg": 1.0, "Si": 0.6, "Cu": 0.3,
                    "Cr": 0.2, "Zn": 0.25, "Ti": 0.15, "Fe": 0.7
                },
                mechanical_properties={
                    MaterialProperty.TENSILE_STRENGTH: {"value": 310, "unit": "MPa", "condition": "T6"},
                    MaterialProperty.YIELD_STRENGTH: {"value": 276, "unit": "MPa", "condition": "T6"},
                    MaterialProperty.HARDNESS: {"value": 95, "unit": "HB", "condition": "T6"}
                },
                applications=[
                    "Structural components", "Marine applications",
                    "Automotive parts", "Consumer electronics"
                ],
                limitations=[
                    "Lower strength than 7075",
                    "Not suitable for high temperature"
                ],
                equivalent_materials=["6063", "6082", "5052"],
                processing_requirements=[
                    "Solution heat treatment for T6",
                    "Artificial aging at 160°C"
                ]
            ),
            "304": MaterialDatabase(
                material_id="304",
                common_names=["304 SS", "18-8 Stainless"],
                chemical_composition={
                    "Fe": 70.0, "Cr": 19.0, "Ni": 9.25, "Mn": 2.0,
                    "Si": 1.0, "C": 0.08, "P": 0.045, "S": 0.03
                },
                mechanical_properties={
                    MaterialProperty.TENSILE_STRENGTH: {"value": 515, "unit": "MPa", "condition": "annealed"},
                    MaterialProperty.YIELD_STRENGTH: {"value": 205, "unit": "MPa", "condition": "annealed"},
                    MaterialProperty.CORROSION_RESISTANCE: {"rating": "excellent", "environment": "general"}
                },
                applications=[
                    "Food processing equipment", "Chemical processing",
                    "Architectural applications", "Kitchen equipment"
                ],
                limitations=[
                    "Susceptible to chloride stress corrosion",
                    "Lower corrosion resistance than 316"
                ],
                equivalent_materials=["316", "316L", "321"],
                processing_requirements=[
                    "Annealing at 1050-1120°C",
                    "Rapid cooling to prevent carbide precipitation"
                ]
            )
        }
    
    def _load_compatibility_matrix(self) -> Dict[str, Dict[str, str]]:
        """Load material compatibility matrix"""
        return {
            "galvanic_compatibility": {
                ("aluminum", "steel"): "poor",
                ("aluminum", "stainless_steel"): "acceptable",
                ("steel", "stainless_steel"): "good",
                ("copper", "aluminum"): "poor",
                ("copper", "steel"): "acceptable"
            },
            "chemical_compatibility": {
                ("304", "chloride_environment"): "poor",
                ("316", "chloride_environment"): "good",
                ("carbon_steel", "acidic_environment"): "poor",
                ("titanium", "acidic_environment"): "excellent"
            }
        }
    
    def _load_substitution_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load material substitution rules and guidelines"""
        return {
            "strength_based": {
                "rule": "substitute_higher_strength_acceptable",
                "examples": {
                    "4140": ["4340", "4330"],  # Higher strength alternatives
                    "6061": ["7075", "2024"]   # Higher strength aluminum
                }
            },
            "corrosion_based": {
                "rule": "substitute_better_corrosion_resistance",
                "examples": {
                    "304": ["316", "316L"],    # Better corrosion resistance
                    "carbon_steel": ["stainless_steel"]
                }
            },
            "application_specific": {
                "marine": {
                    "avoid": ["carbon_steel", "aluminum_bronze"],
                    "prefer": ["316_stainless", "super_duplex", "titanium"]
                },
                "food_grade": {
                    "require": ["316L", "304", "approved_polymers"],
                    "avoid": ["lead_bearing", "zinc_coated"]
                }
            }
        }
    
    async def industry_standards_lookup(self, material_spec: str) -> Dict[str, Any]:
        """
        MCP Tool: Integrate industry standards (ASTM, ISO, etc.)
        
        Args:
            material_spec: Material specification or requirement
            
        Returns:
            Applicable industry standards and requirements
        """
        logger.info("🔍 Looking up industry standards", material_spec=material_spec)
        
        try:
            material_spec_lower = material_spec.lower()
            applicable_standards = []
            
            # Search for applicable standards
            for std_id, standard in self.industry_standards.items():
                # Check if material matches applicable materials
                if any(material in material_spec_lower 
                      for material in standard.applicable_materials):
                    applicable_standards.append({
                        "standard_id": standard.standard_id,
                        "organization": standard.organization.value,
                        "title": standard.title,
                        "key_requirements": standard.key_requirements,
                        "certification_required": standard.certification_required,
                        "testing_methods": standard.testing_methods
                    })
                
                # Check scope for relevance
                if any(keyword in standard.scope.lower() 
                      for keyword in material_spec_lower.split()):
                    if not any(std["standard_id"] == standard.standard_id 
                             for std in applicable_standards):
                        applicable_standards.append({
                            "standard_id": standard.standard_id,
                            "organization": standard.organization.value,
                            "title": standard.title,
                            "scope_match": True,
                            "key_requirements": standard.key_requirements
                        })
            
            # Add recommendations
            recommendations = []
            if not applicable_standards:
                recommendations.append("No specific standards found - consider generic material standards")
            else:
                recommendations.append(f"Found {len(applicable_standards)} applicable standards")
                if any(std.get("certification_required") for std in applicable_standards):
                    recommendations.append("Certification required for one or more standards")
            
            result = {
                "material_specification": material_spec,
                "applicable_standards": applicable_standards,
                "recommendations": recommendations,
                "compliance_notes": self._generate_compliance_notes(applicable_standards)
            }
            
            logger.info("✅ Standards lookup completed", 
                       standards_found=len(applicable_standards))
            
            return result
            
        except Exception as e:
            logger.error("❌ Standards lookup failed", error=str(e))
            return {
                "error": str(e),
                "material_specification": material_spec,
                "applicable_standards": [],
                "recommendations": ["Manual standards review required"]
            }
    
    async def regulatory_compliance_check(self, part_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        MCP Tool: Check regulatory requirements by industry
        
        Args:
            part_spec: Part specification including industry, application, materials
            
        Returns:
            Regulatory compliance requirements and recommendations
        """
        logger.info("🏛️ Checking regulatory compliance", 
                   industry=part_spec.get("industry"),
                   application=part_spec.get("application"))
        
        try:
            industry = part_spec.get("industry", "").lower()
            application = part_spec.get("application", "").lower()
            materials = part_spec.get("materials", [])
            
            applicable_regulations = []
            compliance_requirements = []
            
            # Check each regulation for applicability
            for reg_id, regulation in self.regulatory_database.items():
                applicability = regulation.applicability
                
                # Check industry match
                if "industries" in applicability:
                    if (industry in applicability["industries"] or 
                        "all_manufacturing" in applicability["industries"]):
                        
                        applicable_regulations.append({
                            "regulation_id": regulation.regulation_id,
                            "domain": regulation.domain.value,
                            "title": regulation.title,
                            "requirements": regulation.requirements,
                            "documentation": regulation.documentation_needed,
                            "penalties": regulation.penalties,
                            "timeline": regulation.compliance_timeline,
                            "match_reason": "industry_match"
                        })
                
                # Check application-specific requirements
                if "product_types" in applicability:
                    if any(prod_type in application 
                          for prod_type in applicability["product_types"]):
                        
                        if not any(reg["regulation_id"] == regulation.regulation_id 
                                 for reg in applicable_regulations):
                            applicable_regulations.append({
                                "regulation_id": regulation.regulation_id,
                                "domain": regulation.domain.value,
                                "title": regulation.title,
                                "requirements": regulation.requirements,
                                "match_reason": "application_match"
                            })
            
            # Generate compliance action items
            action_items = self._generate_compliance_action_items(
                applicable_regulations, part_spec
            )
            
            # Assess compliance complexity
            complexity_assessment = self._assess_compliance_complexity(
                applicable_regulations
            )
            
            result = {
                "part_specification": part_spec,
                "applicable_regulations": applicable_regulations,
                "compliance_requirements": compliance_requirements,
                "action_items": action_items,
                "complexity_assessment": complexity_assessment,
                "recommendations": self._generate_compliance_recommendations(
                    applicable_regulations, complexity_assessment
                )
            }
            
            logger.info("✅ Regulatory compliance check completed",
                       regulations_found=len(applicable_regulations),
                       complexity=complexity_assessment["level"])
            
            return result
            
        except Exception as e:
            logger.error("❌ Regulatory compliance check failed", error=str(e))
            return {
                "error": str(e),
                "part_specification": part_spec,
                "recommendations": ["Manual regulatory review required"]
            }
    
    async def material_science_reasoning(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        MCP Tool: Apply material science principles for substitutions
        
        Args:
            requirements: Material requirements including properties, environment, application
            
        Returns:
            Material science analysis and substitution recommendations
        """
        logger.info("🔬 Applying material science reasoning",
                   primary_material=requirements.get("primary_material"),
                   application=requirements.get("application"))
        
        try:
            primary_material = requirements.get("primary_material", "").lower()
            application = requirements.get("application", "").lower()
            environment = requirements.get("environment", {})
            properties_required = requirements.get("properties_required", [])
            
            # Get material data for primary material
            material_data = None
            for mat_id, data in self.material_database.items():
                if (mat_id.lower() == primary_material or 
                    primary_material in [name.lower() for name in data.common_names]):
                    material_data = data
                    break
            
            analysis_results = {
                "primary_material_analysis": {},
                "substitution_candidates": [],
                "compatibility_assessment": {},
                "application_suitability": {},
                "recommendations": []
            }
            
            if material_data:
                # Analyze primary material
                analysis_results["primary_material_analysis"] = {
                    "material_id": material_data.material_id,
                    "properties": {prop.value: val for prop, val in material_data.mechanical_properties.items()},
                    "applications": material_data.applications,
                    "limitations": material_data.limitations,
                    "processing_requirements": material_data.processing_requirements
                }
                
                # Find substitution candidates
                substitution_candidates = await self._find_material_substitutes(
                    material_data, requirements
                )
                analysis_results["substitution_candidates"] = substitution_candidates
                
                # Assess environmental compatibility
                compatibility = await self._assess_environmental_compatibility(
                    material_data, environment
                )
                analysis_results["compatibility_assessment"] = compatibility
                
                # Application suitability analysis
                suitability = await self._assess_application_suitability(
                    material_data, application, properties_required
                )
                analysis_results["application_suitability"] = suitability
                
            else:
                analysis_results["recommendations"].append(
                    f"Material '{primary_material}' not found in database"
                )
            
            # Generate engineering recommendations
            engineering_recommendations = await self._generate_engineering_recommendations(
                analysis_results, requirements
            )
            analysis_results["recommendations"].extend(engineering_recommendations)
            
            logger.info("✅ Material science reasoning completed",
                       substitutes_found=len(analysis_results["substitution_candidates"]))
            
            return analysis_results
            
        except Exception as e:
            logger.error("❌ Material science reasoning failed", error=str(e))
            return {
                "error": str(e),
                "recommendations": ["Manual materials engineering review required"]
            }
    
    # Helper methods
    
    def _generate_compliance_notes(self, standards: List[Dict[str, Any]]) -> List[str]:
        """Generate compliance notes for applicable standards"""
        notes = []
        
        if any(std.get("certification_required") for std in standards):
            notes.append("Third-party certification may be required")
        
        testing_methods = set()
        for std in standards:
            testing_methods.update(std.get("testing_methods", []))
        
        if testing_methods:
            notes.append(f"Testing required: {', '.join(testing_methods)}")
        
        return notes
    
    def _generate_compliance_action_items(self, regulations: List[Dict[str, Any]], 
                                        part_spec: Dict[str, Any]) -> List[str]:
        """Generate specific compliance action items"""
        action_items = []
        
        for regulation in regulations:
            domain = regulation["domain"]
            
            if domain == "fda":
                action_items.append("Verify biocompatibility testing requirements")
                action_items.append("Check if 510(k) submission needed")
            elif domain == "osha":
                action_items.append("Obtain Safety Data Sheets for all materials")
                action_items.append("Ensure proper hazard labeling")
            elif domain == "itar":
                action_items.append("Verify export license requirements")
                action_items.append("Check foreign person access restrictions")
        
        return action_items
    
    def _assess_compliance_complexity(self, regulations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess overall compliance complexity"""
        
        if not regulations:
            return {"level": "none", "score": 0}
        
        high_complexity_domains = ["fda", "itar", "epa"]
        complexity_score = 0
        
        for regulation in regulations:
            if regulation["domain"] in high_complexity_domains:
                complexity_score += 3
            else:
                complexity_score += 1
        
        if complexity_score >= 6:
            level = "high"
        elif complexity_score >= 3:
            level = "medium"
        else:
            level = "low"
        
        return {
            "level": level,
            "score": complexity_score,
            "factors": [reg["domain"] for reg in regulations]
        }
    
    def _generate_compliance_recommendations(self, regulations: List[Dict[str, Any]], 
                                           complexity: Dict[str, Any]) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []
        
        if not regulations:
            recommendations.append("No specific regulatory requirements identified")
            return recommendations
        
        if complexity["level"] == "high":
            recommendations.append("Engage regulatory compliance specialist")
            recommendations.append("Allow extended timeline for approvals")
        
        if any(reg["domain"] == "fda" for reg in regulations):
            recommendations.append("Early FDA consultation recommended")
        
        if any(reg["domain"] == "itar" for reg in regulations):
            recommendations.append("Verify export control classification")
        
        return recommendations
    
    async def _find_material_substitutes(self, material_data: MaterialDatabase, 
                                       requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find suitable material substitutes based on requirements"""
        
        substitutes = []
        
        # Get equivalent materials from database
        for equivalent_id in material_data.equivalent_materials:
            if equivalent_id in self.material_database:
                equiv_data = self.material_database[equivalent_id]
                
                substitutes.append({
                    "material_id": equiv_data.material_id,
                    "common_names": equiv_data.common_names,
                    "substitution_type": "equivalent",
                    "properties": {prop.value: val for prop, val in equiv_data.mechanical_properties.items()},
                    "advantages": self._compare_materials(material_data, equiv_data, "advantages"),
                    "disadvantages": self._compare_materials(material_data, equiv_data, "disadvantages"),
                    "suitability_score": 0.9  # High for equivalent materials
                })
        
        # Apply substitution rules
        application = requirements.get("application", "").lower()
        environment = requirements.get("environment", {})
        
        for rule_name, rule_data in self.substitution_rules.items():
            if rule_name == "application_specific" and application:
                for app_type, app_rules in rule_data.items():
                    if app_type in application:
                        # Add preferred materials
                        for preferred in app_rules.get("prefer", []):
                            if preferred not in [s["material_id"] for s in substitutes]:
                                substitutes.append({
                                    "material_id": preferred,
                                    "substitution_type": "application_preferred",
                                    "suitability_score": 0.8,
                                    "reason": f"Preferred for {app_type} applications"
                                })
        
        return substitutes
    
    def _compare_materials(self, material1: MaterialDatabase, material2: MaterialDatabase, 
                          comparison_type: str) -> List[str]:
        """Compare two materials and return advantages/disadvantages"""
        comparisons = []
        
        # Simple property comparison - in full implementation would be more sophisticated
        if comparison_type == "advantages":
            # Check if material2 has higher strength
            if (MaterialProperty.TENSILE_STRENGTH in material1.mechanical_properties and 
                MaterialProperty.TENSILE_STRENGTH in material2.mechanical_properties):
                
                strength1 = material1.mechanical_properties[MaterialProperty.TENSILE_STRENGTH].get("value", 0)
                strength2 = material2.mechanical_properties[MaterialProperty.TENSILE_STRENGTH].get("value", 0)
                
                if strength2 > strength1:
                    comparisons.append("Higher tensile strength")
        
        return comparisons
    
    async def _assess_environmental_compatibility(self, material_data: MaterialDatabase, 
                                                environment: Dict[str, Any]) -> Dict[str, Any]:
        """Assess material compatibility with operating environment"""
        
        compatibility = {
            "overall_rating": "good",
            "specific_assessments": [],
            "concerns": [],
            "recommendations": []
        }
        
        # Check for corrosive environment
        if environment.get("corrosive") or environment.get("marine"):
            if "stainless" not in material_data.material_id.lower():
                compatibility["concerns"].append("Material may not be suitable for corrosive environment")
                compatibility["overall_rating"] = "poor"
                compatibility["recommendations"].append("Consider stainless steel alternative")
        
        # Check temperature requirements
        if environment.get("high_temperature"):
            if material_data.material_id == "6061":  # Aluminum has temperature limitations
                compatibility["concerns"].append("Aluminum has limited high-temperature capability")
                compatibility["recommendations"].append("Consider steel alternative for high temperature")
        
        return compatibility
    
    async def _assess_application_suitability(self, material_data: MaterialDatabase, 
                                            application: str, 
                                            properties_required: List[str]) -> Dict[str, Any]:
        """Assess material suitability for specific application"""
        
        suitability = {
            "overall_rating": "suitable",
            "application_match": [],
            "property_match": [],
            "limitations": material_data.limitations,
            "score": 0.8
        }
        
        # Check if application matches known applications
        for known_app in material_data.applications:
            if any(keyword in application for keyword in known_app.lower().split()):
                suitability["application_match"].append(known_app)
        
        # Check property requirements
        available_properties = set(prop.value for prop in material_data.mechanical_properties.keys())
        required_properties = set(properties_required)
        
        matched_properties = available_properties.intersection(required_properties)
        suitability["property_match"] = list(matched_properties)
        
        if matched_properties:
            suitability["score"] += 0.1 * len(matched_properties)
        
        return suitability
    
    async def _generate_engineering_recommendations(self, analysis_results: Dict[str, Any], 
                                                  requirements: Dict[str, Any]) -> List[str]:
        """Generate engineering recommendations based on analysis"""
        
        recommendations = []
        
        # Check if substitutes are available
        substitutes = analysis_results.get("substitution_candidates", [])
        if substitutes:
            top_substitute = max(substitutes, key=lambda x: x.get("suitability_score", 0))
            recommendations.append(
                f"Consider {top_substitute['material_id']} as alternative "
                f"(suitability score: {top_substitute.get('suitability_score', 0):.1f})"
            )
        
        # Environmental considerations
        compatibility = analysis_results.get("compatibility_assessment", {})
        if compatibility.get("overall_rating") == "poor":
            recommendations.append("Material not suitable for specified environment")
        
        # Application suitability
        suitability = analysis_results.get("application_suitability", {})
        if suitability.get("score", 0) < 0.5:
            recommendations.append("Material may not be optimal for this application")
        
        return recommendations
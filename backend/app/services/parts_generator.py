import random
import json
import csv
from typing import List, Dict, Any
from decimal import Decimal

try:
    import structlog
    logger = structlog.get_logger()
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

class LargePartsGenerator:
    """Generate realistic large-scale parts catalog for testing"""
    
    def __init__(self):
        # Material categories with realistic properties
        self.materials = {
            "stainless_steel": {
                "grades": ["304", "316", "316L", "317", "321", "347", "410", "420", "430", "17-4PH"],
                "finishes": ["2B", "BA", "No. 4", "No. 8", "Polished", "Brushed", "Mill"],
                "base_price_multiplier": 1.5,
                "density": 8.0  # g/cm³
            },
            "aluminum": {
                "grades": ["1100", "2024", "3003", "5052", "6061", "6063", "7075", "7050"],
                "tempers": ["O", "T3", "T4", "T6", "T651", "H14", "H18", "H32"],
                "finishes": ["Mill", "Anodized", "Powder Coated", "Painted", "Clad"],
                "base_price_multiplier": 0.8,
                "density": 2.7
            },
            "carbon_steel": {
                "grades": ["1008", "1010", "1018", "1020", "1045", "4130", "4140", "8620"],
                "finishes": ["Hot Rolled", "Cold Rolled", "Pickled", "Galvanized", "Zinc Plated"],
                "base_price_multiplier": 0.5,
                "density": 7.85
            },
            "alloy_steel": {
                "grades": ["4140", "4340", "8620", "9310", "A36", "A572", "A992"],
                "heat_treatments": ["Normalized", "Annealed", "Quenched", "Tempered", "Stress Relieved"],
                "base_price_multiplier": 0.7,
                "density": 7.85
            },
            "titanium": {
                "grades": ["Grade 1", "Grade 2", "Grade 5", "Grade 7", "Grade 9", "Grade 12"],
                "conditions": ["Annealed", "Solution Treated", "Aged"],
                "base_price_multiplier": 15.0,
                "density": 4.5
            },
            "brass": {
                "grades": ["C260", "C360", "C464", "C230", "C240"],
                "tempers": ["H01", "H02", "H04", "O50", "O60"],
                "base_price_multiplier": 2.5,
                "density": 8.5
            },
            "bronze": {
                "grades": ["C932", "C954", "C220", "C510", "C630"],
                "conditions": ["As Cast", "Heat Treated", "Work Hardened"],
                "base_price_multiplier": 3.0,
                "density": 8.8
            },
            "copper": {
                "grades": ["101", "110", "145", "194", "195"],
                "tempers": ["Soft", "Half Hard", "Hard", "Spring"],
                "base_price_multiplier": 4.0,
                "density": 8.96
            },
            "nickel_alloy": {
                "grades": ["Inconel 600", "Inconel 625", "Inconel 718", "Hastelloy C276", "Monel 400"],
                "conditions": ["Solution Annealed", "Aged", "Cold Worked"],
                "base_price_multiplier": 25.0,
                "density": 8.4
            },
            "tool_steel": {
                "grades": ["A2", "D2", "H13", "M2", "O1", "S7", "W1"],
                "conditions": ["Annealed", "Hardened", "Tempered"],
                "base_price_multiplier": 8.0,
                "density": 7.8
            }
        }
        
        # Product categories with realistic forms and sizes
        self.categories = {
            "sheet": {
                "thickness_range": (0.010, 2.0),
                "length_range": (12, 144),
                "width_range": (12, 96),
                "price_per_lb": 2.5
            },
            "plate": {
                "thickness_range": (0.25, 12.0),
                "length_range": (24, 240),
                "width_range": (24, 120),
                "price_per_lb": 2.8
            },
            "bar_round": {
                "diameter_range": (0.125, 12.0),
                "length_range": (12, 240),
                "price_per_lb": 3.2
            },
            "bar_square": {
                "side_range": (0.125, 8.0),
                "length_range": (12, 240),
                "price_per_lb": 3.5
            },
            "bar_rectangular": {
                "width_range": (0.25, 8.0),
                "height_range": (0.25, 4.0),
                "length_range": (12, 240),
                "price_per_lb": 3.3
            },
            "bar_hex": {
                "across_flats_range": (0.25, 6.0),
                "length_range": (12, 144),
                "price_per_lb": 4.0
            },
            "tube_round": {
                "od_range": (0.25, 12.0),
                "wall_range": (0.028, 1.0),
                "length_range": (12, 240),
                "price_per_lb": 4.5
            },
            "tube_square": {
                "od_range": (0.5, 8.0),
                "wall_range": (0.049, 0.5),
                "length_range": (12, 240),
                "price_per_lb": 4.8
            },
            "tube_rectangular": {
                "width_range": (0.75, 8.0),
                "height_range": (0.5, 6.0),
                "wall_range": (0.049, 0.5),
                "length_range": (12, 240),
                "price_per_lb": 4.7
            },
            "angle": {
                "leg1_range": (0.5, 8.0),
                "leg2_range": (0.5, 8.0),
                "thickness_range": (0.125, 1.0),
                "length_range": (12, 240),
                "price_per_lb": 3.8
            },
            "channel": {
                "depth_range": (2.0, 15.0),
                "flange_range": (1.0, 4.0),
                "thickness_range": (0.125, 0.75),
                "length_range": (12, 240),
                "price_per_lb": 4.2
            },
            "beam_i": {
                "depth_range": (3.0, 36.0),
                "flange_range": (2.5, 16.0),
                "thickness_range": (0.25, 2.0),
                "length_range": (12, 480),
                "price_per_lb": 3.5
            },
            "wire": {
                "diameter_range": (0.010, 0.5),
                "length_range": (100, 10000),  # feet
                "price_per_lb": 5.5
            },
            "foil": {
                "thickness_range": (0.0005, 0.010),
                "width_range": (6, 48),
                "length_range": (100, 10000),  # feet
                "price_per_lb": 12.0
            }
        }
        
        # Realistic suppliers
        self.suppliers = [
            "MetalMart Industries", "SteelCorp Supply", "AlumTech Solutions", 
            "TitaniumPro Inc", "BrassWorks LLC", "CopperSource Ltd",
            "AlloyMasters Corp", "PrecisionMetal Co", "IndustrialMetals Inc",
            "MetalDepot Supply", "SteelWorks Express", "AluminumDirect",
            "SpecialtyAlloys Ltd", "MetalCrafters Inc", "SteelSolutions Pro",
            "MetalTech Industries", "AlloySupply Corp", "SteelMasters Ltd",
            "MetalWarehouse Co", "PremiumSteel Inc", "MetalDistributors LLC",
            "SteelConnection", "MetalSource Pro", "AlloyExperts Inc",
            "MetalSupply Direct", "SteelTech Solutions", "MetalCraft Supply"
        ]
    
    def generate_part_number(self, material_key: str, category: str, specifications: Dict) -> str:
        """Generate realistic part number"""
        # Material prefix
        material_prefixes = {
            "stainless_steel": "SS",
            "aluminum": "AL", 
            "carbon_steel": "CS",
            "alloy_steel": "AS",
            "titanium": "TI",
            "brass": "BR",
            "bronze": "BZ",
            "copper": "CU",
            "nickel_alloy": "NI",
            "tool_steel": "TS"
        }
        
        # Category codes
        category_codes = {
            "sheet": "SH", "plate": "PL", "bar_round": "BR", "bar_square": "BS",
            "bar_rectangular": "BX", "bar_hex": "BH", "tube_round": "TR",
            "tube_square": "TS", "tube_rectangular": "TX", "angle": "AN",
            "channel": "CH", "beam_i": "BM", "wire": "WR", "foil": "FL"
        }
        
        prefix = material_prefixes.get(material_key, "XX")
        cat_code = category_codes.get(category, "XX")
        
        # Add grade/specification info
        grade = specifications.get("grade", "STD")
        
        # Add dimensional info (simplified)
        if category in ["sheet", "plate"]:
            dim = f"{specifications.get('length', 0):.0f}x{specifications.get('width', 0):.0f}x{specifications.get('thickness', 0):.3f}"
        elif "bar" in category:
            if category == "bar_round":
                dim = f"D{specifications.get('diameter', 0):.3f}x{specifications.get('length', 0):.0f}"
            elif category == "bar_square":
                dim = f"{specifications.get('side', 0):.3f}x{specifications.get('length', 0):.0f}"
            elif category == "bar_rectangular":
                dim = f"{specifications.get('width', 0):.3f}x{specifications.get('height', 0):.3f}x{specifications.get('length', 0):.0f}"
            elif category == "bar_hex":
                dim = f"HEX{specifications.get('across_flats', 0):.3f}x{specifications.get('length', 0):.0f}"
        elif "tube" in category:
            if category == "tube_round":
                dim = f"OD{specifications.get('outer_diameter', 0):.3f}x{specifications.get('wall_thickness', 0):.3f}x{specifications.get('length', 0):.0f}"
            else:
                dim = f"{specifications.get('width', 0):.3f}x{specifications.get('height', 0):.3f}x{specifications.get('wall_thickness', 0):.3f}"
        else:
            dim = f"{random.randint(100, 999)}"
        
        return f"{prefix}-{grade}-{cat_code}-{dim}".replace(".", "")
    
    def calculate_weight(self, material_key: str, category: str, specifications: Dict) -> float:
        """Calculate realistic weight based on material and dimensions"""
        density = self.materials[material_key]["density"]  # g/cm³
        
        # Convert to lb/in³ (1 g/cm³ = 0.0361 lb/in³)
        density_lb_in3 = density * 0.0361
        
        volume = 0  # cubic inches
        
        if category in ["sheet", "plate"]:
            volume = specifications["length"] * specifications["width"] * specifications["thickness"]
        elif category == "bar_round":
            radius = specifications["diameter"] / 2
            volume = 3.14159 * radius * radius * specifications["length"]
        elif category == "bar_square":
            volume = specifications["side"] * specifications["side"] * specifications["length"]
        elif category == "bar_rectangular":
            volume = specifications["width"] * specifications["height"] * specifications["length"]
        elif category == "bar_hex":
            # Hexagon area = (3√3/2) * s² where s is across flats
            s = specifications["across_flats"]
            area = (3 * 1.732 / 2) * s * s
            volume = area * specifications["length"]
        elif category == "tube_round":
            od = specifications["outer_diameter"]
            wall = specifications["wall_thickness"]
            id_radius = (od - 2 * wall) / 2
            od_radius = od / 2
            volume = 3.14159 * (od_radius * od_radius - id_radius * id_radius) * specifications["length"]
        elif category in ["tube_square", "tube_rectangular"]:
            outer_area = specifications["width"] * specifications["height"]
            inner_width = specifications["width"] - 2 * specifications["wall_thickness"]
            inner_height = specifications["height"] - 2 * specifications["wall_thickness"]
            inner_area = max(0, inner_width * inner_height)
            volume = (outer_area - inner_area) * specifications["length"]
        elif category == "angle":
            # L-shaped cross section
            leg1 = specifications["leg1"]
            leg2 = specifications["leg2"]
            thickness = specifications["thickness"]
            area = leg1 * thickness + leg2 * thickness - thickness * thickness
            volume = area * specifications["length"]
        elif category == "wire":
            radius = specifications["diameter"] / 2
            volume = 3.14159 * radius * radius * specifications["length"] * 12  # convert feet to inches
        elif category == "foil":
            volume = specifications["width"] * specifications["thickness"] * specifications["length"] * 12
        else:
            volume = 10  # fallback
        
        return volume * density_lb_in3
    
    def generate_specifications(self, material_key: str, category: str) -> Dict[str, Any]:
        """Generate realistic specifications for a part"""
        material = self.materials[material_key]
        cat_info = self.categories[category]
        
        specs = {
            "units": "inches"
        }
        
        # Add material-specific properties
        if "grades" in material:
            specs["grade"] = random.choice(material["grades"])
        if "finishes" in material:
            specs["finish"] = random.choice(material["finishes"])
        if "tempers" in material:
            specs["temper"] = random.choice(material["tempers"])
        if "conditions" in material:
            specs["condition"] = random.choice(material["conditions"])
        if "heat_treatments" in material:
            specs["heat_treatment"] = random.choice(material["heat_treatments"])
        
        # Add dimensional specifications based on category
        if category in ["sheet", "plate"]:
            specs["length"] = round(random.uniform(*cat_info["length_range"]), 2)
            specs["width"] = round(random.uniform(*cat_info["width_range"]), 2)
            specs["thickness"] = round(random.uniform(*cat_info["thickness_range"]), 3)
        
        elif category == "bar_round":
            specs["diameter"] = round(random.uniform(*cat_info["diameter_range"]), 3)
            specs["length"] = round(random.uniform(*cat_info["length_range"]), 1)
        
        elif category == "bar_square":
            specs["side"] = round(random.uniform(*cat_info["side_range"]), 3)
            specs["length"] = round(random.uniform(*cat_info["length_range"]), 1)
        
        elif category == "bar_rectangular":
            specs["width"] = round(random.uniform(*cat_info["width_range"]), 3)
            specs["height"] = round(random.uniform(*cat_info["height_range"]), 3)
            specs["length"] = round(random.uniform(*cat_info["length_range"]), 1)
        
        elif category == "bar_hex":
            specs["across_flats"] = round(random.uniform(*cat_info["across_flats_range"]), 3)
            specs["length"] = round(random.uniform(*cat_info["length_range"]), 1)
        
        elif category == "tube_round":
            specs["outer_diameter"] = round(random.uniform(*cat_info["od_range"]), 3)
            specs["wall_thickness"] = round(random.uniform(*cat_info["wall_range"]), 3)
            specs["length"] = round(random.uniform(*cat_info["length_range"]), 1)
        
        elif category in ["tube_square", "tube_rectangular"]:
            if category == "tube_rectangular":
                specs["width"] = round(random.uniform(*cat_info["width_range"]), 3)
                specs["height"] = round(random.uniform(*cat_info["height_range"]), 3)
            else:  # tube_square
                side = round(random.uniform(*cat_info["od_range"]), 3)
                specs["width"] = side
                specs["height"] = side
            specs["wall_thickness"] = round(random.uniform(*cat_info["wall_range"]), 3)
            specs["length"] = round(random.uniform(*cat_info["length_range"]), 1)
        
        elif category == "angle":
            specs["leg1"] = round(random.uniform(*cat_info["leg1_range"]), 3)
            specs["leg2"] = round(random.uniform(*cat_info["leg2_range"]), 3)
            specs["thickness"] = round(random.uniform(*cat_info["thickness_range"]), 3)
            specs["length"] = round(random.uniform(*cat_info["length_range"]), 1)
        
        elif category == "wire":
            specs["diameter"] = round(random.uniform(*cat_info["diameter_range"]), 4)
            specs["length"] = round(random.uniform(*cat_info["length_range"]), 0)
            specs["units"] = "feet"
        
        elif category == "foil":
            specs["thickness"] = round(random.uniform(*cat_info["thickness_range"]), 4)
            specs["width"] = round(random.uniform(*cat_info["width_range"]), 1)
            specs["length"] = round(random.uniform(*cat_info["length_range"]), 0)
            specs["units"] = "feet"
        
        return specs
    
    def generate_single_part(self) -> Dict[str, Any]:
        """Generate a single realistic part"""
        # Choose random material and category
        material_key = random.choice(list(self.materials.keys()))
        category = random.choice(list(self.categories.keys()))
        
        material = self.materials[material_key]
        cat_info = self.categories[category]
        
        # Generate specifications
        specifications = self.generate_specifications(material_key, category)
        
        # Generate part number
        part_number = self.generate_part_number(material_key, category, specifications)
        
        # Calculate weight
        weight = self.calculate_weight(material_key, category, specifications)
        
        # Calculate price
        base_price_per_lb = cat_info["price_per_lb"] * material["base_price_multiplier"]
        unit_price = round(weight * base_price_per_lb * random.uniform(0.8, 1.3), 2)
        
        # Generate description
        material_name = material_key.replace("_", " ").title()
        category_name = category.replace("_", " ").title()
        grade = specifications.get("grade", "")
        
        if category in ["sheet", "plate"]:
            desc = f"{material_name} {grade} {category_name}, {specifications['length']}\" x {specifications['width']}\" x {specifications['thickness']}\" thick"
        elif category == "bar_round":
            desc = f"{material_name} {grade} Round Bar, {specifications['diameter']}\" diameter x {specifications['length']}\" length"
        elif category == "bar_square":
            desc = f"{material_name} {grade} Square Bar, {specifications['side']}\" x {specifications['length']}\" length"
        elif category == "bar_rectangular":
            desc = f"{material_name} {grade} Rectangular Bar, {specifications['width']}\" x {specifications['height']}\" x {specifications['length']}\" length"
        elif category == "bar_hex":
            desc = f"{material_name} {grade} Hexagonal Bar, {specifications['across_flats']}\" across flats x {specifications['length']}\" length"
        elif category == "tube_round":
            desc = f"{material_name} {grade} Round Tube, {specifications['outer_diameter']}\" OD x {specifications['wall_thickness']}\" wall x {specifications['length']}\" length"
        elif category in ["tube_square", "tube_rectangular"]:
            desc = f"{material_name} {grade} {category_name.replace('_', ' ')}, {specifications['width']}\" x {specifications['height']}\" x {specifications['wall_thickness']}\" wall"
        elif category == "angle":
            desc = f"{material_name} {grade} Angle, {specifications['leg1']}\" x {specifications['leg2']}\" x {specifications['thickness']}\" thick"
        elif category == "wire":
            desc = f"{material_name} {grade} Wire, {specifications['diameter']}\" diameter x {specifications['length']} feet"
        elif category == "foil":
            desc = f"{material_name} {grade} Foil, {specifications['width']}\" wide x {specifications['thickness']}\" thick x {specifications['length']} feet"
        else:
            desc = f"{material_name} {grade} {category_name}"
        
        # Generate availability and other properties
        availability = random.randint(0, 1000)
        minimum_order = random.choice([1, 1, 1, 5, 10, 25, 50, 100])  # weighted toward lower minimums
        supplier = random.choice(self.suppliers)
        
        return {
            "part_number": part_number,
            "description": desc,
            "category": category_name,
            "material": f"{material_name} {grade}".strip(),
            "specifications": specifications,
            "unit_price": unit_price,
            "availability": availability,
            "supplier": supplier,
            "weight_per_unit": round(weight, 2),
            "minimum_order": minimum_order
        }
    
    def generate_parts_catalog(self, num_parts: int) -> List[Dict[str, Any]]:
        """Generate a large parts catalog"""
        logger.info(f"Generating {num_parts} parts for catalog...")
        
        parts = []
        for i in range(num_parts):
            if i % 1000 == 0:
                logger.info(f"Generated {i}/{num_parts} parts...")
            
            part = self.generate_single_part()
            parts.append(part)
        
        logger.info(f"Generated {len(parts)} parts successfully")
        return parts
    
    def save_to_csv(self, parts: List[Dict[str, Any]], filename: str):
        """Save parts catalog to CSV file"""
        logger.info(f"Saving {len(parts)} parts to {filename}")
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            if not parts:
                return
            
            # Get all possible field names
            fieldnames = set()
            for part in parts:
                fieldnames.update(part.keys())
                if 'specifications' in part:
                    fieldnames.update(part['specifications'].keys())
            
            fieldnames = sorted(list(fieldnames))
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for part in parts:
                # Flatten specifications
                row = part.copy()
                if 'specifications' in row:
                    specs = row.pop('specifications')
                    row.update(specs)
                
                writer.writerow(row)
        
        logger.info(f"Saved parts catalog to {filename}")
    
    def save_to_json(self, parts: List[Dict[str, Any]], filename: str):
        """Save parts catalog to JSON file"""
        logger.info(f"Saving {len(parts)} parts to {filename}")
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(parts, jsonfile, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved parts catalog to {filename}")
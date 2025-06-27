#!/usr/bin/env python3
"""
Parts Database Generator
Generates 50,000 unique industrial parts for the sales order system
"""

import sqlite3
import random
import string
from datetime import datetime, timedelta
from decimal import Decimal
import json

# Part categories and their subcategories
PART_CATEGORIES = {
    "Fasteners": [
        "Bolts", "Screws", "Nuts", "Washers", "Rivets", "Pins", "Clips", "Anchors"
    ],
    "Raw Materials": [
        "Bars", "Sheets", "Plates", "Tubes", "Pipes", "Angles", "Channels", "Beams"
    ],
    "Bearings": [
        "Ball Bearings", "Roller Bearings", "Thrust Bearings", "Pillow Blocks", "Sleeve Bearings"
    ],
    "Seals & Gaskets": [
        "O-Rings", "Oil Seals", "Gaskets", "Mechanical Seals", "Packing"
    ],
    "Electrical": [
        "Connectors", "Cables", "Switches", "Relays", "Fuses", "Terminals"
    ],
    "Hydraulic": [
        "Cylinders", "Pumps", "Valves", "Hoses", "Fittings", "Filters"
    ],
    "Pneumatic": [
        "Cylinders", "Valves", "Fittings", "Tubing", "Filters", "Regulators"
    ],
    "Tools": [
        "Cutting Tools", "Measuring Tools", "Hand Tools", "Power Tools", "Abrasives"
    ],
    "Safety": [
        "PPE", "Safety Equipment", "Emergency Equipment", "Warning Devices"
    ],
    "Mechanical": [
        "Gears", "Sprockets", "Chains", "Belts", "Pulleys", "Couplings"
    ]
}

# Materials with their typical grades
MATERIALS = {
    "Steel": ["A36", "1018", "1045", "4140", "4340", "A572 Gr 50"],
    "Stainless Steel": ["304", "316", "316L", "321", "347", "410", "430", "17-4 PH"],
    "Aluminum": ["6061-T6", "6063-T5", "2024-T3", "7075-T6", "5052-H32", "1100-H14"],
    "Brass": ["C360", "C260", "C464", "C230"],
    "Bronze": ["C932", "C954", "C630"],
    "Copper": ["C101", "C110", "C145"],
    "Titanium": ["Grade 2", "Grade 5", "Grade 7", "Grade 9"],
    "Inconel": ["600", "625", "718", "X-750"],
    "Hastelloy": ["C-276", "C-22", "B-3"],
    "Plastic": ["Nylon", "Delrin", "PTFE", "PEEK", "Polycarbonate", "ABS"]
}

# Form factors for different categories
FORM_FACTORS = {
    "Fasteners": ["Hex Head", "Socket Head", "Flat Head", "Round Head", "Pan Head", "Truss Head"],
    "Raw Materials": ["Round Bar", "Square Bar", "Flat Bar", "Sheet", "Plate", "Tube"],
    "Bearings": ["Deep Groove", "Angular Contact", "Cylindrical", "Spherical", "Thrust"],
    "Seals & Gaskets": ["Standard", "High Temp", "Chemical Resistant", "Food Grade"],
    "Electrical": ["Male", "Female", "Hermaphroditic", "Right Angle", "Straight"],
    "Default": ["Standard", "Heavy Duty", "Light Duty", "Precision", "Commercial"]
}

# Surface finishes
SURFACE_FINISHES = [
    "As Machined", "Anodized", "Zinc Plated", "Chrome Plated", "Nickel Plated",
    "Black Oxide", "Passivated", "Powder Coated", "Hot Dip Galvanized",
    "Phosphate Coated", "Painted", "Polished", "Brushed", "Sandblasted"
]

# Hardness values
HARDNESS_VALUES = [
    "HRC 20-25", "HRC 25-30", "HRC 30-35", "HRC 35-40", "HRC 40-45",
    "HRC 45-50", "HRC 50-55", "HRC 55-60", "HRB 60-80", "HRB 80-100",
    "Shore A 70", "Shore A 80", "Shore A 90", "Shore D 40", "Shore D 60"
]

# Availability statuses
AVAILABILITY_STATUSES = ["IN_STOCK", "LIMITED", "BACKORDER", "DISCONTINUED", "SPECIAL_ORDER"]

# Suppliers (matching the schema)
SUPPLIERS = [
    ("SUP001", "Industrial Metals Corp"),
    ("SUP002", "Precision Fasteners LLC"),
    ("SUP003", "Advanced Materials Inc"),
    ("SUP004", "Stainless Solutions"),
    ("SUP005", "Alloy Specialists"),
    ("SUP006", "High Performance Metals"),
    ("SUP007", "Custom Fabrication Works"),
    ("SUP008", "Quality Hardware Supply"),
    ("SUP009", "Aerospace Grade Materials"),
    ("SUP010", "Marine Metal Works")
]

def generate_part_number(category, subcategory, index):
    """Generate a realistic part number"""
    cat_prefix = category[:3].upper()
    subcat_prefix = subcategory[:2].upper()
    
    # Generate a mix of part number formats
    formats = [
        f"{cat_prefix}-{subcat_prefix}-{index:05d}",
        f"{cat_prefix}{subcat_prefix}{index:06d}",
        f"{cat_prefix}-{index:04d}-{subcat_prefix}",
        f"{random.choice(string.ascii_uppercase)}{cat_prefix}{index:05d}"
    ]
    
    return random.choice(formats)

def generate_dimensions():
    """Generate realistic dimensions"""
    # Common fractional and decimal sizes
    common_sizes = [
        0.125, 0.1875, 0.25, 0.3125, 0.375, 0.4375, 0.5, 0.5625, 0.625, 0.75,
        0.875, 1.0, 1.125, 1.25, 1.375, 1.5, 1.75, 2.0, 2.25, 2.5, 3.0, 3.5,
        4.0, 4.5, 5.0, 6.0, 8.0, 10.0, 12.0
    ]
    
    diameter = random.choice(common_sizes) if random.random() < 0.7 else round(random.uniform(0.1, 24.0), 4)
    length = random.choice(common_sizes) if random.random() < 0.6 else round(random.uniform(0.25, 120.0), 4)
    width = random.choice(common_sizes) if random.random() < 0.5 else round(random.uniform(0.1, 48.0), 4)
    height = random.choice(common_sizes) if random.random() < 0.5 else round(random.uniform(0.1, 36.0), 4)
    thickness = random.choice([0.0625, 0.125, 0.1875, 0.25, 0.375, 0.5, 0.75, 1.0]) if random.random() < 0.6 else round(random.uniform(0.03, 2.0), 4)
    
    return diameter, length, width, height, thickness

def generate_pricing():
    """Generate realistic pricing"""
    # Cost ranges by category complexity
    cost_ranges = {
        "simple": (0.05, 25.0),
        "moderate": (5.0, 250.0),
        "complex": (50.0, 2500.0),
        "specialty": (100.0, 5000.0)
    }
    
    complexity = random.choices(
        ["simple", "moderate", "complex", "specialty"],
        weights=[40, 35, 20, 5]
    )[0]
    
    cost = round(random.uniform(*cost_ranges[complexity]), 2)
    markup = random.uniform(1.5, 3.5)  # 50% to 250% markup
    list_price = round(cost * markup, 2)
    
    return cost, list_price

def generate_description(category, subcategory, material, material_grade, form_factor, dimensions):
    """Generate realistic part descriptions"""
    diameter, length, width, height, thickness = dimensions
    
    desc_parts = []
    
    # Add material info
    if material_grade:
        desc_parts.append(f"{material} {material_grade}")
    else:
        desc_parts.append(material)
    
    # Add form factor
    if form_factor:
        desc_parts.append(form_factor)
    
    # Add subcategory
    desc_parts.append(subcategory.rstrip('s'))  # Remove plural
    
    # Add key dimensions
    if category == "Fasteners":
        if diameter and length:
            desc_parts.append(f"{diameter}\" x {length}\"")
    elif category == "Raw Materials":
        if subcategory in ["Bars", "Tubes", "Pipes"]:
            if diameter:
                desc_parts.append(f"{diameter}\" Dia")
            if length > 0:
                desc_parts.append(f"{length}\" Length")
        elif subcategory in ["Sheets", "Plates"]:
            if thickness and width and height:
                desc_parts.append(f"{thickness}\" x {width}\" x {height}\"")
    elif category == "Bearings":
        if diameter:
            desc_parts.append(f"{diameter}\" Bore")
    
    # Add special features occasionally
    features = ["High Temp", "Corrosion Resistant", "Precision", "Heavy Duty", "Food Grade"]
    if random.random() < 0.2:
        desc_parts.insert(-1, random.choice(features))
    
    return " ".join(desc_parts)

def generate_keywords(category, subcategory, material, description):
    """Generate search keywords"""
    keywords = []
    
    # Add category variations
    keywords.extend([category.lower(), subcategory.lower()])
    
    # Add material variations
    keywords.append(material.lower())
    
    # Add common synonyms and abbreviations
    synonyms = {
        "stainless steel": ["ss", "stainless", "corrosion resistant"],
        "aluminum": ["al", "aluminium", "lightweight"],
        "steel": ["carbon steel", "mild steel"],
        "fasteners": ["hardware", "bolts", "screws"],
        "bearings": ["bearing", "ball bearing", "roller bearing"],
        "hydraulic": ["fluid power", "pressure"],
        "pneumatic": ["air", "compressed air"]
    }
    
    for key, values in synonyms.items():
        if key in description.lower():
            keywords.extend(values)
    
    # Add dimension-based keywords
    if "0.25" in description or "1/4" in description:
        keywords.append("quarter inch")
    if "0.5" in description or "1/2" in description:
        keywords.append("half inch")
    
    return ", ".join(set(keywords))

def generate_specifications(category, material, surface_finish, hardness, tensile_strength):
    """Generate technical specifications"""
    specs = {}
    
    if material:
        specs["material"] = material
    if surface_finish:
        specs["surface_finish"] = surface_finish
    if hardness:
        specs["hardness"] = hardness
    if tensile_strength:
        specs["tensile_strength_psi"] = tensile_strength
    
    # Add category-specific specs
    if category == "Fasteners":
        specs["thread_type"] = random.choice(["UNC", "UNF", "Metric", "ACME", "NPT"])
        specs["drive_type"] = random.choice(["Hex", "Phillips", "Slotted", "Torx", "Socket"])
    elif category == "Bearings":
        specs["seal_type"] = random.choice(["Open", "Shielded", "Sealed", "Contact Seal"])
        specs["precision_class"] = random.choice(["ABEC-1", "ABEC-3", "ABEC-5", "ABEC-7"])
    elif category == "Electrical":
        specs["voltage_rating"] = f"{random.choice([12, 24, 110, 220, 480])}V"
        specs["current_rating"] = f"{random.choice([1, 5, 10, 15, 20, 30])}A"
    
    return json.dumps(specs)

def create_database():
    """Create and populate the SQLite database"""
    print("Creating parts database...")
    
    # Connect to database
    conn = sqlite3.connect('/Users/riverscornelson/PycharmProjects/sales-order-system/backend/parts_catalog.db')
    cursor = conn.cursor()
    
    # Read and execute schema
    with open('/Users/riverscornelson/PycharmProjects/sales-order-system/backend/database_schema.sql', 'r') as f:
        schema = f.read()
    
    # Execute schema (split by semicolon to handle multiple statements)
    for statement in schema.split(';'):
        if statement.strip():
            cursor.execute(statement)
    
    conn.commit()
    print("Database schema created successfully")
    
    # Generate 50,000 parts
    print("Generating 50,000 parts...")
    parts_data = []
    
    for i in range(50000):
        if i % 5000 == 0:
            print(f"Generated {i} parts...")
        
        # Select random category and subcategory
        category = random.choice(list(PART_CATEGORIES.keys()))
        subcategory = random.choice(PART_CATEGORIES[category])
        
        # Select material and grade
        material = random.choice(list(MATERIALS.keys()))
        material_grade = random.choice(MATERIALS[material]) if random.random() < 0.8 else None
        
        # Select form factor
        form_factors = FORM_FACTORS.get(category, FORM_FACTORS["Default"])
        form_factor = random.choice(form_factors) if random.random() < 0.7 else None
        
        # Generate dimensions
        dimensions = generate_dimensions()
        diameter, length, width, height, thickness = dimensions
        
        # Generate other attributes
        part_number = generate_part_number(category, subcategory, i + 1)
        description = generate_description(category, subcategory, material, material_grade, form_factor, dimensions)
        
        # Generate pricing
        cost, list_price = generate_pricing()
        
        # Generate inventory and availability
        availability_status = random.choices(
            AVAILABILITY_STATUSES,
            weights=[70, 15, 8, 4, 3]  # Mostly in stock
        )[0]
        
        quantity_on_hand = random.randint(0, 1000) if availability_status == "IN_STOCK" else random.randint(0, 50)
        minimum_order_qty = random.choice([1, 5, 10, 25, 50, 100])
        lead_time = random.randint(0, 30) if availability_status == "IN_STOCK" else random.randint(7, 90)
        
        # Generate technical specs
        surface_finish = random.choice(SURFACE_FINISHES) if random.random() < 0.6 else None
        hardness = random.choice(HARDNESS_VALUES) if random.random() < 0.4 else None
        tensile_strength = random.randint(30000, 200000) if material == "Steel" else None
        
        # Generate other fields
        supplier_id, supplier_name = random.choice(SUPPLIERS)
        manufacturer = random.choice([supplier_name, f"OEM-{random.randint(100, 999)}"])
        manufacturer_part_number = f"MPN-{random.randint(100000, 999999)}"
        
        weight = round(random.uniform(0.001, 50.0), 4)
        keywords = generate_keywords(category, subcategory, material, description)
        specifications = generate_specifications(category, material, surface_finish, hardness, tensile_strength)
        
        # Create dimensions string
        dim_parts = []
        if diameter: dim_parts.append(f"Dia: {diameter}\"")
        if length: dim_parts.append(f"L: {length}\"")
        if width: dim_parts.append(f"W: {width}\"")
        if height: dim_parts.append(f"H: {height}\"")
        if thickness: dim_parts.append(f"T: {thickness}\"")
        dimensions_str = ", ".join(dim_parts)
        
        # Thread pitch for fasteners
        thread_pitch = None
        if category == "Fasteners" and random.random() < 0.8:
            if random.random() < 0.6:  # UNC/UNF
                thread_pitch = f"{random.choice([8, 10, 12, 16, 18, 20, 24, 28, 32])}"
            else:  # Metric
                thread_pitch = f"M{random.choice([1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0])}"
        
        part_data = (
            part_number, description, category, subcategory, material, material_grade,
            form_factor, dimensions_str, weight, "EA", list_price, cost,
            availability_status, quantity_on_hand, minimum_order_qty, lead_time,
            supplier_id, supplier_name, manufacturer, manufacturer_part_number,
            diameter, length, width, height, thickness, thread_pitch,
            surface_finish, hardness, tensile_strength, keywords, specifications,
            f"Used in {category.lower()} applications", f"Notes for {part_number}"
        )
        
        parts_data.append(part_data)
    
    # Insert parts data in batches
    print("Inserting parts into database...")
    batch_size = 1000
    
    insert_sql = """
    INSERT INTO parts_catalog (
        part_number, description, category, subcategory, material, material_grade,
        form_factor, dimensions, weight_lbs, unit_of_measure, list_price, cost,
        availability_status, quantity_on_hand, minimum_order_quantity, lead_time_days,
        supplier_id, supplier_name, manufacturer, manufacturer_part_number,
        diameter_inches, length_inches, width_inches, height_inches, thickness_inches,
        thread_pitch, surface_finish, hardness, tensile_strength_psi,
        keywords, specifications, applications, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    for i in range(0, len(parts_data), batch_size):
        batch = parts_data[i:i + batch_size]
        cursor.executemany(insert_sql, batch)
        conn.commit()
        print(f"Inserted batch {i//batch_size + 1}/{(len(parts_data) + batch_size - 1)//batch_size}")
    
    # Update FTS index
    print("Building full-text search index...")
    cursor.execute("""
        INSERT INTO parts_search(part_number, description, keywords, specifications)
        SELECT part_number, description, keywords, specifications FROM parts_catalog
    """)
    
    conn.commit()
    
    # Print statistics
    cursor.execute("SELECT COUNT(*) FROM parts_catalog")
    total_parts = cursor.fetchone()[0]
    
    cursor.execute("SELECT category, COUNT(*) FROM parts_catalog GROUP BY category ORDER BY COUNT(*) DESC")
    categories = cursor.fetchall()
    
    print(f"\nDatabase created successfully!")
    print(f"Total parts: {total_parts:,}")
    print("\nParts by category:")
    for category, count in categories:
        print(f"  {category}: {count:,}")
    
    conn.close()

if __name__ == "__main__":
    create_database()
    print("\nParts database generation complete!")
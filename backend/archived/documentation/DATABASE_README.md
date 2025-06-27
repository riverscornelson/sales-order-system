# Sales Order System - Local Parts Database

This document describes the local SQLite database containing 50,000 unique industrial parts for the sales order system.

## 🗃️ Database Overview

The parts catalog database (`parts_catalog.db`) contains a comprehensive collection of industrial parts across multiple categories:

- **Total Parts**: 50,000 unique items
- **Database Type**: SQLite 3
- **Size**: ~45 MB
- **Full-Text Search**: Enabled via FTS5
- **Indexed Fields**: Part number, category, material, availability

## 📊 Database Schema

### Main Tables

#### `parts_catalog` - Core parts data
```sql
CREATE TABLE parts_catalog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_number VARCHAR(50) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100),
    material VARCHAR(100),
    material_grade VARCHAR(50),
    form_factor VARCHAR(50),
    dimensions VARCHAR(200),
    weight_lbs DECIMAL(10,4),
    unit_of_measure VARCHAR(20) DEFAULT 'EA',
    list_price DECIMAL(12,2),
    cost DECIMAL(12,2),
    availability_status VARCHAR(20) DEFAULT 'IN_STOCK',
    quantity_on_hand INTEGER DEFAULT 0,
    minimum_order_quantity INTEGER DEFAULT 1,
    lead_time_days INTEGER DEFAULT 0,
    supplier_id VARCHAR(50),
    supplier_name VARCHAR(200),
    manufacturer VARCHAR(200),
    manufacturer_part_number VARCHAR(100),
    
    -- Technical specifications
    diameter_inches DECIMAL(8,4),
    length_inches DECIMAL(8,4),
    width_inches DECIMAL(8,4),
    height_inches DECIMAL(8,4),
    thickness_inches DECIMAL(8,4),
    thread_pitch VARCHAR(20),
    surface_finish VARCHAR(100),
    hardness VARCHAR(50),
    tensile_strength_psi INTEGER,
    
    -- Search and metadata
    keywords TEXT,
    specifications TEXT,
    applications TEXT,
    notes TEXT,
    
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN DEFAULT 1
);
```

#### `parts_search` - Full-text search index
```sql
CREATE VIRTUAL TABLE parts_search USING fts5(
    part_number,
    description,
    keywords,
    specifications,
    content='parts_catalog'
);
```

#### `suppliers` - Supplier information
10 pre-configured suppliers with contact information and business terms.

## 🏷️ Part Categories

| Category | Count | Examples |
|----------|-------|----------|
| **Fasteners** | 5,078 | Bolts, Screws, Nuts, Washers, Rivets |
| **Raw Materials** | 4,916 | Bars, Sheets, Plates, Tubes, Pipes |
| **Bearings** | 5,065 | Ball Bearings, Roller Bearings, Thrust Bearings |
| **Seals & Gaskets** | 5,064 | O-Rings, Oil Seals, Gaskets |
| **Electrical** | 4,950 | Connectors, Cables, Switches, Relays |
| **Hydraulic** | 5,037 | Cylinders, Pumps, Valves, Hoses |
| **Pneumatic** | 5,031 | Cylinders, Valves, Fittings, Tubing |
| **Tools** | 4,930 | Cutting Tools, Measuring Tools, Hand Tools |
| **Safety** | 4,984 | PPE, Safety Equipment, Emergency Equipment |
| **Mechanical** | 4,945 | Gears, Sprockets, Chains, Belts |

## 🔬 Materials

- **Steel**: A36, 1018, 1045, 4140, 4340, A572 Gr 50
- **Stainless Steel**: 304, 316, 316L, 321, 347, 410, 430, 17-4 PH
- **Aluminum**: 6061-T6, 6063-T5, 2024-T3, 7075-T6, 5052-H32, 1100-H14
- **Brass**: C360, C260, C464, C230
- **Bronze**: C932, C954, C630
- **Copper**: C101, C110, C145
- **Titanium**: Grade 2, Grade 5, Grade 7, Grade 9
- **Inconel**: 600, 625, 718, X-750
- **Hastelloy**: C-276, C-22, B-3
- **Plastic**: Nylon, Delrin, PTFE, PEEK, Polycarbonate, ABS

## 🔍 Search Capabilities

### 1. Direct Part Number Search
```python
part = db_manager.get_part_by_number("FASBO029477")
```

### 2. Full-Text Search
```python
results = db_manager.search_parts_full_text("stainless steel 304")
```

### 3. Description-Based Search
```python
results = db_manager.search_parts_by_description("bearing roller")
```

### 4. Category/Material Filtering
```python
results = db_manager.get_parts_by_category("Fasteners", "Bolts")
```

### 5. Advanced Multi-Strategy Search
```python
# Via LocalPartsCatalogService
results = await catalog.search_parts("1/4 inch stainless bolt")
```

## 🚀 Getting Started

### 1. Database Generation
If you need to regenerate the database:
```bash
cd backend
python generate_parts_database.py
```

### 2. Testing the Database
```bash
cd backend
python test_local_database.py
```

### 3. Using in Application
```python
from app.services.local_parts_catalog import LocalPartsCatalogService

catalog = LocalPartsCatalogService()
results = await catalog.search_parts("your search query")
```

## 📈 Performance

- **Search Performance**: < 30ms for typical queries
- **Full-Text Search**: FTS5 optimized for fast text searches
- **Indexing**: Multiple indexes for optimal query performance
- **Database Size**: ~45 MB for 50,000 parts
- **Memory Usage**: Minimal - SQLite loads only needed data

## 🔧 Agent Integration

The local database is fully integrated with the sales order system agents:

### SemanticSearchAgent
- Uses `LocalPartsCatalogService` for all part matching
- Supports multiple search strategies
- Provides confidence scoring and match explanations

### Search Strategies
1. **Direct part number matching**
2. **Full-text search across descriptions**
3. **Material and category filtering**
4. **Fuzzy matching for partial matches**
5. **Dimensional matching for specifications**

## 📊 Example Queries

### Simple Searches
```sql
-- Find all stainless steel parts
SELECT * FROM parts_catalog WHERE material LIKE '%Stainless Steel%';

-- Find parts by category
SELECT * FROM parts_catalog WHERE category = 'Fasteners';

-- Search by availability
SELECT * FROM parts_catalog WHERE availability_status = 'IN_STOCK';
```

### Advanced Searches
```sql
-- Full-text search
SELECT * FROM parts_catalog p
JOIN parts_search s ON p.part_number = s.part_number
WHERE parts_search MATCH 'aluminum bearing'
ORDER BY rank;

-- Dimensional search
SELECT * FROM parts_catalog 
WHERE diameter_inches = 0.25 AND length_inches BETWEEN 1.0 AND 2.0;

-- Price range with material filter
SELECT * FROM parts_catalog 
WHERE material LIKE '%Steel%' 
AND list_price BETWEEN 10.00 AND 100.00
ORDER BY list_price;
```

## 🛠️ Maintenance

### Database Health Check
```python
from app.database.connection import get_db_manager

db_manager = get_db_manager()
stats = db_manager.get_database_stats()
print(f"Total parts: {stats['total_parts']:,}")
```

### Adding New Parts
```python
# Parts can be added via the database manager
new_part_data = {
    "part_number": "NEW-PART-001",
    "description": "New Part Description",
    # ... other fields
}
db_manager.execute_insert(insert_query, part_data)
```

## 📝 Notes

- The database is designed for **local development** and testing
- All 50,000 parts are **unique** with realistic industrial data
- **Full-text search** is optimized for part descriptions and keywords
- **Multi-strategy search** provides the best matching results
- Database is **production-ready** for local deployments

## 🔗 Related Files

- `generate_parts_database.py` - Database generation script
- `database_schema.sql` - Complete database schema
- `app/database/connection.py` - Database connection utilities
- `app/services/local_parts_catalog.py` - Parts catalog service
- `test_local_database.py` - Database testing script
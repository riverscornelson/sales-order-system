-- Sales Order System - Parts Catalog Database Schema
-- SQLite Database for Local Development

-- Parts Catalog Table
CREATE TABLE IF NOT EXISTS parts_catalog (
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
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN DEFAULT 1,
    
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
    
    -- Additional attributes for search
    keywords TEXT,
    specifications TEXT,
    applications TEXT,
    notes TEXT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_parts_catalog_part_number ON parts_catalog(part_number);
CREATE INDEX IF NOT EXISTS idx_parts_catalog_category ON parts_catalog(category);
CREATE INDEX IF NOT EXISTS idx_parts_catalog_material ON parts_catalog(material);
CREATE INDEX IF NOT EXISTS idx_parts_catalog_availability ON parts_catalog(availability_status);
CREATE INDEX IF NOT EXISTS idx_parts_catalog_description ON parts_catalog(description);
CREATE INDEX IF NOT EXISTS idx_parts_catalog_active ON parts_catalog(active);

-- Full-text search index for descriptions and keywords
CREATE VIRTUAL TABLE IF NOT EXISTS parts_search USING fts5(
    part_number,
    description,
    keywords,
    specifications,
    content='parts_catalog'
);

-- Suppliers Table
CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    contact_email VARCHAR(200),
    contact_phone VARCHAR(50),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    country VARCHAR(100) DEFAULT 'USA',
    rating DECIMAL(3,2),
    payment_terms VARCHAR(100),
    lead_time_days INTEGER DEFAULT 30,
    active BOOLEAN DEFAULT 1,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customer Pricing Table (for future ERP integration)
CREATE TABLE IF NOT EXISTS customer_pricing (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id VARCHAR(50) NOT NULL,
    part_number VARCHAR(50) NOT NULL,
    price DECIMAL(12,2) NOT NULL,
    quantity_break INTEGER DEFAULT 1,
    effective_date DATE NOT NULL,
    expiry_date DATE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (part_number) REFERENCES parts_catalog(part_number)
);

-- Order Processing Sessions Table
CREATE TABLE IF NOT EXISTS processing_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    client_id VARCHAR(100),
    document_filename VARCHAR(500),
    document_type VARCHAR(20),
    status VARCHAR(50) DEFAULT 'PENDING',
    extracted_customer_info TEXT, -- JSON
    extracted_line_items TEXT,    -- JSON
    processing_results TEXT,      -- JSON
    error_messages TEXT,          -- JSON
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_date TIMESTAMP
);

-- Processed Orders Table
CREATE TABLE IF NOT EXISTS processed_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id VARCHAR(100) UNIQUE NOT NULL,
    session_id VARCHAR(100),
    customer_name VARCHAR(200),
    customer_email VARCHAR(200),
    customer_company VARCHAR(200),
    total_amount DECIMAL(12,2),
    line_item_count INTEGER,
    status VARCHAR(50) DEFAULT 'DRAFT',
    order_data TEXT, -- JSON
    submitted_to_erp BOOLEAN DEFAULT 0,
    erp_order_id VARCHAR(100),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    submitted_date TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES processing_sessions(session_id)
);

-- Insert initial suppliers
INSERT OR IGNORE INTO suppliers (supplier_id, name, contact_email, rating, payment_terms, lead_time_days) VALUES
('SUP001', 'Industrial Metals Corp', 'orders@industrialmetals.com', 4.8, 'Net 30', 5),
('SUP002', 'Precision Fasteners LLC', 'sales@precisionfasteners.com', 4.6, 'Net 15', 3),
('SUP003', 'Advanced Materials Inc', 'info@advancedmaterials.com', 4.9, 'Net 30', 7),
('SUP004', 'Stainless Solutions', 'orders@stainlesssolutions.com', 4.7, 'Net 30', 4),
('SUP005', 'Alloy Specialists', 'sales@alloyspecialists.com', 4.5, 'Net 30', 10),
('SUP006', 'High Performance Metals', 'orders@hpmetals.com', 4.8, 'Net 30', 6),
('SUP007', 'Custom Fabrication Works', 'info@customfab.com', 4.4, 'Net 30', 14),
('SUP008', 'Quality Hardware Supply', 'orders@qualityhardware.com', 4.6, 'Net 15', 2),
('SUP009', 'Aerospace Grade Materials', 'sales@aerospacegrade.com', 4.9, 'Net 30', 8),
('SUP010', 'Marine Metal Works', 'orders@marinemetals.com', 4.7, 'Net 30', 5);
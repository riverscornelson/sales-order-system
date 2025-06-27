"""
Database connection utilities for local SQLite database
"""

import sqlite3
import os
from contextlib import contextmanager
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Database path relative to backend directory
DB_PATH = Path(__file__).parent.parent.parent / "parts_catalog.db"

class DatabaseManager:
    """Manages SQLite database connections and operations"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(DB_PATH)
        
        if not os.path.exists(self.db_path):
            logger.warning(f"Database not found at {self.db_path}")
            raise FileNotFoundError(f"Parts catalog database not found. Please run generate_parts_database.py first.")
    
    @contextmanager
    def get_connection(self):
        """Get a database connection with proper cleanup"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results as list of dicts"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Convert rows to dictionaries
            columns = [description[0] for description in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
    
    def execute_insert(self, query: str, params: tuple = None) -> int:
        """Execute an INSERT query and return the last row ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.lastrowid
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Execute an UPDATE query and return the number of affected rows"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.rowcount
    
    def search_parts_full_text(self, search_term: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Perform full-text search on parts"""
        query = """
        SELECT p.* FROM parts_catalog p
        JOIN parts_search s ON p.part_number = s.part_number
        WHERE parts_search MATCH ?
        ORDER BY rank
        LIMIT ?
        """
        return self.execute_query(query, (search_term, limit))
    
    def get_parts_by_category(self, category: str, subcategory: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get parts by category and optional subcategory"""
        if subcategory:
            query = """
            SELECT * FROM parts_catalog 
            WHERE category = ? AND subcategory = ? AND active = 1
            ORDER BY part_number
            LIMIT ?
            """
            return self.execute_query(query, (category, subcategory, limit))
        else:
            query = """
            SELECT * FROM parts_catalog 
            WHERE category = ? AND active = 1
            ORDER BY part_number
            LIMIT ?
            """
            return self.execute_query(query, (category, limit))
    
    def get_part_by_number(self, part_number: str) -> Optional[Dict[str, Any]]:
        """Get a specific part by part number"""
        query = "SELECT * FROM parts_catalog WHERE part_number = ? AND active = 1"
        results = self.execute_query(query, (part_number,))
        return results[0] if results else None
    
    def search_parts_by_description(self, description: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search parts by description using LIKE"""
        query = """
        SELECT * FROM parts_catalog 
        WHERE description LIKE ? AND active = 1
        ORDER BY 
            CASE 
                WHEN description LIKE ? THEN 1
                WHEN description LIKE ? THEN 2
                ELSE 3
            END,
            list_price ASC
        LIMIT ?
        """
        search_term = f"%{description}%"
        exact_start = f"{description}%"
        exact_words = f"% {description} %"
        
        return self.execute_query(query, (search_term, exact_start, exact_words, limit))
    
    def get_materials(self) -> List[str]:
        """Get all unique materials"""
        query = "SELECT DISTINCT material FROM parts_catalog WHERE material IS NOT NULL ORDER BY material"
        results = self.execute_query(query)
        return [row['material'] for row in results]
    
    def get_categories(self) -> List[Dict[str, Any]]:
        """Get all categories with part counts"""
        query = """
        SELECT category, COUNT(*) as part_count
        FROM parts_catalog 
        WHERE active = 1
        GROUP BY category
        ORDER BY category
        """
        return self.execute_query(query)
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats = {}
        
        # Total parts
        total_query = "SELECT COUNT(*) as total FROM parts_catalog WHERE active = 1"
        stats['total_parts'] = self.execute_query(total_query)[0]['total']
        
        # Parts by availability
        availability_query = """
        SELECT availability_status, COUNT(*) as count
        FROM parts_catalog 
        WHERE active = 1
        GROUP BY availability_status
        ORDER BY count DESC
        """
        stats['availability'] = self.execute_query(availability_query)
        
        # Average price ranges
        price_query = """
        SELECT 
            MIN(list_price) as min_price,
            MAX(list_price) as max_price,
            AVG(list_price) as avg_price,
            COUNT(*) as total_with_price
        FROM parts_catalog 
        WHERE active = 1 AND list_price > 0
        """
        stats['pricing'] = self.execute_query(price_query)[0]
        
        # Category breakdown
        stats['categories'] = self.get_categories()
        
        return stats

# Global database manager instance
db_manager = DatabaseManager()

def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance"""
    return db_manager
"""
Enhanced database connection manager with better security and connection management
"""

import sqlite3
import os
import threading
from contextlib import contextmanager
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import logging
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """Type-safe query result wrapper"""
    rows: List[Dict[str, Any]]
    row_count: int
    execution_time: float


class SecureDatabaseManager:
    """Enhanced database manager with security features and connection management"""
    
    # SQL injection protection: whitelist allowed table/column names
    ALLOWED_TABLES = {'parts_catalog', 'parts_search'}
    ALLOWED_COLUMNS = {
        'parts_catalog': {
            'id', 'part_number', 'description', 'category', 'subcategory', 
            'material', 'manufacturer', 'supplier', 'list_price', 'unit_price',
            'availability_status', 'stock_quantity', 'lead_time_days', 'active',
            'created_at', 'updated_at', 'dimensions', 'weight', 'specifications'
        }
    }
    
    def __init__(self, db_path: Optional[str] = None, max_connections: int = 10):
        self.db_path = db_path or str(Path(__file__).parent.parent.parent / "parts_catalog.db")
        self.max_connections = max_connections
        self._connection_pool = []
        self._pool_lock = threading.Lock()
        self._validate_database()
    
    def _validate_database(self):
        """Validate database exists and is accessible"""
        if not os.path.exists(self.db_path):
            logger.warning(f"Database not found at {self.db_path}")
            raise FileNotFoundError(
                f"Parts catalog database not found at {self.db_path}. "
                "Please run generate_parts_database.py first."
            )
        
        # Test connection
        try:
            with self._get_raw_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]
                logger.info(f"Database validated: {table_count} tables found")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to database: {e}")
    
    @contextmanager
    def _get_raw_connection(self):
        """Get a raw SQLite connection with security settings"""
        conn = None
        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=30.0,  # 30 second timeout
                check_same_thread=False,
                isolation_level='DEFERRED'  # Better concurrency
            )
            conn.row_factory = sqlite3.Row
            
            # Security settings
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")  # Better concurrency
            conn.execute("PRAGMA synchronous = NORMAL")  # Good balance of safety/performance
            conn.execute("PRAGMA temp_store = MEMORY")  # Faster temporary operations
            conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
            
            yield conn
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_connection(self):
        """Get a database connection from the pool"""
        with self._get_raw_connection() as conn:
            yield conn
    
    def _validate_query_params(self, table_name: str, columns: List[str] = None) -> None:
        """Validate table and column names to prevent SQL injection"""
        if table_name not in self.ALLOWED_TABLES:
            raise ValueError(f"Table '{table_name}' not allowed")
        
        if columns:
            allowed_cols = self.ALLOWED_COLUMNS.get(table_name, set())
            for col in columns:
                if col not in allowed_cols:
                    raise ValueError(f"Column '{col}' not allowed for table '{table_name}'")
    
    def execute_query(self, query: str, params: Union[tuple, dict] = None, 
                     validate_table: str = None) -> QueryResult:
        """Execute a SELECT query with security validation"""
        start_time = time.time()
        
        # Basic SQL injection protection
        if validate_table:
            self._validate_query_params(validate_table)
        
        # Check for dangerous SQL keywords
        dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 'UPDATE']
        query_upper = query.upper()
        for keyword in dangerous_keywords:
            if keyword in query_upper and not query_upper.strip().startswith('SELECT'):
                raise ValueError(f"Query contains dangerous keyword: {keyword}")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # Convert rows to dictionaries
                columns = [description[0] for description in cursor.description] if cursor.description else []
                rows = []
                for row in cursor.fetchall():
                    rows.append(dict(zip(columns, row)))
                
                execution_time = time.time() - start_time
                
                return QueryResult(
                    rows=rows,
                    row_count=len(rows),
                    execution_time=execution_time
                )
                
            except sqlite3.Error as e:
                logger.error(f"SQL error: {e}, Query: {query[:100]}...")
                raise
    
    def execute_safe_search(self, search_term: str, table: str = 'parts_catalog', 
                           columns: List[str] = None, limit: int = 50) -> QueryResult:
        """Execute a safe search query with parameterized inputs"""
        self._validate_query_params(table, columns)
        
        # Sanitize search term
        if not isinstance(search_term, str):
            raise ValueError("Search term must be a string")
        
        # Limit search term length
        if len(search_term) > 200:
            raise ValueError("Search term too long")
        
        # Build safe query
        select_cols = ', '.join(columns) if columns else '*'
        query = f"""
        SELECT {select_cols} 
        FROM {table} 
        WHERE description LIKE ? AND active = 1
        ORDER BY list_price ASC
        LIMIT ?
        """
        
        search_param = f"%{search_term}%"
        return self.execute_query(query, (search_param, limit), validate_table=table)
    
    def get_part_by_number_safe(self, part_number: str) -> Optional[Dict[str, Any]]:
        """Safely get a part by part number"""
        if not isinstance(part_number, str) or len(part_number) > 50:
            raise ValueError("Invalid part number")
        
        # Remove any potentially dangerous characters
        safe_part_number = ''.join(c for c in part_number if c.isalnum() or c in '-_.')
        
        query = "SELECT * FROM parts_catalog WHERE part_number = ? AND active = 1"
        result = self.execute_query(query, (safe_part_number,), validate_table='parts_catalog')
        
        return result.rows[0] if result.rows else None
    
    def search_parts_full_text_safe(self, search_term: str, limit: int = 50) -> QueryResult:
        """Perform safe full-text search"""
        if not isinstance(search_term, str) or len(search_term) > 200:
            raise ValueError("Invalid search term")
        
        # Escape FTS special characters
        safe_term = search_term.replace('"', '""').replace("'", "''")
        
        query = """
        SELECT p.* FROM parts_catalog p
        JOIN parts_search s ON p.part_number = s.part_number
        WHERE parts_search MATCH ?
        ORDER BY rank
        LIMIT ?
        """
        
        return self.execute_query(query, (safe_term, limit), validate_table='parts_catalog')
    
    def get_database_health(self) -> Dict[str, Any]:
        """Get database health and performance metrics"""
        health = {}
        
        try:
            # Basic connectivity
            result = self.execute_query("SELECT 1 as health_check")
            health['connectivity'] = 'OK' if result.rows else 'FAILED'
            
            # Database size
            size_result = self.execute_query("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            health['database_size_bytes'] = size_result.rows[0]['size'] if size_result.rows else 0
            
            # Table counts
            tables_result = self.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
            health['table_count'] = len(tables_result.rows)
            
            # Parts count
            parts_result = self.execute_query("SELECT COUNT(*) as count FROM parts_catalog WHERE active = 1")
            health['active_parts_count'] = parts_result.rows[0]['count'] if parts_result.rows else 0
            
            # Performance check
            start_time = time.time()
            self.execute_query("SELECT * FROM parts_catalog LIMIT 1")
            health['query_response_time_ms'] = (time.time() - start_time) * 1000
            
            health['status'] = 'healthy'
            
        except Exception as e:
            health['status'] = 'unhealthy'
            health['error'] = str(e)
            
        return health


# Global secure database manager instance
secure_db_manager = SecureDatabaseManager()

def get_secure_db_manager() -> SecureDatabaseManager:
    """Get the global secure database manager instance"""
    return secure_db_manager
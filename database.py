import sqlite3
import logging
from datetime import datetime
from typing import Optional, List, Dict

logger = logging.getLogger("inventory-db")


class InventoryDB:
    """SQLite database for managing inventory and sales."""
    
    def __init__(self, db_path: str = "inventory.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Products table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                price REAL NOT NULL,
                stock INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Sales table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer TEXT NOT NULL,
                product TEXT NOT NULL,
                amount REAL NOT NULL,
                payment_status TEXT DEFAULT 'pending',
                delivery_status TEXT DEFAULT 'pending',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Inquiries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inquiries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Database initialized: %s", self.db_path)
    
    def add_product(self, name: str, price: float, stock: int) -> bool:
        """Add a new product."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
                (name, price, stock)
            )
            conn.commit()
            conn.close()
            logger.info(f"Added product: {name}")
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"Product already exists: {name}")
            return False
    
    def get_product(self, name: str) -> Optional[Dict]:
        """Get product by name."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE name = ?", (name,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def list_products(self) -> List[Dict]:
        """List all products."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE stock > 0")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def update_stock(self, name: str, new_stock: int) -> bool:
        """Update product stock."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE products SET stock = ? WHERE name = ?", (new_stock, name))
            conn.commit()
            conn.close()
            logger.info(f"Updated stock for {name}: {new_stock}")
            return cursor.rowcount > 0
        except Exception as exc:
            logger.exception("Error updating stock: %s", exc)
            return False
    
    def log_sale(self, customer: str, product: str, amount: float, notes: str = "") -> int:
        """Log a sale."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sales (customer, product, amount, notes) VALUES (?, ?, ?, ?)",
            (customer, product, amount, notes)
        )
        conn.commit()
        sale_id = cursor.lastrowid
        conn.close()
        logger.info(f"Sale logged: {customer} - {product} (${amount})")
        return sale_id
    
    def get_sales(self, limit: int = 10) -> List[Dict]:
        """Get recent sales."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM sales ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def log_inquiry(self, customer: str, message: str) -> None:
        """Log customer inquiry."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO inquiries (customer, message) VALUES (?, ?)",
            (customer, message)
        )
        conn.commit()
        conn.close()

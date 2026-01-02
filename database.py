"""
database.py - Database Module for Budget Tracker
=================================================

PYTHON CONCEPT: Modules
-----------------------
A module is just a .py file that contains code (functions, variables, classes).
We can import and reuse this code in other files using: 
    from database import get_connection

PYTHON CONCEPT: Docstrings
--------------------------
This text between triple quotes is called a "docstring". It documents what
the module/function does. You can see it by typing help(database) in Python.

DATABASE CONCEPT: SQLite
------------------------
SQLite is a lightweight database that stores everything in a single file.
Perfect for local apps like ours! No server setup needed.
"""

import sqlite3  # Built into Python - no install needed!
import shutil   # For file operations like copying
from datetime import datetime
from pathlib import Path

# PYTHON CONCEPT: Constants
# -------------------------
# By convention, we use UPPERCASE for values that shouldn't change.
# This is the path to our database file.
DATABASE_PATH = Path(__file__).parent / "budget_tracker.db"
BACKUP_DIR = Path(__file__).parent / "backups"
MAX_BACKUPS = 30  # Keep last 30 backups (about 1 month of daily backups)


# =============================================================================
# BACKUP OPERATIONS
# =============================================================================
# PYTHON CONCEPT: File Operations
# --------------------------------
# Python's shutil module provides high-level file operations like copying.
# pathlib.Path makes working with file paths easy and cross-platform.

def create_backup() -> str:
    """
    Create a timestamped backup of the database.
    
    PYTHON CONCEPT: shutil.copy2()
    ------------------------------
    copy2() copies a file AND preserves metadata (timestamps, permissions).
    Regular copy() only copies the content.
    
    Returns:
        str: Path to the backup file, or None if database doesn't exist
    """
    # Don't backup if database doesn't exist yet
    if not DATABASE_PATH.exists():
        return None
    
    # Create backups directory if it doesn't exist
    # PYTHON CONCEPT: mkdir with parents=True
    # Creates parent directories too, like 'mkdir -p' in terminal
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create filename with timestamp
    # PYTHON CONCEPT: strftime() - String Format Time
    # %Y=year, %m=month, %d=day, %H=hour, %M=minute, %S=second
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"budget_tracker_backup_{timestamp}.db"
    backup_path = BACKUP_DIR / backup_filename
    
    # Copy the database file
    shutil.copy2(DATABASE_PATH, backup_path)
    
    # Clean up old backups
    _cleanup_old_backups()
    
    return str(backup_path)


def _cleanup_old_backups():
    """
    Remove old backups, keeping only the most recent MAX_BACKUPS.
    
    PYTHON CONCEPT: Sorting with key function
    -----------------------------------------
    sorted() can take a 'key' function that extracts a comparison value.
    Here we sort files by modification time (oldest first).
    """
    if not BACKUP_DIR.exists():
        return
    
    # Get all backup files
    # PYTHON CONCEPT: glob() - Pattern matching for files
    # *.db matches all files ending in .db
    backups = list(BACKUP_DIR.glob("budget_tracker_backup_*.db"))
    
    # Sort by modification time (oldest first)
    # PYTHON CONCEPT: lambda functions
    # A lambda is a small anonymous function: lambda x: x.stat().st_mtime
    # Same as: def get_mtime(x): return x.stat().st_mtime
    backups.sort(key=lambda f: f.stat().st_mtime)
    
    # Delete oldest backups if we have too many
    while len(backups) > MAX_BACKUPS:
        oldest = backups.pop(0)  # Remove and get the first (oldest)
        oldest.unlink()  # Delete the file
        print(f"Deleted old backup: {oldest.name}")


def get_all_backups() -> list:
    """
    Get a list of all backup files with their info.
    
    Returns:
        List of dicts with backup info (filename, path, date, size)
    """
    if not BACKUP_DIR.exists():
        return []
    
    backups = []
    for backup_file in sorted(BACKUP_DIR.glob("budget_tracker_backup_*.db"), 
                               key=lambda f: f.stat().st_mtime, reverse=True):
        stat = backup_file.stat()
        backups.append({
            "filename": backup_file.name,
            "path": str(backup_file),
            "date": datetime.fromtimestamp(stat.st_mtime),
            "size_kb": stat.st_size / 1024  # Convert bytes to KB
        })
    
    return backups


def restore_from_backup(backup_path: str) -> bool:
    """
    Restore database from a backup file.
    
    WARNING: This replaces all current data!
    
    Args:
        backup_path: Path to the backup file to restore
        
    Returns:
        True if successful, False otherwise
    """
    backup_file = Path(backup_path)
    
    if not backup_file.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")
    
    # Create a backup of current data before restoring (safety net!)
    current_backup = create_backup()
    if current_backup:
        print(f"Created safety backup before restore: {current_backup}")
    
    # Copy backup over the current database
    shutil.copy2(backup_file, DATABASE_PATH)
    
    return True


def get_database_info() -> dict:
    """
    Get information about the current database.
    
    Returns:
        Dict with database stats (size, last modified, record counts)
    """
    info = {
        "exists": DATABASE_PATH.exists(),
        "path": str(DATABASE_PATH),
        "size_kb": 0,
        "last_modified": None,
        "transaction_count": 0,
        "user_count": 0
    }
    
    if DATABASE_PATH.exists():
        stat = DATABASE_PATH.stat()
        info["size_kb"] = stat.st_size / 1024
        info["last_modified"] = datetime.fromtimestamp(stat.st_mtime)
        
        # Get record counts
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM transactions")
            info["transaction_count"] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM users")
            info["user_count"] = cursor.fetchone()[0]
            conn.close()
        except:
            pass  # Database might not be initialized yet
    
    return info


def get_connection():
    """
    Create and return a connection to our SQLite database.
    
    PYTHON CONCEPT: Functions
    -------------------------
    Functions are reusable blocks of code. We define them with 'def'.
    This function takes no parameters and returns a database connection.
    
    Returns:
        sqlite3.Connection: A connection object to interact with the database
    """
    conn = sqlite3.connect(DATABASE_PATH)
    
    # This makes our query results accessible by column name (not just index)
    # Instead of row[0], we can use row['name'] - much clearer!
    conn.row_factory = sqlite3.Row
    
    return conn


def init_database():
    """
    Initialize the database with our tables.
    
    DATABASE CONCEPT: Tables
    ------------------------
    Think of tables like spreadsheets:
    - Each table stores one type of data (users, expenses, etc.)
    - Each row is one record (one expense, one user)
    - Each column is one piece of information (amount, date, category)
    
    SQL CONCEPT: CREATE TABLE
    -------------------------
    SQL (Structured Query Language) is how we talk to databases.
    CREATE TABLE defines the structure of our data.
    """
    conn = get_connection()
    cursor = conn.cursor()  # A cursor lets us execute SQL commands
    
    # =========================================================================
    # TABLE 1: USERS (you and your wife)
    # =========================================================================
    # Each person who uses the app gets a row here
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # SQL BREAKDOWN:
    # - id: Unique identifier, auto-increments (1, 2, 3...)
    # - name: The person's name, TEXT type, NOT NULL means required
    # - UNIQUE: No two users can have the same name
    # - created_at: Automatically set to current time when row is created
    
    # =========================================================================
    # TABLE 2: CATEGORIES (how we organize expenses)
    # =========================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            category_type TEXT NOT NULL CHECK(category_type IN ('expense', 'income', 'savings', 'debt'))
        )
    """)
    # CHECK constraint ensures category_type is one of the valid options
    
    # =========================================================================
    # TABLE 3: TRANSACTIONS (expenses, income, savings, debt payments)
    # =========================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            transaction_type TEXT NOT NULL CHECK(transaction_type IN ('expense', 'income', 'savings', 'debt_payment')),
            transaction_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    """)
    # SQL CONCEPT: FOREIGN KEY
    # ------------------------
    # Links this table to users and categories tables.
    # user_id must match an id in the users table.
    # This creates relationships between our data!
    
    # =========================================================================
    # TABLE 4: SAVINGS GOALS (what you're saving for)
    # =========================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS savings_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            target_amount REAL NOT NULL,
            current_amount REAL DEFAULT 0,
            target_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # =========================================================================
    # TABLE 5: DEBTS (loans, credit cards, etc.)
    # =========================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            original_amount REAL NOT NULL,
            current_balance REAL NOT NULL,
            interest_rate REAL DEFAULT 0,
            minimum_payment REAL DEFAULT 0,
            due_date INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # due_date is an integer 1-31 for day of month
    
    # =========================================================================
    # TABLE 6: BUDGETS (monthly spending limits per category)
    # =========================================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            monthly_limit REAL NOT NULL,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    """)
    
    # PYTHON CONCEPT: commit()
    # ------------------------
    # Changes aren't saved until we commit! This is for data safety.
    # If something goes wrong, uncommitted changes are rolled back.
    conn.commit()
    conn.close()
    
    # Add default categories if they don't exist
    _seed_default_categories()
    
    print("✓ Database initialized successfully!")


def _seed_default_categories():
    """
    Add default expense categories.
    
    PYTHON CONCEPT: Private Functions
    ---------------------------------
    Functions starting with _ are "private" by convention.
    This means they're meant to be used only inside this module,
    not imported by other files.
    """
    default_categories = [
        # Expense categories
        ("Groceries", "expense"),
        ("Dining Out", "expense"),
        ("Transportation", "expense"),
        ("Utilities", "expense"),
        ("Entertainment", "expense"),
        ("Shopping", "expense"),
        ("Healthcare", "expense"),
        ("Personal Care", "expense"),
        ("Subscriptions", "expense"),
        ("Other", "expense"),
        # Income categories
        ("Salary", "income"),
        ("Side Income", "income"),
        ("Gifts", "income"),
        # Savings categories
        ("Emergency Fund", "savings"),
        ("Retirement", "savings"),
        ("Vacation", "savings"),
        ("General Savings", "savings"),
        # Debt categories
        ("Credit Card", "debt"),
        ("Student Loan", "debt"),
        ("Car Loan", "debt"),
        ("Mortgage", "debt"),
        ("Personal Loan", "debt"),
    ]
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # PYTHON CONCEPT: for loop with tuple unpacking
    # ---------------------------------------------
    # Each item in default_categories is a tuple like ("Groceries", "expense")
    # We can "unpack" it directly into name and category_type variables!
    for name, category_type in default_categories:
        try:
            cursor.execute(
                "INSERT INTO categories (name, category_type) VALUES (?, ?)",
                (name, category_type)
            )
        except sqlite3.IntegrityError:
            # Category already exists (UNIQUE constraint), skip it
            pass
    
    conn.commit()
    conn.close()


# =============================================================================
# USER OPERATIONS
# =============================================================================

def add_user(name: str) -> int:
    """
    Add a new user to the database.
    
    PYTHON CONCEPT: Type Hints
    --------------------------
    name: str means 'name should be a string'
    -> int means 'this function returns an integer'
    Type hints don't enforce types, but help with documentation and IDE support.
    
    Args:
        name: The user's name
        
    Returns:
        The ID of the newly created user
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (name) VALUES (?)", (name,))
    conn.commit()
    user_id = cursor.lastrowid  # Get the auto-generated ID
    conn.close()
    return user_id


def get_all_users() -> list:
    """
    Get all users from the database.
    
    Returns:
        A list of all users (as Row objects that work like dictionaries)
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users ORDER BY name")
    users = cursor.fetchall()  # Get all results
    conn.close()
    return users


# =============================================================================
# CATEGORY OPERATIONS
# =============================================================================

def get_categories_by_type(category_type: str) -> list:
    """
    Get all categories of a specific type.
    
    Args:
        category_type: One of 'expense', 'income', 'savings', 'debt'
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM categories WHERE category_type = ? ORDER BY name",
        (category_type,)
    )
    categories = cursor.fetchall()
    conn.close()
    return categories


# =============================================================================
# TRANSACTION OPERATIONS
# =============================================================================

def add_transaction(user_id: int, category_id: int, amount: float, 
                   description: str, transaction_type: str, 
                   transaction_date: str) -> int:
    """
    Add a new transaction (expense, income, savings, or debt payment).
    
    PYTHON CONCEPT: Multiple Parameters
    -----------------------------------
    Functions can have many parameters. When calling, you can use:
    - Positional: add_transaction(1, 2, 50.00, "Lunch", "expense", "2024-01-15")
    - Keyword: add_transaction(user_id=1, amount=50.00, ...)
    Keyword arguments are clearer for functions with many parameters!
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transactions 
        (user_id, category_id, amount, description, transaction_type, transaction_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, category_id, amount, description, transaction_type, transaction_date))
    conn.commit()
    transaction_id = cursor.lastrowid
    conn.close()
    return transaction_id


def get_transactions(user_id: int = None, transaction_type: str = None,
                    start_date: str = None, end_date: str = None) -> list:
    """
    Get transactions with optional filters.
    
    PYTHON CONCEPT: Default Parameters
    -----------------------------------
    Parameters with = None are optional. If not provided, they default to None.
    This lets us build flexible queries with optional filters.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # PYTHON CONCEPT: Building Dynamic SQL
    # ------------------------------------
    # We start with a base query and add conditions as needed
    query = """
        SELECT t.*, u.name as user_name, c.name as category_name 
        FROM transactions t
        JOIN users u ON t.user_id = u.id
        JOIN categories c ON t.category_id = c.id
        WHERE 1=1
    """
    # "WHERE 1=1" is a trick! It's always true, so we can just keep adding "AND ..."
    
    params = []  # Parameters for our query (prevents SQL injection!)
    
    if user_id:
        query += " AND t.user_id = ?"
        params.append(user_id)
    
    if transaction_type:
        query += " AND t.transaction_type = ?"
        params.append(transaction_type)
    
    if start_date:
        query += " AND t.transaction_date >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND t.transaction_date <= ?"
        params.append(end_date)
    
    query += " ORDER BY t.transaction_date DESC"
    
    cursor.execute(query, params)
    transactions = cursor.fetchall()
    conn.close()
    return transactions


def get_monthly_summary(year: int, month: int) -> dict:
    """
    Get a summary of spending/income for a specific month.
    
    Returns a dictionary with totals by user and category.
    
    PYTHON CONCEPT: Dictionaries
    ----------------------------
    Dictionaries store key-value pairs: {"name": "John", "age": 30}
    Perfect for structured data like our summary!
    """
    # Format: 2024-01 for January 2024
    month_str = f"{year}-{month:02d}"  # :02d pads with zeros (1 -> 01)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get totals by user and transaction type
    cursor.execute("""
        SELECT 
            u.name as user_name,
            t.transaction_type,
            SUM(t.amount) as total
        FROM transactions t
        JOIN users u ON t.user_id = u.id
        WHERE strftime('%Y-%m', t.transaction_date) = ?
        GROUP BY u.name, t.transaction_type
    """, (month_str,))
    
    by_user = cursor.fetchall()
    
    # Get totals by category
    cursor.execute("""
        SELECT 
            c.name as category_name,
            t.transaction_type,
            SUM(t.amount) as total
        FROM transactions t
        JOIN categories c ON t.category_id = c.id
        WHERE strftime('%Y-%m', t.transaction_date) = ?
        GROUP BY c.name, t.transaction_type
        ORDER BY total DESC
    """, (month_str,))
    
    by_category = cursor.fetchall()
    
    conn.close()
    
    return {
        "by_user": by_user,
        "by_category": by_category,
        "month": month_str
    }


# =============================================================================
# DEBT OPERATIONS
# =============================================================================

def add_debt(name: str, original_amount: float, current_balance: float,
            interest_rate: float = 0, minimum_payment: float = 0,
            due_date: int = None) -> int:
    """Add a new debt to track."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO debts 
        (name, original_amount, current_balance, interest_rate, minimum_payment, due_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, original_amount, current_balance, interest_rate, minimum_payment, due_date))
    conn.commit()
    debt_id = cursor.lastrowid
    conn.close()
    return debt_id


def get_all_debts() -> list:
    """Get all debts."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM debts ORDER BY current_balance DESC")
    debts = cursor.fetchall()
    conn.close()
    return debts


def update_debt_balance(debt_id: int, new_balance: float):
    """Update a debt's current balance."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE debts SET current_balance = ? WHERE id = ?",
        (new_balance, debt_id)
    )
    conn.commit()
    conn.close()


# =============================================================================
# SAVINGS GOAL OPERATIONS
# =============================================================================

def add_savings_goal(name: str, target_amount: float, 
                    target_date: str = None) -> int:
    """Add a new savings goal."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO savings_goals (name, target_amount, target_date)
        VALUES (?, ?, ?)
    """, (name, target_amount, target_date))
    conn.commit()
    goal_id = cursor.lastrowid
    conn.close()
    return goal_id


def get_all_savings_goals() -> list:
    """Get all savings goals."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM savings_goals ORDER BY target_date")
    goals = cursor.fetchall()
    conn.close()
    return goals


def update_savings_goal_amount(goal_id: int, new_amount: float):
    """Update a savings goal's current amount."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE savings_goals SET current_amount = ? WHERE id = ?",
        (new_amount, goal_id)
    )
    conn.commit()
    conn.close()


# =============================================================================
# UPDATE & DELETE OPERATIONS
# =============================================================================
# PYTHON CONCEPT: CRUD Operations
# --------------------------------
# CRUD stands for Create, Read, Update, Delete - the four basic operations
# for persistent storage. We already have Create (add_*) and Read (get_*).
# Now let's add Update and Delete!

def update_transaction(transaction_id: int, user_id: int = None, 
                       category_id: int = None, amount: float = None,
                       description: str = None, transaction_date: str = None):
    """
    Update an existing transaction.
    
    PYTHON CONCEPT: Optional Updates
    ---------------------------------
    We only update fields that are provided (not None).
    This lets us update just one field without touching others.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Build the UPDATE query dynamically
    # PYTHON CONCEPT: List building with conditions
    updates = []
    params = []
    
    if user_id is not None:
        updates.append("user_id = ?")
        params.append(user_id)
    
    if category_id is not None:
        updates.append("category_id = ?")
        params.append(category_id)
    
    if amount is not None:
        updates.append("amount = ?")
        params.append(amount)
    
    if description is not None:
        updates.append("description = ?")
        params.append(description)
    
    if transaction_date is not None:
        updates.append("transaction_date = ?")
        params.append(transaction_date)
    
    if updates:  # Only run if there's something to update
        # PYTHON CONCEPT: str.join()
        # Joins list items with a separator: ["a", "b"] -> "a, b"
        query = f"UPDATE transactions SET {', '.join(updates)} WHERE id = ?"
        params.append(transaction_id)
        cursor.execute(query, params)
        conn.commit()
    
    conn.close()


def delete_transaction(transaction_id: int):
    """
    Delete a transaction by ID.
    
    SQL CONCEPT: DELETE
    -------------------
    DELETE FROM table WHERE condition
    Be careful! Without WHERE, it deletes ALL rows!
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    conn.commit()
    conn.close()


def get_transaction_by_id(transaction_id: int):
    """Get a single transaction by its ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.*, u.name as user_name, c.name as category_name 
        FROM transactions t
        JOIN users u ON t.user_id = u.id
        JOIN categories c ON t.category_id = c.id
        WHERE t.id = ?
    """, (transaction_id,))
    transaction = cursor.fetchone()
    conn.close()
    return transaction


def delete_debt(debt_id: int):
    """Delete a debt by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM debts WHERE id = ?", (debt_id,))
    conn.commit()
    conn.close()


def update_debt(debt_id: int, name: str = None, current_balance: float = None,
               interest_rate: float = None, minimum_payment: float = None):
    """Update debt details."""
    conn = get_connection()
    cursor = conn.cursor()
    
    updates = []
    params = []
    
    if name is not None:
        updates.append("name = ?")
        params.append(name)
    
    if current_balance is not None:
        updates.append("current_balance = ?")
        params.append(current_balance)
    
    if interest_rate is not None:
        updates.append("interest_rate = ?")
        params.append(interest_rate)
    
    if minimum_payment is not None:
        updates.append("minimum_payment = ?")
        params.append(minimum_payment)
    
    if updates:
        query = f"UPDATE debts SET {', '.join(updates)} WHERE id = ?"
        params.append(debt_id)
        cursor.execute(query, params)
        conn.commit()
    
    conn.close()


def delete_savings_goal(goal_id: int):
    """Delete a savings goal by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM savings_goals WHERE id = ?", (goal_id,))
    conn.commit()
    conn.close()


def update_savings_goal(goal_id: int, name: str = None, target_amount: float = None,
                       current_amount: float = None, target_date: str = None):
    """Update savings goal details."""
    conn = get_connection()
    cursor = conn.cursor()
    
    updates = []
    params = []
    
    if name is not None:
        updates.append("name = ?")
        params.append(name)
    
    if target_amount is not None:
        updates.append("target_amount = ?")
        params.append(target_amount)
    
    if current_amount is not None:
        updates.append("current_amount = ?")
        params.append(current_amount)
    
    if target_date is not None:
        updates.append("target_date = ?")
        params.append(target_date)
    
    if updates:
        query = f"UPDATE savings_goals SET {', '.join(updates)} WHERE id = ?"
        params.append(goal_id)
        cursor.execute(query, params)
        conn.commit()
    
    conn.close()


def delete_user(user_id: int):
    """
    Delete a user by ID.
    
    WARNING: This will fail if the user has transactions!
    In a real app, you might want to either:
    1. Delete all their transactions first (cascade delete)
    2. Prevent deletion if they have data
    3. Mark as inactive instead of deleting
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if user has transactions
    cursor.execute("SELECT COUNT(*) FROM transactions WHERE user_id = ?", (user_id,))
    count = cursor.fetchone()[0]
    
    if count > 0:
        conn.close()
        raise ValueError(f"Cannot delete user: they have {count} transactions. Delete transactions first.")
    
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


# =============================================================================
# MAIN - Run this file directly to initialize the database
# =============================================================================

if __name__ == "__main__":
    """
    PYTHON CONCEPT: if __name__ == "__main__"
    -----------------------------------------
    This code only runs when you execute this file directly:
        python database.py
    
    It does NOT run when you import this module:
        from database import get_connection
    
    This is perfect for testing or one-time setup!
    """
    print("Initializing Budget Tracker Database...")
    init_database()
    print("\nDatabase is ready! You can now run the main app.")


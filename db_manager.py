import sqlite3

DB_NAME = 'app.db'

def get_connection():
    """
    Establishes a connection to the SQLite database.
    Returns:
        conn (sqlite3.Connection): The connection object to the database.
    """
    conn = sqlite3.connect(DB_NAME)
    return conn

def init_db():
    """
    Initializes the database by creating necessary tables if they do not exist.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Create Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    );
    ''')

    # Create Search History table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS search_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        query TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    ''')

    # Create User Interactions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_interactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        paper_id TEXT NOT NULL,
        action TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    ''')

    # Create Cached Results table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cached_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT UNIQUE NOT NULL,
        results TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    ''')

    conn.commit()
    conn.close()
# import sqlite3 to interact with SQLite databases
# sqlite3 is a lightweight database stored in a single file
import sqlite3

# # os is used for file paths and directories
import os

# --- Database Path Setup ---
# __file__ is the path to this script (database.py)
# os.path.abspath(__file__) gives the full path to this file
# os.path.dirname(...) removes the filename, leaving the directory path
# BASE_DIR now points to the backend folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Move up one level to .../ (project root), then add "database/inventory.db"
DB_PATH = os.path.join(BASE_DIR, "..", "database", "inventory.db")

# -- Database Initialization Function ---
# Function to create the database and shirts table if they don't exist
# NOTE: This function runs every time the app starts,
# but the table is only created once because of "IF NOT EXISTS"
def init_db():
    # Connect to database (creates file if it doesn't exist)
    # SQLite creates a new file at DB_PATH if it doesn't already exist
    conn = sqlite3.connect(DB_PATH)

    # Create a cursor object to execute SQL commands
    # cursor is an object used to execute SQL queries and interact with the database
    cursor = conn.cursor()

    # --- Create Table SQL ---
    # Executes SQL command to create "shirts" table with specified columns
    # IF NOT EXISTS prevents duplicate table creation
    # id: unique identifier for each shirt entry, auto-increments
    # filename: name of uploaded image file, cannot be null
    # size columns track inventory counts per size, default to 0
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shirts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            size_s INTEGER DEFAULT 0,
            size_m INTEGER DEFAULT 0,
            size_l INTEGER DEFAULT 0,
            size_xl INTEGER DEFAULT 0,
            size_xxl INTEGER DEFAULT 0
        )
    """)

    # Commit changes to the database
    conn.commit()
    
    # Close the connection to free up memory/resources
    conn.close()
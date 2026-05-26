# VIMS Backend - Flask Application

# Import the function created in database.py to initialize the database
# NOTE: Python must import init_db() so it can be called before the server starts
from database import init_db

# Flask creates the backend application
# request lets you inspect incoming HTTP requests
# jsonify converts Python data to JSON format for API responses
# os interacts with the file system (folders, paths) 
from flask import Flask, request, jsonify
import os

# Create Flask app instance
#__name__ tells Flask where app lives
# Starts the backend server
app = Flask(__name__)

# --- Set upload folder ---
# os.path.abspath(__file__): gets full path to app.py
# os.path.dirname(...): removes filename, leaves backend directory
# BASE_DIR now points to the backend directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Move up one level to .../ (project root), then add "images" folder
UPLOAD_FOLDER = os.path.join(BASE_DIR, "..", "images")

# Create the images folder if it doesn't exist
# exist_ok=True means no error if folder already exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Add Inventory Item Route ---
# Creates endpoint POST /add-item to insert new record into the database
@app.route("/add-item", methods=["POST"]) # Route definition: listens for POST requests at /add-item
def add_item():
    # Get request data sent by the client in JSON format
    data = request.json

    # Validate input
    # Ensures request data exists and required "filename" field is provided
    if not data or "filename" not in data:
        return jsonify({"error": "Missing filename"}), 400
    
    # Extract values
    # If size fields are missing, default to 0 using data.get(key, default)
    filename = data.get("filename")
    size_s = data.get("size_s", 0)
    size_m = data.get("size_m", 0)
    size_l = data.get("size_l", 0)
    size_xl = data.get("size_xl", 0)
    size_xxl = data.get("size_xxl", 0)

    # Database import
    # Import locally to keep database dependencies scoped to this function
    import sqlite3
    # DB_PATH is reused from database.py to maintain a single source of truth
    from database import DB_PATH

    # Connect to the database
    # Opens database session
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Insert SQL data
    # Uses parameterized queries (?) to prevent SQL injection and ensure safe data insertion
    cursor.execute("""
        INSERT INTO shirts (filename, size_s, size_m, size_l, size_xl, size_xxl)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (filename, size_s, size_m, size_l, size_xl, size_xxl))

    # Save and close database connection
    # Writes data permanently to the database file and frees up resources
    conn.commit()
    conn.close()

    # Response confirms success to client with a JSON message
    return jsonify({"message": "Item added successfully"})

# --- Root Route ---
# Creates endpoint GET / when localhost:3000 is visited
@app.route("/")
def home():
    # Returns a simple message to confirm backend is running
    return "VIMS Backend Running 🚀"

# --- Upload Route ---
# Creates endpoint POST /upload, only accepts POST requests
@app.route("/upload", methods=["POST"])
# This function executes when a POST request is made to /upload
def upload_image():
    # Check if file exists. Looks for "image" key in uploaded files.
    # If missing, return JSON error message with 400 Bad Request status code
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    
    # request.files contains uploaded files sent via form-data in the HTTP request
    # Extract the file object using the "image" key
    file = request.files["image"]

    # --- Save file ---
    # Create full path to save the file: UPLOAD_FOLDER + original filename
    # NOTE: filename should be sanitized in production using secure_filename
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    # Write the file to disk at the specified path.
    file.save(file_path)

    # Return JSON response confirming upload with the original filename
    return jsonify({"message": "Image uploaded successfully", "filename": file.filename})

# Run server only if script is executed directly (not imported elsewhere)
if __name__ == "__main__":
    # NOTE: It is important to initialize system resources (like databases)
    # BEFORE starting the server, so the application is ready to handle requests

    # Connect to SQLite, create inventory.db file if it doesn't exist, and create shirts table if it doesn't exist
    init_db()

    # Starts the Flask development server with debug mode on and listens on port 3000
    # debug=True reloads on code changes and shows detailed error messages
    app.run(debug=True, port=3000)
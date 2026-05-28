# VIMS Backend - Flask Application

# Import database initialization function and DB path
# NOTE: Python must import init_db() so it can be called before the server starts
# NOTE: In larger applications, database connections are typically managed centrally
from database import init_db, DB_PATH

# Flask creates the backend application
# request lets you inspect incoming HTTP requests
# jsonify converts Python data to JSON format for API responses
from flask import Flask, request, jsonify

# os handles file paths and directories, used for saving uploaded images and defining upload folder
import os

# sqlite3 handles database operations, used to connect to the SQLite database and execute SQL queries
import sqlite3

# secure_filename prevents unsafe file paths
from werkzeug.utils import secure_filename 

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


# --- Add Inventory Item Route (Deprecated) ---
# NOTE: This endpoint is deprecated.
# It remains available for testing/manual insertion.
# Use /upload for normal application workflow.
@app.route("/add-item", methods=["POST"]) # Route definition: listens for POST requests at /add-item
def add_item():
    # Get request data sent by the client in JSON format
    data = request.get_json(silent=True) # silent=True prevents exceptions if JSON is invalid, returns None instead

    # Validate input
    # Ensures request data exists and required "filename" field is provided
    if not data or not data.get("filename"):
        return jsonify({
            "status": "error",
            "message": "Missing filename"
        }), 400

    # Extract values
    # If size fields are missing, default to 0 using data.get(key, default)
    filename = data.get("filename") # Required field, no default value
    size_s = data.get("size_s", 0)
    size_m = data.get("size_m", 0)
    size_l = data.get("size_l", 0)
    size_xl = data.get("size_xl", 0)
    size_xxl = data.get("size_xxl", 0)

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

    item_id = cursor.lastrowid # Retrieves the ID of the newly inserted record

    # Save and close database connection
    # Writes data permanently to the database file and frees up resources
    conn.commit()
    conn.close()

    # Response confirms success to client with a JSON message
    return jsonify({
        "status": "success",
        "message": "Item added successfully (deprecated endpoint - use /upload instead)",
        "data": {
            "id": item_id,
            "filename": filename
        }
    })

# --- Get Inventory Route ---
# Creates endpoint GET /items to retrieve all inventory records
@app.route("/items", methods=["GET"]) # Route definition: listens for GET requests at /items
def get_items():

    # Connect to the database
    conn = sqlite3.connect(DB_PATH) # Opens database session
    cursor = conn.cursor()

    # Execute SQL query to select all rows
    cursor.execute("SELECT * FROM shirts") # Returns all rows from the shirts table
    rows = cursor.fetchall() # Fetches all results as a list of tuples (not yet in JSON format)

    conn.close() # Close database connection

    # Convert database rows into JSON format
    # NOTE: Flask cannot directly send SQL tuples, must convert to list of dictionaries first
    items = []
    for row in rows:
        items.append({
            "id": row[0],
            "filename": row[1],
            "size_s": row[2],
            "size_m": row[3],
            "size_l": row[4],
            "size_xl": row[5],
            "size_xxl": row[6]
        })

    # Return JSON response containing the list of inventory items
    # Sends JSON list to client
    return jsonify({
        "status": "success",
        "count": len(items),
        "data": items
    })

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
    if "image" not in request.files or request.files["image"].filename == "":
        return jsonify({
            "status": "error",
            "message": "No image uploaded"
        }), 400
    
    # request.files contains uploaded files sent via form-data in the HTTP request
    # Extract the file object using the "image" key
    file = request.files["image"]

    # --- Secure the filename ---
    # Prevents malicious or invalid file paths
    filename = secure_filename(file.filename)

    # --- Save file ---
    # Create full path to save the file: UPLOAD_FOLDER + original filename
    # filename is sanitized using secure_filename to prevent unsafe file paths
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    # Write the file to disk at the specified path.
    file.save(file_path)

    # --- Extract inventory data ---
    # request.form returns strings, so convert values to integers using int()
    # default value of 0 is applied if field is missing
    try:
        size_s = int(request.form.get("size_s", 0))
        size_m = int(request.form.get("size_m", 0))
        size_l = int(request.form.get("size_l", 0))
        size_xl = int(request.form.get("size_xl", 0))
        size_xxl = int(request.form.get("size_xxl", 0))
    except ValueError:
        # If any size field is not a valid integer, return an error
        return jsonify({
            "status": "error",
            "message": "Invalid size values"
        }), 400

    # --- Insert into database ---
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO shirts (filename, size_s, size_m, size_l, size_xl, size_xxl)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (filename, size_s, size_m, size_l, size_xl, size_xxl))

    # Get inserted row ID
    item_id = cursor.lastrowid # Retrieves the ID of the newly inserted record

    conn.commit()
    conn.close()

    # Return JSON response confirming upload with the original filename
    return jsonify({
        "status": "success",
        "message": "Image uploaded and item added successfully",
        "data": {
            "id": item_id,
            "filename": filename,
            "size_s": size_s,
            "size_m": size_m,
            "size_l": size_l,
            "size_xl": size_xl,
            "size_xxl": size_xxl
        }
    })

# Run server only if script is executed directly (not imported elsewhere)
if __name__ == "__main__":
    # NOTE: It is important to initialize system resources (like databases)
    # BEFORE starting the server, so the application is ready to handle requests

    # Connect to SQLite, create inventory.db file if it doesn't exist, and create shirts table if it doesn't exist
    init_db()

    # Starts the Flask development server with debug mode on and listens on port 3000
    # debug=True reloads on code changes and shows detailed error messages
    app.run(debug=True, port=3000)
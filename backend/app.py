# VIMS Backend - Flask Application

# Flask creates the backend application
# request lets you inspect incoming HTTP requests
# jsonify converts Python data to JSON format for API responses
# send_from_directory is used to serve uploaded images so the frontend can display them
from flask import Flask, request, jsonify, send_from_directory

from flask_cors import CORS # Allows cross-origin requests from frontend (e.g., localhost:8000) to backend (localhost:3000)

# Create Flask app instance
app = Flask(__name__)

# Enable CORS
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True), # Allows all origins to access the API, necessary for frontend-backend communication during development

# Import database initialization function and DB path
# NOTE: Python must import init_db() so it can be called before the server starts
# NOTE: In larger applications, database connections are typically managed centrally
from database import init_db, DB_PATH

# os handles file paths and directories, used for saving uploaded images and defining upload folder
import os

# sqlite3 handles database operations, used to connect to the SQLite database and execute SQL queries
import sqlite3

# secure_filename prevents unsafe file paths
from werkzeug.utils import secure_filename 

# --- Set upload folder ---
# os.path.abspath(__file__): gets full path to app.py
# os.path.dirname(...): removes filename, leaves backend directory
# BASE_DIR now points to the backend directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FRONTEND_FOLDER = os.path.join(BASE_DIR, "..", "frontend") # Path to the frontend directory, used for serving index.html

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
    cursor.execute("SELECT * FROM shirts ORDER BY last_updated DESC") # Selects all columns from the shirts table, ordered by last_updated in descending order (newest first)
    rows = cursor.fetchall() # Fetches all results as a list of tuples (not yet in JSON format)

    conn.close() # Close database connection

    # Convert database rows into JSON format
    # NOTE: Flask cannot directly send SQL tuples, must convert to list of dictionaries first
    items = []
    for row in rows:
        items.append({
            # Maps each column in the database row to a key in the dictionary
            # category, price, size_xxxl, and last_updated may be None if they were added after the item was created and not updated yet
            "id": row[0], # ID is the first column (index 0)
            "filename": row[1],
            "size_s": row[2],
            "size_m": row[3],
            "size_l": row[4],
            "size_xl": row[5],
            "size_xxl": row[6],
            "display_name": row[7],
            "category": row[8],
            "price": row[9],
            "size_xxxl": row[10],
            "last_updated": row[11] # last_updated is the thirteenth column (index 12)
        })

    # Return JSON response containing the list of inventory items
    # Sends JSON list to client
    return jsonify({
        "status": "success",
        "count": len(items),
        "data": items
    })

# --- Serve Frontend Route ---
# This route serves the frontend index.html file when the root URL (/) is accessed.
@app.route("/")
def serve_frontend():
    return send_from_directory(FRONTEND_FOLDER, "index.html") # Sends the index.html file from the frontend directory when the root URL is accessed, allowing the frontend to be served by the Flask backend during development

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
    display_name = request.form.get("display_name") or filename  # Optional display name for the image, defaults to the original filename if not provided

    # --- Extract additional fields ---
    category = request.form.get("category") or "adult shirt" # Optional category field, defaults to "adult shirt" if not provided
    price = int(request.form.get("price") or 10) # Optional price field, defaults to 10 if not provided, converted to integer

    # Get current timestamp for last_updated field
    from datetime import datetime
    last_updated = datetime.now().isoformat() # Get current timestamp in ISO format for last_updated field

    # --- Save file ---
    # Create full path to save the file: UPLOAD_FOLDER + original filename
    # filename is sanitized using secure_filename to prevent unsafe file paths
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    # Write the file to disk at the specified path.
    file.save(file_path)

    # --- Extract inventory data ---
    # request.form returns strings, so convert values to integers using int()
    # default value of 0 is applied if field is missing
    def parse_size(value):
        if value == "" or value is None:
            return None
        return int(value)

    try:
        size_s = parse_size(request.form.get("size_s"))
        size_m = parse_size(request.form.get("size_m"))
        size_l = parse_size(request.form.get("size_l"))
        size_xl = parse_size(request.form.get("size_xl"))
        size_xxl = parse_size(request.form.get("size_xxl"))
    except ValueError:
        # If any size field is not a valid integer, return an error
        return jsonify({
            "status": "error",
            "message": "Invalid size values"
        }), 400

    # --- Insert into database ---
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Insert the new inventory item into the shirts table, including all relevant fields such as category, price, and last_updated
    cursor.execute("""
        INSERT INTO shirts (
            filename, display_name, category, price, size_s, size_m, size_l, size_xl, size_xxl, last_updated
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        filename, display_name, category, price, size_s, size_m, size_l, size_xl, size_xxl, last_updated
    ))

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
            "display_name": display_name,
            "size_s": size_s,
            "size_m": size_m,
            "size_l": size_l,
            "size_xl": size_xl,
            "size_xxl": size_xxl
        }
    })

# --- Serve Uploaded Images Route ---
# Allows the frontend to access uploaded images via /images/<filename>
@app.route("/images/<filename>")
def serve_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# --- Delete Item Route ---
@app.route("/delete-item/<int:item_id>", methods=["DELETE", "OPTIONS"]) # Route definition: listens for DELETE requests at /delete-item/<item_id>
def delete_item(item_id):

    if request.method == "OPTIONS":
        return '', 200 # Respond to preflight OPTIONS request with 200 OK

    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get filename before deleting
    cursor.execute("SELECT filename FROM shirts WHERE id = ?", (item_id,))
    result = cursor.fetchone() # Fetch the first result (should be only one row since ID is unique)

    if result:
        filename = result[0] # Extract filename from the result tuple

        # Delete the image file from disk
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(file_path):
            os.remove(file_path) # Remove the file from the filesystem

    # Delete from database
    cursor.execute("DELETE FROM shirts WHERE id = ?", (item_id,))
    conn.commit() # Save changes to the database
    conn.close() # Close database connection

    # Return JSON response confirming deletion
    return jsonify({
        "status": "success",
        "message": f"Item {item_id} deleted"
    })

# --- Update Item Route ---
@app.route("/update-item/<int:item_id>", methods=["PUT", "OPTIONS"]) # Route definition: listens for PUT requests at /update-item/<item_id>
def update_item(item_id):
    from datetime import datetime
    last_updated = datetime.now().isoformat() # Get current timestamp in ISO format for last_updated field

    if request.method == "OPTIONS":
        return '', 200 # Respond to preflight OPTIONS request with 200 OK

    # Get request data sent by the client in JSON format
    data = request.get_json()

    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    
    # Update the specified fields for the item with the given ID. Only updates fields that are provided in the request data.
    cursor.execute("""
        UPDATE shirts
        SET display_name = ?, size_s = ?, size_m = ?, size_l = ?, size_xl = ?, size_xxl = ?, size_xxxl = ?, last_updated = ?
        WHERE id = ?
    """, (
        data.get("display_name"),
        data.get("size_s"),
        data.get("size_m"),
        data.get("size_l"),
        data.get("size_xl"),
        data.get("size_xxl"),
        data.get("size_xxxl"),
        last_updated,
        item_id
    ))

    # Save changes to the database and close the connection
    conn.commit()
    conn.close()

    # Return JSON response confirming update
    return jsonify({
        "status": "success",
        "message": f"Item {item_id} updated"
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
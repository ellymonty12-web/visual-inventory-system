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
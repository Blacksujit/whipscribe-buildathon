"""Start the Flask app without debug reloader for background execution."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Initialize database
import store
store.init_db()

from app import app

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)

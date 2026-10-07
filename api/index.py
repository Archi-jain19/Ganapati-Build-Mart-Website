import sys
import os

# Add parent directory to sys.path so app.py and db.py can be imported seamlessly
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from app import app

# Export WSGI application callable for Vercel Serverless
application = app

if __name__ == "__main__":
    app.run()

#!/usr/bin/env python3
"""
Database initialization script for the RAG Chatbot
This script creates the necessary tables in the Neon Serverless Postgres database
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import init_db

def main():
    print("Initializing Neon Serverless Postgres database...")
    try:
        init_db()
        print("Database initialization completed successfully!")
    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
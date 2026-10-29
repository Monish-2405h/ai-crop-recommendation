"""
create_admin.py
===============
Run this script to create an admin account in MongoDB.

Usage:
  python create_admin.py
"""
import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

import os, datetime, bcrypt
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / "backend" / ".env")
load_dotenv(BASE_DIR / ".env")

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.server_info()
    db     = client["ai_crop_advisor"]
    users  = db["users"]
    print("Connected to MongoDB:", MONGO_URI)
except Exception as e:
    print(f"Failed to connect to MongoDB at {MONGO_URI}: {e}")
    print("Please start MongoDB (net start MongoDB or mongod) and try again.")
    exit(1)

print("\n=== Create Admin Account ===")
name  = input("Admin name (default: Admin): ").strip() or "Admin"
email = input("Admin email: ").strip().lower()
if not email or "@" not in email:
    print("Invalid email address"); exit(1)

pw    = input("Admin password (min 6 chars): ").strip()
if len(pw) < 6:
    print("Password too short (minimum 6 characters required)"); exit(1)

if users.find_one({"email": email}):
    print(f"Email '{email}' already exists in database"); exit(1)

hashed = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
doc = {
    "name": name,
    "email": email,
    "password": hashed,
    "role": "admin",
    "createdAt": datetime.datetime.utcnow().isoformat()
}
users.insert_one(doc)
print(f"\nAdmin account created successfully!")
print(f"   Email : {email}")
print(f"   Role  : admin")
print("   You can now log in at: http://localhost:5000/admin")

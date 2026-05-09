"""
Run this script once to create the first manager account.

Usage (from the web-programming/ directory):
    python scripts/create_manager.py

Set MANAGER_USERNAME, MANAGER_EMAIL, MANAGER_PASSWORD via env vars or edit below.
"""

import os
import sys
from pathlib import Path

# Add project root to path so backend imports work
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / "backend" / ".env")

from sqlmodel import Session, select
from backend.database import engine, create_db_and_tables
from backend.models import User, UserRole
from backend.auth_utils import hash_password, validate_password_strength

USERNAME = os.getenv("MANAGER_USERNAME", "manager")
EMAIL    = os.getenv("MANAGER_EMAIL",    "manager@nucleiai.com")
PASSWORD = os.getenv("MANAGER_PASSWORD", "")

def main():
    create_db_and_tables()

    if not PASSWORD:
        print("ERROR: set MANAGER_PASSWORD env var before running this script.")
        print("  Example: MANAGER_PASSWORD='MyStr0ng!Pass' python scripts/create_manager.py")
        sys.exit(1)

    try:
        validate_password_strength(PASSWORD)
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    with Session(engine) as session:
        existing = session.exec(
            select(User).where((User.email == EMAIL) | (User.username == USERNAME))
        ).first()
        if existing:
            print(f"User '{existing.username}' already exists (role: {existing.role.value}).")
            if existing.role != UserRole.manager:
                existing.role = UserRole.manager
                session.add(existing)
                session.commit()
                print(f"Promoted '{existing.username}' to manager.")
            else:
                print("Already a manager — nothing to do.")
            return

        user = User(
            username=USERNAME,
            email=EMAIL,
            hashed_password=hash_password(PASSWORD),
            role=UserRole.manager,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        print(f"Manager created: id={user.id}, username={user.username}, email={user.email}")

if __name__ == "__main__":
    main()

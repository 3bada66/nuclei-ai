"""
Bootstrap the first manager account.

Run ONCE on a fresh database before making the app publicly accessible:

    cd web-programming/
    python -m backend.seed

This script is idempotent — it does nothing if a manager already exists.
"""

from __future__ import annotations

import getpass
import sys

from sqlmodel import Session, select

from backend.auth_utils import hash_password, validate_password_strength
from backend.database import create_db_and_tables, engine
from backend.models import User, UserRole


def main() -> None:
    create_db_and_tables()

    with Session(engine) as session:
        existing_manager = session.exec(
            select(User).where(User.role == UserRole.manager)
        ).first()

        if existing_manager:
            print(f"[seed] Manager already exists: '{existing_manager.username}' — nothing to do.")
            return

        print("=== NucleiAI — First Manager Setup ===")
        print("This account will have full administrative privileges.\n")

        username = input("Username (3-50 chars): ").strip()
        if len(username) < 3 or len(username) > 50:
            print("Error: username must be 3-50 characters.")
            sys.exit(1)

        email = input("Email: ").strip()
        if "@" not in email or "." not in email.split("@")[-1]:
            print("Error: invalid email address.")
            sys.exit(1)

        while True:
            password = getpass.getpass("Password (min 8 chars, upper, lower, digit, special): ")
            try:
                validate_password_strength(password)
                break
            except ValueError as e:
                print(f"Error: {e}")

        clash = session.exec(
            select(User).where((User.email == email) | (User.username == username))
        ).first()
        if clash:
            print("Error: username or email already registered.")
            sys.exit(1)

        manager = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            role=UserRole.manager,
        )
        session.add(manager)
        session.commit()
        print(f"\n[seed] Manager account '{username}' created successfully.")
        print("[seed] You can now start the server and log in.")


if __name__ == "__main__":
    main()

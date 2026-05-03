#!/usr/bin/env python3
"""
Setup test users for URIS-AI load testing.

This script creates test user accounts in the database for use in load tests.

Usage:
    python tests/load/setup_test_users.py

Requirements: 10.2
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session

from uris_ai.models.database import User, get_db
from uris_ai.services.auth_service import AuthService


def create_test_users(db: Session, auth_service: AuthService):
    """
    Create test users for load testing.
    
    Args:
        db: Database session
        auth_service: Authentication service for password hashing
    """
    test_users = [
        {
            "username": "test_user_1",
            "password": "test_password_1",
            "role": "public",
            "email": "test1@example.com",
        },
        {
            "username": "test_user_2",
            "password": "test_password_2",
            "role": "public",
            "email": "test2@example.com",
        },
        {
            "username": "test_user_3",
            "password": "test_password_3",
            "role": "public",
            "email": "test3@example.com",
        },
        {
            "username": "test_facility_manager",
            "password": "test_password_facility",
            "role": "facility_manager",
            "email": "facility@example.com",
        },
        {
            "username": "test_government",
            "password": "test_password_gov",
            "role": "government",
            "email": "government@example.com",
        },
    ]
    
    created_count = 0
    skipped_count = 0
    
    for user_data in test_users:
        # Check if user already exists
        existing = db.query(User).filter(User.username == user_data["username"]).first()
        
        if existing:
            print(f"⊘ User '{user_data['username']}' already exists, skipping")
            skipped_count += 1
            continue
        
        # Create new user
        user = User(
            username=user_data["username"],
            email=user_data["email"],
            password_hash=auth_service.hash_password(user_data["password"]),
            role=user_data["role"],
            is_active=True,
        )
        
        db.add(user)
        print(f"✓ Created user '{user_data['username']}' with role '{user_data['role']}'")
        created_count += 1
    
    # Commit all changes
    db.commit()
    
    print("\n" + "=" * 80)
    print(f"Test user setup complete:")
    print(f"  Created: {created_count}")
    print(f"  Skipped (already exists): {skipped_count}")
    print(f"  Total: {created_count + skipped_count}")
    print("=" * 80)


def main():
    """Main entry point."""
    print("=" * 80)
    print("URIS-AI Load Test User Setup")
    print("=" * 80)
    print("Creating test users for load testing...")
    print()
    
    try:
        # Get database session
        db = next(get_db())
        
        # Get auth service
        auth_service = AuthService()
        
        # Create test users
        create_test_users(db, auth_service)
        
        print("\n✓ Test users are ready for load testing")
        print("\nYou can now run load tests with:")
        print("  python tests/load/run_load_tests.py target --host http://localhost:8000")
        
    except Exception as e:
        print(f"\n✗ Error setting up test users: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

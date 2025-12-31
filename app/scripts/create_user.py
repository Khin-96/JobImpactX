"""
User Creation Script.
Create users with specific roles.
"""

import sys
import argparse
import logging
from app.config.logging import setup_logging
from app.db.session import SessionLocal
from app.db.queries import create_user, get_user_by_username, get_user_by_email
from app.auth.security import hash_password

setup_logging()
logger = logging.getLogger(__name__)


def create_user_account(
    username: str,
    email: str,
    password: str,
    role: str = "Analyst"
):
    """
    Create a new user account.
    
    Args:
        username: Username for the account
        email: Email address
        password: Plain text password (will be hashed)
        role: User role (Admin, Analyst, Viewer)
    """
    
    # Validate role
    valid_roles = ["Admin", "Analyst", "Viewer"]
    if role not in valid_roles:
        logger.error(f"Invalid role: {role}. Must be one of {valid_roles}")
        sys.exit(1)
    
    db = SessionLocal()
    try:
        # Check if username exists
        existing_user = get_user_by_username(db, username)
        if existing_user:
            logger.error(f"Username already exists: {username}")
            sys.exit(1)
        
        # Check if email exists
        existing_email = get_user_by_email(db, email)
        if existing_email:
            logger.error(f"Email already registered: {email}")
            sys.exit(1)
        
        # Hash password
        hashed_password = hash_password(password)
        
        # Create user
        user = create_user(
            db=db,
            username=username,
            email=email,
            hashed_password=hashed_password,
            role=role
        )
        
        logger.info(f"User created successfully:")
        logger.info(f"  Username: {user.username}")
        logger.info(f"  Email: {user.email}")
        logger.info(f"  Role: {user.role}")
        logger.info(f"  ID: {user.id}")
        
        print("\n" + "="*60)
        print("USER CREATED SUCCESSFULLY")
        print("="*60)
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print(f"Role: {user.role}")
        print(f"ID: {user.id}")
        print(f"Active: {user.is_active}")
        print("="*60 + "\n")
        
        if role == "Admin":
            print("IMPORTANT: This user has administrative privileges.")
            print("Ensure the password is kept secure.")
        
    except Exception as e:
        logger.error(f"Failed to create user: {e}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a new user account")
    parser.add_argument(
        "--username",
        required=True,
        help="Username for the account"
    )
    parser.add_argument(
        "--email",
        required=True,
        help="Email address"
    )
    parser.add_argument(
        "--password",
        required=True,
        help="Password (will be hashed)"
    )
    parser.add_argument(
        "--role",
        default="Analyst",
        choices=["Admin", "Analyst", "Viewer"],
        help="User role (default: Analyst)"
    )
    
    args = parser.parse_args()
    
    create_user_account(
        username=args.username,
        email=args.email,
        password=args.password,
        role=args.role
    )

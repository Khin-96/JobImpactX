import logging
import os
from app.db.session import engine
from app.db.models import Base
from app.config.logging import setup_logging
from app.db.queries import create_user, get_user_by_username
from app.db.session import SessionLocal
from app.auth.security import hash_password

setup_logging()
logger = logging.getLogger(__name__)


def create_default_admin():
    """Create default admin user if it doesn't exist."""
    db = SessionLocal()
    try:
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_email = os.getenv("ADMIN_EMAIL", "admin@jobimpactx.com")
        admin_password = os.getenv("ADMIN_PASSWORD", "ChangeThisPassword123!")
        
        existing_admin = get_user_by_username(db, admin_username)
        
        if not existing_admin:
            hashed_password = hash_password(admin_password)
            admin_user = create_user(
                db=db,
                username=admin_username,
                email=admin_email,
                hashed_password=hashed_password,
                role="Admin"
            )
            logger.info(f"Created default admin user: {admin_username}")
            logger.warning(
                f"IMPORTANT: Change the default admin password immediately! "
                f"Username: {admin_username}"
            )
        else:
            logger.info(f"Admin user already exists: {admin_username}")
    
    except Exception as e:
        logger.error(f"Failed to create admin user: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


def init_db():
    """Create all tables and initialize database."""
    logger.info("Initializing database...")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Create default admin user
        create_default_admin()
        
        logger.info("Database initialization complete")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    init_db()
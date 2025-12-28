import logging
from app.db.session import engine
from app.db.models import Base
from app.config.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

def init_db():
    """Create all tables."""
    logger.info("Initializing database...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully")

if __name__ == "__main__":
    init_db()
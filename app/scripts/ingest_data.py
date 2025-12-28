import pandas as pd
import logging
import sys
from pathlib import Path
from app.config.logging import setup_logging
from app.db.session import SessionLocal
from app.db.models import Role
import uuid
from datetime import datetime

setup_logging()
logger = logging.getLogger(__name__)

def ingest_data(csv_path: str, validate: bool = True, deduplicate: bool = True):
    """
    Ingest CSV file into database.
    
    Args:
        csv_path: Path to CSV file
        validate: Perform validation
        deduplicate: Remove duplicates
    """
    
    if not Path(csv_path).exists():
        logger.error(f"File not found: {csv_path}")
        sys.exit(1)
    
    # Read CSV
    logger.info(f"Reading CSV: {csv_path}")
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    
    # Validate
    if validate:
        required = ['Job_Title', 'Average_Salary', 'Years_Experience', 
                   'Education_Level', 'AI_Exposure_Index', 'Tech_Growth_Factor']
        missing = set(required) - set(df.columns)
        if missing:
            logger.error(f"Missing columns: {missing}")
            sys.exit(1)
    
    # Deduplicate
    if deduplicate:
        initial = len(df)
        df = df.drop_duplicates(subset=['Job_Title', 'Average_Salary', 'Years_Experience'])
        logger.info(f"Deduplicated: {initial} -> {len(df)} rows")
    
    # Insert into database
    db = SessionLocal()
    try:
        skill_cols = [f'Skill_{i}' for i in range(1, 11)]
        
        for idx, row in df.iterrows():
            role = Role(
                id=uuid.uuid4(),
                job_title=row['Job_Title'],
                average_salary=float(row['Average_Salary']),
                years_experience=int(row['Years_Experience']),
                education_level=row['Education_Level'],
                ai_exposure_index=float(row['AI_Exposure_Index']),
                tech_growth_factor=float(row['Tech_Growth_Factor']),
                skills=[float(row[col]) for col in skill_cols if col in df.columns],
                created_at=datetime.utcnow()
            )
            db.add(role)
            
            if (idx + 1) % 100 == 0:
                logger.info(f"Processed {idx + 1} rows")
        
        db.commit()
        logger.info(f"Successfully ingested {len(df)} roles")
    
    except Exception as e:
        db.rollback()
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", help="Path to CSV file")
    parser.add_argument("--validate", action="store_true", default=True)
    parser.add_argument("--deduplicate", action="store_true", default=True)
    args = parser.parse_args()
    
    ingest_data(args.csv_path, args.validate, args.deduplicate)
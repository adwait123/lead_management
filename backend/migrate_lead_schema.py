"""
Database migration script to add new fields to Lead model
Run this to update the staging database schema
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from models.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_lead_schema():
    """Add new fields to leads table"""

    migrations = [
        # Add external_id field for Yelp lead IDs, etc.
        "ALTER TABLE leads ADD COLUMN external_id VARCHAR(255);",
        "CREATE INDEX IF NOT EXISTS idx_leads_external_id ON leads(external_id);",

        # Add first_name and last_name fields
        "ALTER TABLE leads ADD COLUMN first_name VARCHAR(255);",
        "ALTER TABLE leads ADD COLUMN last_name VARCHAR(255);",

        # Make name field nullable since we now have first_name/last_name
        "ALTER TABLE leads ALTER COLUMN name DROP NOT NULL;"
    ]

    try:
        with engine.connect() as conn:
            for migration in migrations:
                try:
                    logger.info(f"Executing: {migration}")
                    conn.execute(text(migration))
                    conn.commit()
                    logger.info("✅ Migration executed successfully")
                except Exception as e:
                    if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                        logger.info(f"⚠️ Column already exists, skipping: {migration}")
                    else:
                        logger.error(f"❌ Migration failed: {migration}")
                        logger.error(f"Error: {e}")
                        raise

        logger.info("🎉 All migrations completed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Migration process failed: {e}")
        return False

def verify_schema():
    """Verify the new schema is correct"""
    try:
        with engine.connect() as conn:
            # Check if new columns exist
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'leads'
                AND column_name IN ('external_id', 'first_name', 'last_name')
                ORDER BY column_name;
            """))

            columns = [row[0] for row in result]
            expected_columns = ['external_id', 'first_name', 'last_name']

            logger.info(f"Found columns: {columns}")

            if set(columns) == set(expected_columns):
                logger.info("✅ Schema verification successful!")
                return True
            else:
                missing = set(expected_columns) - set(columns)
                logger.error(f"❌ Missing columns: {missing}")
                return False

    except Exception as e:
        logger.error(f"❌ Schema verification failed: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Starting Lead model migration...")

    if migrate_lead_schema():
        print("🔍 Verifying schema...")
        if verify_schema():
            print("🎉 Migration completed successfully!")
            print("📋 New fields added:")
            print("   - external_id: For Yelp lead IDs and other external references")
            print("   - first_name: Customer first name")
            print("   - last_name: Customer last name")
            print("   - name: Now nullable (backward compatibility)")
        else:
            print("❌ Schema verification failed!")
            sys.exit(1)
    else:
        print("❌ Migration failed!")
        sys.exit(1)
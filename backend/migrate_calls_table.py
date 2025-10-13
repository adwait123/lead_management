#!/usr/bin/env python3
"""
Database Migration Script for Outbound Calling Feature
Creates the calls table and related indexes
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text, inspect, MetaData
from sqlalchemy.exc import SQLAlchemyError

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import DATABASE_URL, Base
from models.call import Call
from models.agent import Agent
from models.lead import Lead

def check_database_connection(engine):
    """Test database connectivity"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def table_exists(engine, table_name):
    """Check if a table exists in the database"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def create_calls_table(engine):
    """Create the calls table"""
    try:
        # Import Call model to ensure relationships are properly set up
        from models import Call

        # Check if table already exists
        if table_exists(engine, 'calls'):
            print("✅ calls table already exists")
            return True

        print("Creating calls table...")
        Call.__table__.create(engine, checkfirst=True)
        print("✅ calls table created successfully")
        return True

    except Exception as e:
        print(f"❌ Failed to create calls table: {e}")
        return False

def create_call_indexes(engine):
    """Create performance indexes for calls table"""
    try:
        with engine.connect() as conn:
            # Calls table indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_calls_lead_id
                ON calls (lead_id)
            """))

            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_calls_agent_id
                ON calls (agent_id)
            """))

            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_calls_status_created
                ON calls (call_status, created_at DESC)
            """))

            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_calls_phone_number
                ON calls (phone_number)
            """))

            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_calls_initiated_at
                ON calls (initiated_at DESC)
            """))

            conn.commit()
            print("✅ Call indexes created")

    except Exception as e:
        print(f"❌ Error creating call indexes: {e}")

def verify_call_table_structure(engine):
    """Verify calls table exists with correct structure"""
    try:
        inspector = inspect(engine)

        if not table_exists(engine, 'calls'):
            print("❌ Missing calls table")
            return False

        columns = inspector.get_columns('calls')
        column_names = [col['name'] for col in columns]

        expected_columns = [
            'id', 'lead_id', 'agent_id', 'phone_number', 'call_status',
            'room_name', 'call_duration', 'transcript', 'call_summary',
            'call_metadata', 'error_message', 'retry_count',
            'initiated_at', 'answered_at', 'ended_at', 'created_at', 'updated_at'
        ]

        missing_columns = [col for col in expected_columns if col not in column_names]
        if missing_columns:
            print(f"❌ Missing columns in calls table: {missing_columns}")
            return False

        print(f"✅ calls table verified ({len(columns)} columns)")
        return True

    except Exception as e:
        print(f"❌ Error verifying calls table structure: {e}")
        return False

def check_call_foreign_keys(engine):
    """Verify calls table foreign key relationships"""
    try:
        inspector = inspect(engine)

        if not table_exists(engine, 'calls'):
            return True

        foreign_keys = inspector.get_foreign_keys('calls')
        fk_tables = [fk['referred_table'] for fk in foreign_keys]

        expected_fk_tables = ['leads', 'agents']
        for table in expected_fk_tables:
            if table in fk_tables:
                print(f"✅ Calls table foreign key to {table} verified")
            else:
                print(f"⚠️  Warning: Calls foreign key to {table} not found")

        return True

    except Exception as e:
        print(f"❌ Error checking calls foreign key constraints: {e}")
        return False

def test_calls_table_operations(engine):
    """Test basic operations on calls table"""
    try:
        with engine.connect() as conn:
            if table_exists(engine, 'calls'):
                result = conn.execute(text("SELECT COUNT(*) FROM calls"))
                count = result.scalar()
                print(f"✅ calls table accessible (current rows: {count})")
            else:
                print("❌ calls table not accessible")
                return False

        return True

    except Exception as e:
        print(f"❌ Error testing calls table operations: {e}")
        return False

def main():
    """Main migration function"""
    print("=" * 70)
    print("OUTBOUND CALLING FEATURE DATABASE MIGRATION")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'Local'}")
    print()

    # Create engine
    engine = create_engine(DATABASE_URL)

    # Step 1: Test database connection
    print("1. Testing database connection...")
    if not check_database_connection(engine):
        return False

    # Step 2: Create calls table
    print("\n2. Creating calls table...")
    if not create_calls_table(engine):
        return False

    # Step 3: Verify table structure
    print("\n3. Verifying calls table structure...")
    if not verify_call_table_structure(engine):
        return False

    # Step 4: Check foreign key constraints
    print("\n4. Checking foreign key constraints...")
    check_call_foreign_keys(engine)

    # Step 5: Create performance indexes
    print("\n5. Creating performance indexes...")
    create_call_indexes(engine)

    # Step 6: Test table operations
    print("\n6. Testing calls table operations...")
    if not test_calls_table_operations(engine):
        return False

    print("\n" + "=" * 70)
    print("✅ OUTBOUND CALLING MIGRATION COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print()
    print("Calls table is now ready for outbound calling:")
    print("✅ calls - Outbound call tracking and management")
    print()
    print("Features now available:")
    print("- Track outbound call status and history")
    print("- Store call transcripts and summaries")
    print("- Link calls to leads and agents")
    print("- Call performance metrics")
    print()
    print("Next steps:")
    print("- Configure outbound calling agents")
    print("- Test call dispatch functionality")
    print("- Set up LiveKit SIP integration")

    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎉 Calls migration finished successfully!")
            sys.exit(0)
        else:
            print("\n💥 Migration failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error during migration: {e}")
        sys.exit(1)
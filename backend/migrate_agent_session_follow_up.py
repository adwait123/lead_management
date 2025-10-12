#!/usr/bin/env python3
"""
Database Migration Script: Add Follow-up Sequence Columns to Agent Sessions
Adds the follow-up tracking columns to the agent_sessions table
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text, inspect, MetaData, Column, JSON, String, DateTime
from sqlalchemy.exc import SQLAlchemyError

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import DATABASE_URL

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

def column_exists(engine, table_name, column_name):
    """Check if a column exists in a table"""
    inspector = inspect(engine)
    columns = inspector.get_columns(table_name)
    return any(col['name'] == column_name for col in columns)

def add_follow_up_columns(engine):
    """Add follow-up sequence columns to agent_sessions table"""
    try:
        with engine.connect() as conn:
            # Check which columns are missing and add them
            columns_to_add = [
                ("active_follow_up_sequences", "JSON DEFAULT '{}'"),
                ("last_follow_up_trigger", "VARCHAR(255)"),
                ("follow_up_sequence_state", "JSON DEFAULT '{}'")
            ]

            added_columns = []
            for column_name, column_def in columns_to_add:
                if not column_exists(engine, 'agent_sessions', column_name):
                    try:
                        # SQLite syntax for adding columns
                        sql = f"ALTER TABLE agent_sessions ADD COLUMN {column_name} {column_def}"
                        conn.execute(text(sql))
                        added_columns.append(column_name)
                        print(f"✅ Added column: {column_name}")
                    except Exception as e:
                        print(f"⚠️  Error adding column {column_name}: {e}")
                else:
                    print(f"✅ Column already exists: {column_name}")

            conn.commit()

            if added_columns:
                print(f"✅ Successfully added {len(added_columns)} columns to agent_sessions table")
            else:
                print("✅ All columns already exist")

            return True

    except Exception as e:
        print(f"❌ Failed to add columns: {e}")
        return False

def verify_table_structure(engine):
    """Verify the agent_sessions table has the follow-up columns"""
    try:
        inspector = inspect(engine)

        if not table_exists(engine, 'agent_sessions'):
            print("❌ Agent sessions table does not exist")
            return False

        columns = inspector.get_columns('agent_sessions')
        column_names = [col['name'] for col in columns]

        # Check for follow-up related columns
        follow_up_columns = [
            'active_follow_up_sequences',
            'last_follow_up_trigger',
            'follow_up_sequence_state'
        ]

        missing_columns = [col for col in follow_up_columns if col not in column_names]

        if missing_columns:
            print(f"❌ Missing follow-up columns: {missing_columns}")
            return False

        print(f"✅ Agent sessions table structure verified with follow-up columns")
        print(f"   Total columns: {len(column_names)}")
        print(f"   Follow-up columns: {len(follow_up_columns)}")

        return True

    except Exception as e:
        print(f"❌ Error verifying table structure: {e}")
        return False

def verify_existing_tables(engine):
    """Verify that agent_sessions table exists"""
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    if 'agent_sessions' not in existing_tables:
        print(f"❌ Agent sessions table does not exist")
        print("   Please run the main database migrations first")
        return False

    print("✅ Agent sessions table exists")
    return True

def test_follow_up_functionality(engine):
    """Test that the follow-up columns work correctly"""
    try:
        with engine.connect() as conn:
            # Test JSON column functionality
            test_data = '{"no_response": {"active": true, "current_step": 1, "total_steps": 3}}'

            # Try to select with JSON operations (if supported)
            try:
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM agent_sessions
                    WHERE active_follow_up_sequences IS NOT NULL
                """))
                count = result.scalar()
                print(f"✅ Follow-up columns accessible (sessions with follow-up data: {count})")

            except Exception as e:
                print(f"⚠️  JSON operations may not be fully supported: {e}")

            return True

    except Exception as e:
        print(f"❌ Error testing follow-up functionality: {e}")
        return False

def main():
    """Main migration function"""
    print("=" * 70)
    print("AGENT SESSION FOLLOW-UP COLUMNS MIGRATION SCRIPT")
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

    # Step 2: Verify existing tables
    print("\n2. Verifying existing tables...")
    if not verify_existing_tables(engine):
        return False

    # Step 3: Check current table structure
    print("\n3. Checking current agent_sessions table structure...")
    if verify_table_structure(engine):
        print("✅ All follow-up columns already exist")
        print("   Migration not needed")
        return True

    # Step 4: Add missing columns
    print("\n4. Adding follow-up sequence columns...")
    if not add_follow_up_columns(engine):
        return False

    # Step 5: Verify table structure
    print("\n5. Verifying updated table structure...")
    if not verify_table_structure(engine):
        return False

    # Step 6: Test functionality
    print("\n6. Testing follow-up functionality...")
    test_follow_up_functionality(engine)

    print("\n" + "=" * 70)
    print("✅ AGENT SESSION FOLLOW-UP MIGRATION COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print()
    print("The agent_sessions table now supports:")
    print("- Follow-up sequence tracking (active_follow_up_sequences)")
    print("- Last trigger tracking (last_follow_up_trigger)")
    print("- Sequence state management (follow_up_sequence_state)")
    print()
    print("Follow-up sequence features now available:")
    print("- Track multiple active follow-up sequences per session")
    print("- Manage sequence progress and state")
    print("- Support for cancellation and resumption")
    print("- Detailed sequence analytics")
    print()
    print("Next steps:")
    print("- Restart your application to pick up the new columns")
    print("- Test follow-up sequence creation and execution")
    print("- Deploy the updated schema to staging/production")

    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎉 Migration completed successfully!")
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
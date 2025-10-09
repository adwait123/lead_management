#!/usr/bin/env python3
"""
Database Migration Script: Add Message Table
Creates the messages table for storing conversation history between agents and leads
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text, inspect, MetaData
from sqlalchemy.exc import SQLAlchemyError

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import DATABASE_URL, Base
from models.message import Message

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

def create_messages_table(engine):
    """Create the messages table"""
    try:
        # Import all models to ensure relationships are properly set up
        from models import Agent, Lead, AgentSession, Message

        # Create only the messages table
        Message.__table__.create(engine, checkfirst=True)
        print("✅ Messages table created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create messages table: {e}")
        return False

def verify_table_structure(engine):
    """Verify the messages table structure"""
    try:
        inspector = inspect(engine)

        if not table_exists(engine, 'messages'):
            print("❌ Messages table does not exist")
            return False

        columns = inspector.get_columns('messages')
        column_names = [col['name'] for col in columns]

        # Expected columns
        expected_columns = [
            'id', 'agent_session_id', 'lead_id', 'agent_id', 'content',
            'message_type', 'sender_type', 'sender_name', 'message_status',
            'delivery_status', 'error_message', 'external_message_id',
            'external_conversation_id', 'external_platform', 'message_metadata',
            'prompt_used', 'model_used', 'response_time_ms', 'token_usage',
            'parent_message_id', 'thread_id', 'created_at', 'updated_at',
            'sent_at', 'delivered_at', 'read_at', 'is_flagged',
            'flagged_reason', 'quality_score'
        ]

        missing_columns = [col for col in expected_columns if col not in column_names]

        if missing_columns:
            print(f"❌ Missing columns: {missing_columns}")
            return False

        print(f"✅ Messages table structure verified ({len(column_names)} columns)")

        # Check foreign key constraints
        foreign_keys = inspector.get_foreign_keys('messages')
        fk_tables = [fk['referred_table'] for fk in foreign_keys]

        expected_fk_tables = ['agent_sessions', 'leads', 'agents']
        for table in expected_fk_tables:
            if table not in fk_tables:
                print(f"⚠️  Warning: Foreign key to {table} table not found")
            else:
                print(f"✅ Foreign key to {table} table verified")

        return True

    except Exception as e:
        print(f"❌ Error verifying table structure: {e}")
        return False

def create_indexes(engine):
    """Create additional indexes for better performance"""
    try:
        with engine.connect() as conn:
            # Index on agent_session_id and created_at for conversation history
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_messages_session_created
                ON messages (agent_session_id, created_at DESC)
            """))

            # Index on lead_id and created_at for lead message history
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_messages_lead_created
                ON messages (lead_id, created_at DESC)
            """))

            # Index on external_conversation_id for webhook lookups
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_messages_external_conv
                ON messages (external_conversation_id)
            """))

            # Index on sender_type and message_status for filtering
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_messages_sender_status
                ON messages (sender_type, message_status)
            """))

            conn.commit()
            print("✅ Performance indexes created")

    except Exception as e:
        print(f"❌ Error creating indexes: {e}")

def verify_existing_tables(engine):
    """Verify that required tables exist"""
    required_tables = ['agents', 'leads', 'agent_sessions']
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    missing_tables = [table for table in required_tables if table not in existing_tables]

    if missing_tables:
        print(f"❌ Missing required tables: {missing_tables}")
        print("   Please run the main database migrations first")
        return False

    print("✅ All required parent tables exist")
    return True

def main():
    """Main migration function"""
    print("=" * 60)
    print("MESSAGE TABLE MIGRATION SCRIPT")
    print("=" * 60)
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

    # Step 3: Check if messages table already exists
    print("\n3. Checking for existing messages table...")
    if table_exists(engine, 'messages'):
        print("⚠️  Messages table already exists")
        print("   Verifying structure...")
        if verify_table_structure(engine):
            print("✅ Messages table structure is correct")
            print("   Migration not needed")
            return True
        else:
            print("❌ Messages table structure is incorrect")
            print("   Manual intervention required")
            return False

    # Step 4: Create messages table
    print("\n4. Creating messages table...")
    if not create_messages_table(engine):
        return False

    # Step 5: Verify table structure
    print("\n5. Verifying table structure...")
    if not verify_table_structure(engine):
        return False

    # Step 6: Create performance indexes
    print("\n6. Creating performance indexes...")
    create_indexes(engine)

    # Step 7: Final verification
    print("\n7. Final verification...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM messages"))
            count = result.scalar()
            print(f"✅ Messages table accessible (current rows: {count})")
    except Exception as e:
        print(f"❌ Error accessing messages table: {e}")
        return False

    print("\n" + "=" * 60)
    print("✅ MESSAGE TABLE MIGRATION COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print()
    print("The messages table is now ready for use.")
    print("You can now:")
    print("- Store conversation messages between agents and leads")
    print("- Track message delivery status")
    print("- Maintain conversation history")
    print("- Support external platform integration (Yelp, Zapier)")
    print()
    print("Next steps:")
    print("- Deploy the updated models to your application")
    print("- Test the message creation and retrieval functionality")
    print("- Configure webhook endpoints to use message storage")

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
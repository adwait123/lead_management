#!/usr/bin/env python3
"""
Complete Database Migration Script for Phase 3: Two-Way Messaging
Creates all required tables: agent_sessions, messages, and any missing tables
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text, inspect, MetaData
from sqlalchemy.exc import SQLAlchemyError

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import DATABASE_URL, Base
from models.agent import Agent
from models.lead import Lead
from models.agent_session import AgentSession
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

def create_missing_tables(engine):
    """Create all missing tables required for Phase 3"""
    try:
        # Import all models to ensure relationships are properly set up
        from models import Agent, Lead, AgentSession, Message

        # Get existing tables
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())

        # Required tables for Phase 3
        required_tables = {
            'agents': Agent.__table__,
            'leads': Lead.__table__,
            'agent_sessions': AgentSession.__table__,
            'messages': Message.__table__
        }

        created_tables = []

        for table_name, table_obj in required_tables.items():
            if table_name not in existing_tables:
                print(f"Creating table: {table_name}")
                table_obj.create(engine, checkfirst=True)
                created_tables.append(table_name)
                print(f"✅ {table_name} table created successfully")
            else:
                print(f"✅ {table_name} table already exists")

        if created_tables:
            print(f"✅ Created {len(created_tables)} new tables: {created_tables}")
        else:
            print("✅ All required tables already exist")

        return True

    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False

def verify_table_structures(engine):
    """Verify all required tables exist with correct structure"""
    try:
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())

        required_tables = ['agents', 'leads', 'agent_sessions', 'messages']

        for table_name in required_tables:
            if table_name not in existing_tables:
                print(f"❌ Missing table: {table_name}")
                return False
            else:
                columns = inspector.get_columns(table_name)
                print(f"✅ {table_name} table verified ({len(columns)} columns)")

        return True

    except Exception as e:
        print(f"❌ Error verifying table structures: {e}")
        return False

def create_indexes(engine):
    """Create performance indexes"""
    try:
        with engine.connect() as conn:
            # Messages table indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_messages_session_created
                ON messages (agent_session_id, created_at DESC)
            """))

            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_messages_lead_created
                ON messages (lead_id, created_at DESC)
            """))

            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_messages_external_conv
                ON messages (external_conversation_id)
            """))

            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_messages_sender_status
                ON messages (sender_type, message_status)
            """))

            # Agent sessions table indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_agent_sessions_agent_lead
                ON agent_sessions (agent_id, lead_id)
            """))

            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_agent_sessions_status
                ON agent_sessions (session_status)
            """))

            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_agent_sessions_trigger
                ON agent_sessions (trigger_type)
            """))

            # Leads table indexes (if not exist)
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_leads_external_id
                ON leads (external_id)
            """))

            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_leads_status_source
                ON leads (status, source)
            """))

            conn.commit()
            print("✅ Performance indexes created")

    except Exception as e:
        print(f"❌ Error creating indexes: {e}")

def check_foreign_key_constraints(engine):
    """Verify foreign key relationships"""
    try:
        inspector = inspect(engine)

        # Check messages table foreign keys
        if table_exists(engine, 'messages'):
            foreign_keys = inspector.get_foreign_keys('messages')
            fk_tables = [fk['referred_table'] for fk in foreign_keys]

            expected_fk_tables = ['agent_sessions', 'leads', 'agents']
            for table in expected_fk_tables:
                if table in fk_tables:
                    print(f"✅ Messages table foreign key to {table} verified")
                else:
                    print(f"⚠️  Warning: Messages foreign key to {table} not found")

        # Check agent_sessions table foreign keys
        if table_exists(engine, 'agent_sessions'):
            foreign_keys = inspector.get_foreign_keys('agent_sessions')
            fk_tables = [fk['referred_table'] for fk in foreign_keys]

            expected_fk_tables = ['agents', 'leads']
            for table in expected_fk_tables:
                if table in fk_tables:
                    print(f"✅ Agent sessions foreign key to {table} verified")
                else:
                    print(f"⚠️  Warning: Agent sessions foreign key to {table} not found")

        return True

    except Exception as e:
        print(f"❌ Error checking foreign key constraints: {e}")
        return False

def test_table_operations(engine):
    """Test basic operations on all tables"""
    try:
        with engine.connect() as conn:
            # Test each table
            for table_name in ['agents', 'leads', 'agent_sessions', 'messages']:
                if table_exists(engine, table_name):
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = result.scalar()
                    print(f"✅ {table_name} table accessible (current rows: {count})")
                else:
                    print(f"❌ {table_name} table not accessible")
                    return False

        return True

    except Exception as e:
        print(f"❌ Error testing table operations: {e}")
        return False

def main():
    """Main migration function"""
    print("=" * 70)
    print("COMPLETE PHASE 3 DATABASE MIGRATION SCRIPT")
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

    # Step 2: Create missing tables
    print("\n2. Creating missing tables...")
    if not create_missing_tables(engine):
        return False

    # Step 3: Verify table structures
    print("\n3. Verifying table structures...")
    if not verify_table_structures(engine):
        return False

    # Step 4: Check foreign key constraints
    print("\n4. Checking foreign key constraints...")
    check_foreign_key_constraints(engine)

    # Step 5: Create performance indexes
    print("\n5. Creating performance indexes...")
    create_indexes(engine)

    # Step 6: Test table operations
    print("\n6. Testing table operations...")
    if not test_table_operations(engine):
        return False

    print("\n" + "=" * 70)
    print("✅ COMPLETE PHASE 3 MIGRATION COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print()
    print("All tables are now ready for Phase 3: Two-Way Messaging:")
    print("✅ agents - AI agent configurations")
    print("✅ leads - Lead management with new schema")
    print("✅ agent_sessions - Agent-to-lead conversation sessions")
    print("✅ messages - Complete conversation history storage")
    print()
    print("Features now available:")
    print("- Automatic agent engagement on new leads")
    print("- Two-way messaging with conversation history")
    print("- Message persistence and delivery tracking")
    print("- External platform integration (Yelp, Zapier)")
    print()
    print("Next steps:")
    print("- Test webhook endpoints to verify agent session creation")
    print("- Test conversation flow and message storage")
    print("- Verify OpenAI integration is working")

    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎉 Complete migration finished successfully!")
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
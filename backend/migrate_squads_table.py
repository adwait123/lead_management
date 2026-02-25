#!/usr/bin/env python3
"""
Database Migration Script for Multi-Agent Squad Orchestration
Creates the squads table and adds squad_id FK to agents table
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text, inspect

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import DATABASE_URL, Base
from models.squad import Squad
from models.agent import Agent


def check_database_connection(engine):
    """Test database connectivity"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("  Database connection successful")
        return True
    except Exception as e:
        print(f"  Database connection failed: {e}")
        return False


def table_exists(engine, table_name):
    """Check if a table exists in the database"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def column_exists(engine, table_name, column_name):
    """Check if a column exists in a table"""
    inspector = inspect(engine)
    if not table_exists(engine, table_name):
        return False
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def create_squads_table(engine):
    """Create the squads table"""
    try:
        if table_exists(engine, 'squads'):
            print("  squads table already exists")
            return True

        print("  Creating squads table...")
        Squad.__table__.create(engine, checkfirst=True)
        print("  squads table created successfully")
        return True

    except Exception as e:
        print(f"  Failed to create squads table: {e}")
        return False


def add_squad_id_to_agents(engine):
    """Add squad_id column to agents table"""
    try:
        if column_exists(engine, 'agents', 'squad_id'):
            print("  agents.squad_id column already exists")
            return True

        print("  Adding squad_id column to agents table...")
        with engine.connect() as conn:
            conn.execute(text(
                "ALTER TABLE agents ADD COLUMN squad_id INTEGER REFERENCES squads(id)"
            ))
            conn.commit()
        print("  agents.squad_id column added successfully")
        return True

    except Exception as e:
        print(f"  Failed to add squad_id to agents: {e}")
        return False


def create_indexes(engine):
    """Create performance indexes"""
    try:
        with engine.connect() as conn:
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_squads_is_active ON squads (is_active)"
            ))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_agents_squad_id ON agents (squad_id)"
            ))
            conn.commit()
        print("  Indexes created")
    except Exception as e:
        print(f"  Error creating indexes: {e}")


def verify_migration(engine):
    """Verify migration was successful"""
    try:
        ok = True
        if not table_exists(engine, 'squads'):
            print("  Missing squads table")
            ok = False
        else:
            inspector = inspect(engine)
            cols = [c['name'] for c in inspector.get_columns('squads')]
            expected = ['id', 'name', 'description', 'is_active', 'agents',
                        'routing_config', 'shared_context_schema', 'entry_agent_key',
                        'created_at', 'updated_at']
            missing = [c for c in expected if c not in cols]
            if missing:
                print(f"  Missing columns in squads: {missing}")
                ok = False
            else:
                print(f"  squads table verified ({len(cols)} columns)")

        if not column_exists(engine, 'agents', 'squad_id'):
            print("  Missing agents.squad_id column")
            ok = False
        else:
            print("  agents.squad_id column verified")

        return ok
    except Exception as e:
        print(f"  Verification error: {e}")
        return False


def main():
    print("=" * 60)
    print("MULTI-AGENT SQUAD ORCHESTRATION — DATABASE MIGRATION")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    engine = create_engine(DATABASE_URL)

    print("1. Testing database connection...")
    if not check_database_connection(engine):
        return False

    print("\n2. Creating squads table...")
    if not create_squads_table(engine):
        return False

    print("\n3. Adding squad_id to agents table...")
    if not add_squad_id_to_agents(engine):
        return False

    print("\n4. Creating indexes...")
    create_indexes(engine)

    print("\n5. Verifying migration...")
    if not verify_migration(engine):
        return False

    print("\n" + "=" * 60)
    print("SQUAD MIGRATION COMPLETED SUCCESSFULLY")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  python create_demo_squad.py   — seed the Torkin Pest Control squad")
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nMigration interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)

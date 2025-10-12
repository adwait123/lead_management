#!/usr/bin/env python3
"""
Health check script for staging deployment
"""
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_database_connection():
    """Test database connection"""
    try:
        from models.database import get_db, engine

        # Test engine connection
        with engine.connect() as conn:
            result = conn.execute("SELECT 1 as test")
            test_value = result.scalar()
            print(f"✅ Database connection successful (test query: {test_value})")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False

def check_tables_exist():
    """Check if required tables exist"""
    try:
        from sqlalchemy import inspect
        from models.database import engine

        inspector = inspect(engine)
        tables = inspector.get_table_names()

        required_tables = ['agents', 'leads', 'agent_sessions', 'follow_up_tasks', 'messages']

        print(f"\n📋 Database Tables Check:")
        print(f"   Found {len(tables)} tables: {tables}")

        missing_tables = []
        for table in required_tables:
            if table in tables:
                print(f"   ✅ {table}")
            else:
                print(f"   ❌ {table} (missing)")
                missing_tables.append(table)

        if missing_tables:
            print(f"\n⚠️  Missing tables: {missing_tables}")
            print("   Run database migrations first!")
            return False

        return True

    except Exception as e:
        print(f"❌ Error checking tables: {str(e)}")
        return False

def check_agent_table_structure():
    """Check agent table structure"""
    try:
        from sqlalchemy import inspect
        from models.database import engine

        inspector = inspect(engine)
        columns = inspector.get_columns('agents')
        column_names = [col['name'] for col in columns]

        print(f"\n📋 Agents Table Structure:")
        print(f"   Columns ({len(column_names)}): {column_names}")

        required_columns = ['id', 'name', 'prompt_template', 'workflow_steps', 'triggers']
        missing_columns = [col for col in required_columns if col not in column_names]

        if missing_columns:
            print(f"   ⚠️  Missing columns: {missing_columns}")
            return False

        print(f"   ✅ All required columns present")
        return True

    except Exception as e:
        print(f"❌ Error checking agent table: {str(e)}")
        return False

def test_agent_query():
    """Test basic agent queries"""
    try:
        from models.database import get_db
        from models.agent import Agent

        db = next(get_db())

        # Count agents
        agent_count = db.query(Agent).count()
        print(f"\n🤖 Agent Data:")
        print(f"   Total agents: {agent_count}")

        if agent_count > 0:
            # Get first agent
            first_agent = db.query(Agent).first()
            print(f"   First agent: {first_agent.name} (ID: {first_agent.id})")

            # Check for workflow steps
            workflow_count = len(first_agent.workflow_steps) if first_agent.workflow_steps else 0
            print(f"   Workflow steps: {workflow_count}")

        db.close()
        return True

    except Exception as e:
        print(f"❌ Error testing agent queries: {str(e)}")
        return False

def test_pydantic_schemas():
    """Test Pydantic schema validation"""
    try:
        from models.schemas import AgentResponseSchema
        from models.agent import Agent
        from models.database import get_db

        print(f"\n📝 Pydantic Schema Test:")
        print(f"   AgentResponseSchema available: {AgentResponseSchema is not None}")
        print(f"   Has model_validate: {hasattr(AgentResponseSchema, 'model_validate')}")
        print(f"   Has from_orm: {hasattr(AgentResponseSchema, 'from_orm')}")

        # Test with real agent if available
        db = next(get_db())
        agent = db.query(Agent).first()

        if agent:
            try:
                result = AgentResponseSchema.model_validate(agent)
                print(f"   ✅ model_validate works: {type(result)}")
            except Exception as e:
                print(f"   ❌ model_validate failed: {str(e)}")
        else:
            print(f"   ⚠️  No agents available for testing")

        db.close()
        return True

    except Exception as e:
        print(f"❌ Error testing Pydantic schemas: {str(e)}")
        return False

def main():
    """Main health check function"""
    print("="*70)
    print("🏥 STAGING HEALTH CHECK")
    print("="*70)

    checks = [
        ("Database Connection", check_database_connection),
        ("Tables Exist", check_tables_exist),
        ("Agent Table Structure", check_agent_table_structure),
        ("Agent Queries", test_agent_query),
        ("Pydantic Schemas", test_pydantic_schemas)
    ]

    results = []
    for check_name, check_func in checks:
        print(f"\n🔍 {check_name}...")
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name} failed with exception: {str(e)}")
            results.append((check_name, False))

    print("\n" + "="*70)
    print("📊 HEALTH CHECK SUMMARY")
    print("="*70)

    passed = 0
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {check_name}")
        if result:
            passed += 1

    print(f"\n🎯 Overall: {passed}/{len(results)} checks passed")

    if passed == len(results):
        print("🎉 All checks passed! System is healthy.")
    else:
        print("⚠️  Some checks failed. Review the issues above.")

    return passed == len(results)

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 Health check crashed: {str(e)}")
        sys.exit(1)
#!/usr/bin/env python3
"""
Test script to verify Pydantic model_validate works with SQLAlchemy models
"""
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import get_db, create_tables
from models.agent import Agent
from models.schemas import AgentResponseSchema
from sqlalchemy.orm import Session

def test_pydantic_model_validate():
    """Test that model_validate works with our SQLAlchemy models"""
    print("🧪 Testing Pydantic model_validate with SQLAlchemy models")

    # Create tables
    create_tables()

    # Get a database session
    db_gen = get_db()
    db = next(db_gen)

    try:
        # Get an existing agent or create a test one
        agent = db.query(Agent).first()

        if not agent:
            print("   No agents found, creating a test agent...")
            agent = Agent(
                name="Test Agent",
                description="Test agent for Pydantic validation",
                type="text",
                use_case="general_sales",
                prompt_template="You are a helpful assistant.",
                model="gpt-3.5-turbo",
                temperature="0.7",
                max_tokens=500,
                is_active=True
            )
            db.add(agent)
            db.commit()
            db.refresh(agent)
            print(f"   Created test agent with ID: {agent.id}")
        else:
            print(f"   Using existing agent with ID: {agent.id}")

        # Test the old method (from_orm) - this should fail in Pydantic v2
        print("\n📝 Testing from_orm (should fail)...")
        try:
            result_old = AgentResponseSchema.from_orm(agent)
            print(f"   ❌ from_orm worked unexpectedly: {type(result_old)}")
        except Exception as e:
            print(f"   ✅ from_orm failed as expected: {str(e)[:100]}...")

        # Test the new method (model_validate) - this should work
        print("\n📝 Testing model_validate (should work)...")
        try:
            result_new = AgentResponseSchema.model_validate(agent)
            print(f"   ✅ model_validate worked: {type(result_new)}")
            print(f"   Agent name: {result_new.name}")
            print(f"   Agent ID: {result_new.id}")
            print(f"   Agent type: {result_new.type}")

            # Test that it can be serialized to dict/JSON
            agent_dict = result_new.model_dump()
            print(f"   ✅ Serialization works, keys: {list(agent_dict.keys())[:5]}...")

            return True

        except Exception as e:
            print(f"   ❌ model_validate failed: {str(e)}")
            return False

    except Exception as e:
        print(f"❌ Test setup failed: {str(e)}")
        return False
    finally:
        db.close()

def test_agent_sessions():
    """Test model_validate with AgentSession models"""
    print("\n🧪 Testing AgentSession model_validate")

    from models.agent_session import AgentSession
    from models.schemas import AgentSessionResponseSchema

    # Get a database session
    db_gen = get_db()
    db = next(db_gen)

    try:
        # Get an existing session
        session = db.query(AgentSession).first()

        if not session:
            print("   No agent sessions found, skipping test")
            return True

        print(f"   Using session with ID: {session.id}")

        # Test model_validate with AgentSession
        try:
            result = AgentSessionResponseSchema.model_validate(session)
            print(f"   ✅ AgentSession model_validate worked: {result.id}")
            return True
        except Exception as e:
            print(f"   ❌ AgentSession model_validate failed: {str(e)}")
            return False

    except Exception as e:
        print(f"❌ AgentSession test failed: {str(e)}")
        return False
    finally:
        db.close()

def main():
    """Run all tests"""
    print("=" * 70)
    print("PYDANTIC MODEL_VALIDATE COMPATIBILITY TEST")
    print("=" * 70)

    # Test Agent model
    agent_test = test_pydantic_model_validate()

    # Test AgentSession model
    session_test = test_agent_sessions()

    print("\n" + "=" * 70)
    print("TEST RESULTS")
    print("=" * 70)
    print(f"Agent model_validate: {'✅ PASS' if agent_test else '❌ FAIL'}")
    print(f"AgentSession model_validate: {'✅ PASS' if session_test else '❌ FAIL'}")

    if agent_test and session_test:
        print("\n🎉 All tests passed! It's safe to replace from_orm with model_validate")
        return True
    else:
        print("\n⚠️ Some tests failed! Review before making changes")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
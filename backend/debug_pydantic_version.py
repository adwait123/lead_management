#!/usr/bin/env python3
"""
Debug script to check Pydantic version and schema configuration
"""
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_pydantic_version():
    """Check Pydantic version"""
    try:
        import pydantic
        print(f"✅ Pydantic version: {pydantic.VERSION}")
        print(f"   Pydantic location: {pydantic.__file__}")
        return pydantic.VERSION
    except ImportError:
        print("❌ Pydantic not installed")
        return None

def check_schema_configuration():
    """Check if schemas have from_attributes configuration"""
    try:
        from models.schemas import AgentResponseSchema

        print(f"\n📋 AgentResponseSchema configuration:")
        print(f"   Class: {AgentResponseSchema}")
        print(f"   Has model_validate: {hasattr(AgentResponseSchema, 'model_validate')}")
        print(f"   Has from_orm: {hasattr(AgentResponseSchema, 'from_orm')}")

        # Check Config class
        if hasattr(AgentResponseSchema, 'model_config'):
            print(f"   model_config: {AgentResponseSchema.model_config}")
        elif hasattr(AgentResponseSchema, 'Config'):
            config = AgentResponseSchema.Config
            print(f"   Config class: {config}")
            if hasattr(config, 'from_attributes'):
                print(f"   from_attributes: {config.from_attributes}")
            if hasattr(config, 'orm_mode'):
                print(f"   orm_mode: {config.orm_mode}")
        else:
            print("   ❌ No Config found")

        return True
    except Exception as e:
        print(f"❌ Error checking schema: {str(e)}")
        return False

def test_schema_methods():
    """Test if we can create a schema instance"""
    try:
        from models.schemas import AgentResponseSchema
        from models.agent import Agent
        from models.database import get_db

        # Get a test agent
        db = next(get_db())
        agent = db.query(Agent).first()

        if not agent:
            print("⚠️  No agents found in database for testing")
            return False

        print(f"\n🧪 Testing schema methods with agent ID {agent.id}:")

        # Test model_validate
        try:
            result = AgentResponseSchema.model_validate(agent)
            print(f"   ✅ model_validate works: {type(result)}")
        except Exception as e:
            print(f"   ❌ model_validate failed: {str(e)}")

        # Test from_orm (should fail in Pydantic v2)
        try:
            result = AgentResponseSchema.from_orm(agent)
            print(f"   ⚠️  from_orm works (unexpected): {type(result)}")
        except Exception as e:
            print(f"   ✅ from_orm failed as expected: {str(e)[:100]}...")

        db.close()
        return True

    except Exception as e:
        print(f"❌ Error testing schema methods: {str(e)}")
        return False

def check_git_status():
    """Check git commit info"""
    try:
        import subprocess

        # Get current commit hash
        result = subprocess.run(['git', 'rev-parse', 'HEAD'],
                              capture_output=True, text=True, cwd=os.path.dirname(__file__))
        if result.returncode == 0:
            commit_hash = result.stdout.strip()
            print(f"\n📝 Git Information:")
            print(f"   Current commit: {commit_hash[:8]}")

            # Get commit message
            result = subprocess.run(['git', 'log', '-1', '--oneline'],
                                  capture_output=True, text=True, cwd=os.path.dirname(__file__))
            if result.returncode == 0:
                print(f"   Last commit: {result.stdout.strip()}")

        return True
    except Exception as e:
        print(f"❌ Error checking git status: {str(e)}")
        return False

def main():
    """Main debug function"""
    print("="*70)
    print("🔍 PYDANTIC VERSION & SCHEMA DEBUG")
    print("="*70)

    # Check Pydantic version
    version = check_pydantic_version()

    # Check git status
    check_git_status()

    # Check schema configuration
    schema_ok = check_schema_configuration()

    # Test schema methods
    if schema_ok:
        test_schema_methods()

    print("\n" + "="*70)

    if version and version >= "2.0.0":
        print("✅ Pydantic v2 detected - should use model_validate")
    else:
        print("⚠️  Pydantic v1 detected - should use from_orm")

    print("="*70)

if __name__ == "__main__":
    main()
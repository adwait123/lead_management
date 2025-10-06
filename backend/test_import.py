#!/usr/bin/env python3
"""
Simple test script to verify all imports work correctly
"""

print("Testing imports...")

try:
    print("1. Testing basic imports...")
    import uvicorn
    import fastapi
    import sqlalchemy
    import pydantic
    import openai
    print("✅ Basic imports successful")

    print("2. Testing FastAPI creation...")
    from fastapi import FastAPI
    app = FastAPI()
    print("✅ FastAPI creation successful")

    print("3. Testing database models...")
    from models.database import Base, engine
    print("✅ Database models import successful")

    print("4. Testing schemas...")
    from models.schemas import LeadCreateSchema
    print("✅ Schemas import successful")

    print("\n🎉 All imports successful! Ready for deployment.")

except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
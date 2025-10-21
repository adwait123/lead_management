#!/usr/bin/env python3
"""
Start the FastAPI server for local testing
"""

import uvicorn
import os
import sys
from pathlib import Path

def main():
    """Start the server with proper configuration"""

    # Ensure we're in the right directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)

    print("🚀 Starting FastAPI server for inbound webhook testing...")
    print(f"📂 Working directory: {os.getcwd()}")
    print(f"🌐 Server will be available at: http://localhost:8000")
    print(f"📋 API docs at: http://localhost:8000/docs")
    print(f"🔗 Webhook endpoint: http://localhost:8000/api/inbound-calls/webhooks/twilio")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)

    try:
        # Run the server
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

if __name__ == "__main__":
    main()
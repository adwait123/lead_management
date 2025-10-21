#!/usr/bin/env python3
"""
Complete setup and test script for inbound calling functionality
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path

def setup_environment():
    """Set up the environment for testing"""
    print("🔧 Setting up test environment...")

    # Ensure we're in the right directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)

    # Create inbound agent if needed
    print("🤖 Creating inbound agent...")
    try:
        result = subprocess.run([sys.executable, "create_inbound_agent.py"],
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ Inbound agent setup complete")
        else:
            print(f"⚠️  Inbound agent setup warning: {result.stderr}")
    except Exception as e:
        print(f"❌ Error setting up inbound agent: {str(e)}")

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting FastAPI server...")

    try:
        # Start server in background
        server_process = subprocess.Popen(
            [sys.executable, "start_test_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Wait a bit for server to start
        print("⏳ Waiting for server to start...")
        time.sleep(5)

        # Check if server is running
        if server_process.poll() is None:
            print("✅ Server started successfully")
            return server_process
        else:
            stdout, stderr = server_process.communicate()
            print(f"❌ Server failed to start: {stderr}")
            return None

    except Exception as e:
        print(f"❌ Error starting server: {str(e)}")
        return None

def run_tests():
    """Run the comprehensive tests"""
    print("🧪 Running comprehensive tests...")

    try:
        result = subprocess.run([sys.executable, "test_inbound_webhook.py"],
                              capture_output=True, text=True, timeout=60)

        print("📊 TEST RESULTS:")
        print("=" * 60)
        print(result.stdout)

        if result.stderr:
            print("⚠️  WARNINGS/ERRORS:")
            print(result.stderr)

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("❌ Tests timed out after 60 seconds")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {str(e)}")
        return False

def cleanup(server_process):
    """Clean up resources"""
    print("\n🧹 Cleaning up...")

    if server_process and server_process.poll() is None:
        print("🛑 Stopping server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=10)
            print("✅ Server stopped gracefully")
        except subprocess.TimeoutExpired:
            print("⚠️  Force killing server...")
            server_process.kill()

def main():
    """Main test execution"""
    print("🚀 Inbound Calling Setup and Test Suite")
    print("=" * 60)

    server_process = None

    try:
        # Step 1: Setup environment
        setup_environment()

        # Step 2: Start server
        server_process = start_server()
        if not server_process:
            print("❌ Cannot proceed without server")
            return False

        # Step 3: Run tests
        test_success = run_tests()

        # Step 4: Report results
        print("\n" + "=" * 60)
        if test_success:
            print("🎉 ALL TESTS PASSED!")
            print("✅ Inbound calling webhook is ready for production deployment")
            print("\n💡 Next steps:")
            print("   1. Deploy to Render")
            print("   2. Update Twilio webhook URL")
            print("   3. Test with real phone calls")
        else:
            print("⚠️  SOME TESTS FAILED")
            print("🔍 Check the test output above for specific issues")
            print("💡 Common fixes:")
            print("   - Ensure database is properly set up")
            print("   - Check that all dependencies are installed")
            print("   - Verify agent configuration")

        return test_success

    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return False
    finally:
        cleanup(server_process)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
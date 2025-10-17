# backend/download_models.py
import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add agent src to path
agent_path = os.path.join(os.path.dirname(__file__), "agent", "src")
sys.path.insert(0, agent_path)

try:
    from agent import entrypoint
    from livekit import agents

    logger.info("Downloading required models...")
    # The download-files command is part of the CLI runner
    agents.cli.run_app(
        agents.WorkerOptions(entrypoint_fnc=entrypoint),
        cli_args=["download-files"],
    )
    logger.info("Models downloaded successfully.")

except Exception as e:
    logger.error(f"Failed to download models: {str(e)}")
    # Exit with a non-zero code to fail the build
    sys.exit(1)

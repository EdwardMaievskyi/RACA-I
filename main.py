import logging
import sys
from dotenv import load_dotenv

load_dotenv()

from ui.gradio_app import launch_app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the web interface."""
    try:
        logger.info("Launching Gradio app...")
        launch_app()
    except KeyboardInterrupt:
        logger.critical("Keyboard interrupt detected. Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Error starting the application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

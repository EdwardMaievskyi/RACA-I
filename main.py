import os
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"

from ui.gradio_app import launch_app


def main():
    """Main entry point for the web interface."""
    print("🤖 AI Code Generator - Web Interface")
    print("=" * 50)

    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable is not set!")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        sys.exit(1)

    try:
        launch_app()
    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")
    except Exception as e:
        print(f"❌ Error starting the application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

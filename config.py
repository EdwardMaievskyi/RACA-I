import os
from dotenv import load_dotenv

load_dotenv()

PRIMARY_MODEL_NAME = os.getenv("PRIMARY_MODEL_NAME")
MAX_RETRY_ITERATIONS = int(os.getenv("MAX_RETRY_ITERATIONS"))
MAX_CODE_TIMEOUT = int(os.getenv("MAX_CODE_TIMEOUT"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# E2B Configuration
E2B_API_KEY = os.getenv("E2B_API_KEY")
E2B_TEMPLATE_ID = os.getenv("E2B_TEMPLATE_ID", "base")
ALLOW_LOCAL_EXECUTION = os.getenv("ALLOW_LOCAL_EXECUTION") == 'true'

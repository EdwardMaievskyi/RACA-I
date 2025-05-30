import os
from dotenv import load_dotenv

load_dotenv()

PRIMARY_MODEL_NAME = os.getenv("PRIMARY_MODEL_NAME")
MAX_RETRY_ITERATIONS = int(os.getenv("MAX_RETRY_ITERATIONS"))
MAX_CODE_TIMEOUT = int(os.getenv("MAX_CODE_TIMEOUT"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

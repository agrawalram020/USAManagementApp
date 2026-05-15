import os
from dotenv import load_dotenv

load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://usa_user:unity77@localhost:5432/usa_db"
)

ORCHESTRATOR_MODEL = "mistral-large-latest"
SUBAGENT_MODEL = "mistral-small-latest"

ORCHESTRATOR_MAX_TOKENS = 8192
SUBAGENT_MAX_TOKENS = 4096
STRATEGY_PLANNER_MAX_TOKENS = 16384

MAX_ITERATIONS = 10
APP_ROOT_PATH = os.getenv("APP_ROOT_PATH", "").rstrip("/")

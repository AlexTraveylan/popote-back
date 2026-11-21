import os

os.environ["SEED_ON_STARTUP"] = "false"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["OPENAI_API_KEY"] = ""

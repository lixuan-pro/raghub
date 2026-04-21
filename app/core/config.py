import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    app_name: str = os.getenv("APP_NAME", "RAGHub")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")


settings = Settings()
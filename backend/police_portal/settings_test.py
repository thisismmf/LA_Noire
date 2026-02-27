from .settings import *  # noqa: F401,F403
import os

# Override DB host/port for local pytest runs (connect to dockerized Postgres via localhost)
DATABASES["default"]["HOST"] = os.environ.get("POSTGRES_HOST", "localhost")
DATABASES["default"]["PORT"] = os.environ.get("POSTGRES_PORT", "5433")

PAYMENT_GATEWAY_PROVIDER = "mock"
PAYMENT_CALLBACK_BASE_URL = os.environ.get("PAYMENT_CALLBACK_BASE_URL", "http://localhost:8000")

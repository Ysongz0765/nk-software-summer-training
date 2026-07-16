from __future__ import annotations

import os

if os.environ.get("RUN_MYSQL_INTEGRATION_TESTS") != "1":
    os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DEBUG", "false")

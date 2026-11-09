"""FIX-STATE config.py - secrets read from the environment, none hardcoded."""

import os

API_KEY = os.environ.get("API_KEY")
DB_PASSWORD = os.environ.get("DB_PASSWORD")

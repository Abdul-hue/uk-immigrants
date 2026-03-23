"""Database connection and migrations for UK Immigration Eligibility Platform."""

import os
from pathlib import Path

from dotenv import load_dotenv
import psycopg2

load_dotenv()


def get_connection():
    """Return a psycopg2 connection using DATABASE_URL."""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL environment variable is not set")
    return psycopg2.connect(url)


def run_migrations():
    """Read and execute schema.sql."""
    schema_path = Path(__file__).parent / "schema.sql"
    with open(schema_path, encoding="utf-8") as f:
        schema_sql = f.read()

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(schema_sql)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    run_migrations()
    print("Schema deployed successfully")

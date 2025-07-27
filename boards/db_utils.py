import psycopg2
import psycopg2.extras
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Optional: change to pull from config
DEFAULT_DB_CONFIG = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': 'password',
    'host': 'localhost',
    'port': 5432
}

@contextmanager
def get_connection(db_config=DEFAULT_DB_CONFIG):
    """Context manager for PostgreSQL connection."""
    conn = psycopg2.connect(**db_config)
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.exception("Database operation failed.")
        raise
    finally:
        conn.close()

def create_table_if_not_exists(conn):
    """Create the hash-link cache table if it doesn't exist."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS image_cache (
                hash TEXT PRIMARY KEY,
                url TEXT NOT NULL
            )
        """)
        logger.info("Ensured image_cache table exists.")

def insert_hash_url(conn, hash_value, url):
    """Insert hash-URL pair into the cache table."""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO image_cache (hash, url)
            VALUES (%s, %s)
            ON CONFLICT (hash) DO NOTHING
        """, (hash_value, url))
        logger.debug(f"Inserted or skipped: {hash_value} -> {url}")

def get_url_by_hash(conn, hash_value):
    """Retrieve cached URL by image hash."""
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("SELECT url FROM image_cache WHERE hash = %s", (hash_value,))
        row = cur.fetchone()
        return row['url'] if row else None

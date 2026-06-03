import psycopg2
from psycopg2.extras import execute_values

from dotenv import load_dotenv
import os

load_dotenv()

AIVEN_DB = {
    "host": os.getenv("AIVEN_HOST"),
    "port": int(os.getenv("AIVEN_PORT", "5432")),
    "dbname": os.getenv("AIVEN_DBNAME", "defaultdb"),
    "user": os.getenv("AIVEN_USER"),
    "password": os.getenv("AIVEN_PASSWORD"),
    "sslmode": os.getenv("AIVEN_SSLMODE", "require"),
}

LOCAL_DB = {
    "host": "localhost",
    "port": 5432,
    "dbname": "boards",
    "user": "postgres",
    "password": "password",
}


def connect_local():
    return psycopg2.connect(**LOCAL_DB)


def connect_aiven():
    return psycopg2.connect(**AIVEN_DB)


def create_table_if_not_exists(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS public.image_cache (
            hash TEXT PRIMARY KEY,
            link TEXT NOT NULL,
            filename TEXT
        )
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_image_cache_filename
        ON public.image_cache(filename)
    """)


def main():
    local_conn = connect_local()
    remote_conn = connect_aiven()

    try:
        local_cur = local_conn.cursor()
        remote_cur = remote_conn.cursor()

        create_table_if_not_exists(remote_cur)

        print("Reading local rows...")

        local_cur.execute("""
            SELECT hash, link, filename
            FROM public.image_cache
        """)

        rows = local_cur.fetchall()

        print(f"Found {len(rows)} rows.")

        if not rows:
            return

        print("Upserting into Aiven...")

        execute_values(
            remote_cur,
            """
            INSERT INTO public.image_cache (
                hash,
                link,
                filename
            )
            VALUES %s
            ON CONFLICT (hash)
            DO UPDATE SET
                link = EXCLUDED.link,
                filename = COALESCE(
                    public.image_cache.filename,
                    EXCLUDED.filename
                )
            """,
            rows,
            page_size=1000,
        )

        remote_conn.commit()

        print(f"Successfully synced {len(rows)} rows.")

    finally:
        local_conn.close()
        remote_conn.close()


if __name__ == "__main__":
    main()
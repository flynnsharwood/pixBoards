import logging

logger = logging.getLogger(__name__)


class DatabaseUnavailable(Exception):
    pass


def create_conn(config):
    # imported here so psycopg2 is only needed when a DB feature is used
    try:
        import psycopg2
    except ImportError:
        raise DatabaseUnavailable(
            "psycopg2 is not installed; install the upload extra: pip install 'pixboards[upload]'"
        ) from None

    kwargs = dict(
        dbname=config["dbname"],
        user=config["user"],
        password=config["password"],
        host=config["host"],
        port=config.get("server_port", 5432),
    )
    if config.get("sslmode"):
        kwargs["sslmode"] = config["sslmode"]
    try:
        return psycopg2.connect(**kwargs)
    except psycopg2.Error as e:
        raise DatabaseUnavailable(f"could not connect to {config['host']}: {e}") from e


def create_boards_table(conn):
    with conn.cursor() as cur:
        cur.execute(
            """CREATE TABLE IF NOT EXISTS savedBoards (
                   id SERIAL PRIMARY KEY,
                   title TEXT,
                   output_path TEXT,
                   subfolders TEXT[],
                   num_images INTEGER,
                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
               )"""
        )
    conn.commit()


def save_boards(conn, boards):
    """One row per board, in a single transaction."""
    try:
        with conn.cursor() as cur:
            cur.executemany(
                """INSERT INTO savedBoards (title, output_path, subfolders, num_images)
                   VALUES (%s, %s, %s, %s)""",
                [
                    (b.name, b.output_dir, [c.name for c in b.nested_boards], b.no_of_imgs)
                    for b in boards
                ],
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    logger.info(f"saved {len(boards)} boards")

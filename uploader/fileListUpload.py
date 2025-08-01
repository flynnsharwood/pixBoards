import hashlib
import logging
import os
import time

import psycopg2
import requests
from dotenv import load_dotenv


# --- Logging ---
log_file_path = os.path.join(os.path.dirname(__file__), "upload.log")
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# --- Load API Key ---
load_dotenv()
IMG_CHEST_API_KEY = os.getenv("IMG_CHEST_API_KEY")
HEADERS = {"Authorization": f"Bearer {IMG_CHEST_API_KEY}"}


LIST_FILE_PATH = input('location file with links\n') or 'MediaFiles.txt'


def connect_db():
    return psycopg2.connect(
        dbname="boards",
        user="postgres",
        password="password",
        host="localhost",
    )


def create_table_if_not_exists(cursor):
    logger.info("[DB] Ensuring image_cache table exists...")
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS image_cache (
            hash TEXT PRIMARY KEY,
            link TEXT NOT NULL
        )
    """
    )


def compute_hash(image_path):
    logger.info(f"[HASH] Computing hash for: {image_path}")
    with open(image_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def load_link_by_hash(cursor, hash_val):
    cursor.execute("SELECT link FROM image_cache WHERE hash = %s", (hash_val,))
    row = cursor.fetchone()
    if row:
        logger.info(f"[CACHE HIT] Found link for hash {hash_val}")
    else:
        logger.info(f"[CACHE MISS] No link found for hash {hash_val}")
    return row[0] if row else None


def save_link(cursor, hash_val, link):
    cursor.execute(
        """
        INSERT INTO image_cache (hash, link)
        VALUES (%s, %s)
        ON CONFLICT (hash) DO NOTHING
    """,
        (hash_val, link),
    )
    logger.info(f"[CACHE SAVE] {hash_val} → {link}")


def upload_images(image_paths):
    logger.info(f"[UPLOAD] Uploading {len(image_paths)} image(s)...")
    files = []
    for image_path in image_paths:
        with open(image_path, "rb") as f:
            filename = os.path.basename(image_path)
            files.append(("images[]", (filename, f.read(), "image/jpeg")))

    data = {"title": os.path.basename(image_paths[0])}
    resp = requests.post(
        "https://api.imgchest.com/v1/post",
        headers=HEADERS,
        files=files,
        data=data,
    )
    resp.raise_for_status()

    post_id = resp.json()["data"]["id"]
    info = requests.get(f"https://api.imgchest.com/v1/post/{post_id}", headers=HEADERS)
    info.raise_for_status()

    image_list = info.json()["data"]["images"]
    if not image_list or len(image_list) != len(image_paths):
        raise Exception("Mismatch in uploaded image count")

    for path, img in zip(image_paths, image_list):
        logger.info(f"[SUCCESS] {path} → {img['link']}")
    return [img["link"] for img in image_list]


def chunked(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


def read_file_list(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    if not lines or not lines[0].startswith("#"):
        raise Exception("First line of file must start with '#' and contain index")
    current_index = int(lines[0][1:].strip())
    file_paths = [line.strip() for line in lines[1:] if line.strip()]
    return current_index, file_paths


def write_updated_index(index):
    with open(LIST_FILE_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()
    with open(LIST_FILE_PATH, "w", encoding="utf-8") as f:
        f.write(f"#{index}\n")
        f.writelines(lines[1:])
    logger.info(f"[INDEX] Updated to #{index}")


def upload_all():
    conn = connect_db()
    cur = conn.cursor()
    create_table_if_not_exists(cur)

    index, file_paths = read_file_list(LIST_FILE_PATH)
    index_original = index

    logger.info(f"[START] Uploading from index {index} of {len(file_paths)}")
    remaining_files = file_paths[index:]

    uncached = [path for path in remaining_files if os.path.exists(path)]
    skipped = len(remaining_files) - len(uncached)
    if skipped:
        logger.warning(f"[SKIP] {skipped} file(s) not found and skipped.")

    logger.info(f"[READY] {len(uncached)} file(s) ready to upload")

    def try_upload_with_retries(paths_to_upload, retries=3, delay=2):
        for attempt in range(1, retries + 1):
            try:
                return upload_images(paths_to_upload)
            except Exception as e:
                logger.warning(f"[RETRY {attempt}] {e}")
                if attempt == retries:
                    raise
                time.sleep(delay)

    for batch in chunked(uncached, 18):
        try:
            uploaded_links = try_upload_with_retries(batch)
            for path, link in zip(batch, uploaded_links):
                hash_val = compute_hash(path)
                save_link(cur, hash_val, link)
                index += 1
                write_updated_index(index)
            conn.commit()
            logger.info("[BATCH] Upload and DB commit complete")
            time.sleep(2)
        except Exception as e:
            logger.error(f"[ERROR] Failed batch: {e}")
            break

    cur.close()
    conn.close()

    uploaded_count = index - index_original
    logger.info(f"[DONE] Uploaded {uploaded_count} file(s)")
    return uploaded_count


if __name__ == "__main__":
    start_time = time.time()
    try:
        index_before, _ = read_file_list(LIST_FILE_PATH)
        uploaded = upload_all()
        elapsed_time = time.time() - start_time
        logger.info(f"[FINISHED] Time taken: {elapsed_time:.2f} sec")
        if uploaded > 0:
            logger.info(f"[PERFORMANCE] {elapsed_time / uploaded:.2f} sec/image")
    except Exception as e:
        logger.error(f"[FATAL] {e}")

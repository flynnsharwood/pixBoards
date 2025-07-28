import os
from boards.classes import * 
from boards.create import create_index_file
from pathlib import Path


from boards.log_utils import setup_logger
logger = setup_logger(__name__)

def boardsForImglist(imgList_List, listDir, paginate):
    # Now I might need to sanitise the image list so that there aren't instances with the same name.
    # But as the imagelist files are in the same folder, they won't have the same name, so I leave this for the future me.
    os.makedirs(listDir, exist_ok=True)

    boards = []

    for idx, imgListFile in enumerate(imgList_List):
        boardName = os.path.splitext(os.path.basename(imgListFile))[0]

        with open(imgListFile, "r", encoding="utf-8") as f:
            images = [line.strip() for line in f if line.strip()]

        outputFile = os.path.join(listDir, boardName)
        print(outputFile)
               
        b = board(
            name=boardName,
            output_file_loc=outputFile + '.html',
            image_paths=images,
            paginate= paginate,
            images_per_page=42 if paginate else 10000,
        )
        b.paginate_board() # yes, paginate board no matter what. the function will take care of the situation when you don't want to paginate.
        boards.append(b)
    

    return boards


def standardBoards(directories, masterDir, paginate, upload):
    boards = []
    masterDir = Path(masterDir)
    masterDir.mkdir(parents=True, exist_ok=True)

    media_extensions = ('.jpg', '.jpeg', '.png', '.gif',
                        '.bmp', '.webp', '.mp4', '.avi', '.webm')

    for d in directories:
        # normalize to a Path
        src_dir = Path(d)

        if not src_dir.exists():
            logger.warning(f"Skipping non-existent directory: {src_dir}")
            continue

        for root, dirs, files in os.walk(src_dir):
            image_paths = []

            for fname in sorted(files):
                if fname.lower().endswith(media_extensions):
                    abs_path = Path(root) / fname
                    image_paths.append(abs_path.resolve().as_uri())

            logger.debug(f"Processing {root} with {len(image_paths)} images.")

            # skip the top‑level folder itself if you don’t want a board for it.
            # I want a board so I won't be skipping
            rel = Path(root).relative_to(os.path.dirname(src_dir))
            if str(rel) == '.':
                board_name = src_dir.name # dummy boards too
                # continue

            board_name = str(rel).replace(os.sep, "_~")
            output_path = masterDir  # everything writes into this one folder

            # create a Board object and paginate it
            b = board(
                name=board_name,
                output_file_loc=str(output_path),
                image_paths=image_paths,
                paginate=paginate,
                images_per_page=(42 if paginate else 10_000),
                upload=upload,
            )
            b.paginate_board()
            boards.append(b)

            logger.debug(f"Board created: {board_name} ({len(image_paths)} images)")

    return boards

from pathlib import Path
import os
from boards.classes import board
from boards.imgchest import process_images
from boards.log_utils import setup_logger

logger = setup_logger(__name__)

def uploadBoards(directories, masterDir, paginate, upload=True):
    """
    Walk each directory in `directories`, upload all media files to ImgChest,
    then build and paginate boards whose image_paths are the returned HTTP URLs.
    Returns a list of board objects.
    """
    boards = []
    masterDir = Path(masterDir)
    # Ensure masterDir exists once
    masterDir.mkdir(parents=True, exist_ok=True)

    media_extensions = ('.jpg', '.jpeg', '.png', '.gif',
                        '.bmp', '.webp', '.mp4', '.avi', '.webm')

    for d in directories:
        src_dir = Path(d)
        if not src_dir.exists():
            logger.warning(f"Skipping non-existent directory: {src_dir}")
            continue

        # traverse subfolders to create nested boards
        for root, dirs, files in os.walk(src_dir):
            rel = Path(root).relative_to(os.path.dirname(src_dir))
            # rel = Path(root).relative_to(src_dir)
            if rel == Path('.'):
                board_name = src_dir.name # dummy boards too
                # continue
            board_name = str(rel).replace(os.sep, "_~")

            # collect local files
            local_files = [Path(root) / f for f in sorted(files)
                           if f.lower().endswith(media_extensions)]
            if not local_files:
                logger.info(f"No media in {root}, creating empty board.")
                b = board(
                    name=board_name,
                    output_file_loc=str(masterDir),
                    image_paths=[],
                    paginate=paginate,
                    images_per_page=(42 if paginate else 10000),
                    upload=upload,
                )
                boards.append(b)
                continue

            logger.debug(f"Uploading {len(local_files)} images from {root}…")
            try:
                # upload to ImgChest, get HTTP URLs
                http_links, hash_map = process_images(local_files)
            except Exception as e:
                logger.error(f"Failed to upload images in {root}: {e}")
                continue
            
            
            # create board object with remote URLs
            b = board(
                name=board_name,
                output_file_loc=str(masterDir),  # already a folder path
                image_paths=http_links,
                paginate=paginate,
                images_per_page=(42 if paginate else 10000),
                upload=upload,

            )
            b.link_hash_map = hash_map
            b.paginate_board()
            boards.append(b)
            logger.debug(f"Uploaded board created: {board_name} ({len(http_links)} images)")

    return boards



# def standardBoards(directories, masterDir, paginate, upload):
#     boards = []
#     for directory in directories:
#         # source_dir = directory
#         # target_dir = directory["target_directory"]
#         media_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.mp4', '.avi', '.webm')

#         for root, dirs, files in os.walk(directory):
#             image_paths = []
#             for f in sorted(files):
#                 if f.lower().endswith(media_extensions):
#                     abs_path = Path(os.path.join(root, f)).resolve()
#                     file_url = abs_path.as_uri()
#                     image_paths.append(file_url)

#             logger.info(f'Processing {root} with {len(image_paths)} images.')

#             rel_path = os.path.relpath(root, directory)
#             if rel_path == '.': continue
#             board_name = rel_path.replace(os.sep, "_~")
#             output_path = masterDir
#             # logger.info('masta diru = ' + masterDir)
#             os.makedirs(output_path, exist_ok=True)

#             b = board(
#                 name=board_name,
#                 output_file_loc=output_path,
#                 image_paths=image_paths,
#                 paginate=paginate,
#                 images_per_page=42 if paginate else 10000,
#                 upload=upload,
#             )

#             b.paginate_board()
#             boards.append(b)
#             logger.info(f"Board created for: {board_name}, with {len(image_paths)} images.")
#     return boards

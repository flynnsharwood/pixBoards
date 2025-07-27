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
    for directory in directories:
        source_dir = directory["source_directory"]
        # target_dir = directory["target_directory"]
        media_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.mp4', '.avi', '.webm')

        for root, dirs, files in os.walk(source_dir):
            image_paths = []
            for f in sorted(files):
                if f.lower().endswith(media_extensions):
                    abs_path = Path(os.path.join(root, f)).resolve()
                    file_url = abs_path.as_uri()
                    image_paths.append(file_url)

            logger.info(f'Processing {root} with {len(image_paths)} images.')

            rel_path = os.path.relpath(root, source_dir)
            if rel_path == '.': continue
            board_name = rel_path.replace(os.sep, "_~")
            output_path = masterDir
            # logger.info('masta diru = ' + masterDir)
            os.makedirs(output_path, exist_ok=True)

            b = board(
                name=board_name,
                output_file_loc=output_path,
                image_paths=image_paths,
                paginate=paginate,
                images_per_page=42 if paginate else 10000,
                upload=upload,
            )

            b.paginate_board()
            boards.append(b)
            logger.info(f"Board created for: {board_name}, with {len(image_paths)} images.")
    return boards

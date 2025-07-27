import os
from boards.classes import * 
from boards.create import create_index_file
from pathlib import Path

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
        source_dir = Path(directory["source_directory"]).resolve()
        target_dir = Path(directory["target_directory"]).resolve()
        media_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.mp4', '.avi', '.webm')

        for root, dirs, files in os.walk(source_dir):
            root_path = Path(root).resolve()
            image_paths = []

            for f in sorted(files):
                if f.lower().endswith(media_extensions):
                    abs_path = Path(root_path, f).resolve()
                    file_url = abs_path.as_uri()
                    image_paths.append(file_url)

            if not image_paths:
                continue

            # Build target directory for images
            rel_path = root_path.relative_to(source_dir)
            output_path = Path(target_dir, rel_path).resolve()

            # ➕ Create output path (for media files if needed)
            os.makedirs(output_path, exist_ok=True)

            # ➕ Define HTML output directory inside this board's directory
            html_output_dir = output_path
            os.makedirs(html_output_dir, exist_ok=True)

            board_name = root_path.name
            logger.info(f'Creating board: {board_name} at {html_output_dir}')

            b = board(
                name=board_name,
                output_file_loc=str(html_output_dir),  
                image_paths=image_paths,
                paginate=paginate,
                images_per_page=42 if paginate else 10000,
                upload=upload,
            )

            logger.info(f'Board created with {len(image_paths)} images: {board_name}')

            b.paginate_board()
            boards.append(b)
    return boards

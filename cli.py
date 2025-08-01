import argparse
import csv
import os
import time
from datetime import date

import yaml

import psycopg2

from boards.boardmakers import boardsForImglist, standardBoards, uploadBoards
from boards.create import (create_css_file, create_html_file,
                           create_index_file, create_js_file)
from boards.log_utils import setup_logger

logger = setup_logger(__name__)

from boards.arguments import args

from boards.db import create_boards_table, save_board

# def parse_directories(args, config):
#     from boards.create import getDirList  # Make sure it's importable here

#     if args.csvs:
#         directories = getDirList(args.csvs)
#         logger.debug("Using CSVs → %s", directories)
#     elif config.get("csvList"):
#         directories = getDirList(config["csvList"])
#         logger.debug("Using config.csvList → %s", directories)
#     elif args.dir:
#         directories = [args.dir]
#         logger.debug("Using --dir → %s", directories)
#     elif config.get("directories"):
#         directories = config["directories"]
#         logger.debug("Using config.directories → %s", directories)
#     else:
#         logger.error("No source directories specified. Exiting.")
#         exit(1)

#     return directories


def main():

    def getDirList(csvList):
        source_dirs = []
        for csv_path in csvList:
            with open(csv_path, newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    source_dirs.append(row["source_directory"])
        return source_dirs

    # Setup logger
    start_time = time.time()
    today = date.today()

    logger.info(f"Today is {today}, Starting ...")

    # Load config

    def load_config(yml_path):
        with open(yml_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    if args.config:
        configFile = args.config
    else:
        configFile = "config.yml"
    config = load_config(configFile)

    if args.saveBoards:
        conn = psycopg2.connect(
            dbname="boards",
            user="postgres",
            password="password",
            host="localhost",
        )
        create_boards_table(conn)

    masterDir = config["masterDir"]
    configCss = {
        "col_count": args.col if args.col else config.get("col_count", []),
        "margin": args.margin if args.margin else config.get("margin", []),
    }
    paginate = config.get("paginate", True) is True
    boards = []

    # Handle imagelist mode
    if args.useLists or args.imageLists:
        usingLists = True
        imgList_List = (
            args.imageLists if args.imageLists else config.get("imageLists", [])
        )
        outputDir = os.path.join(os.path.dirname(config["masterDir"]), "imglists_v2")
        boards.extend(boardsForImglist(imgList_List, masterDir, paginate))

        if input('Do you want to include local images as well?  (y/N)') == 'y': usingLists = False
    else:
        usingLists = False

    # Handle upload
    if args.upload:
        logger.info("Upload case")
        outputDir = masterDir + "upload"
        upload = True
    else:
        upload = False
        outputDir = masterDir

    # Determine directories to process
    if args.csvs:
        # user explicitly passed CSVs
        directories = getDirList(args.csvs)
        logger.debug("Using CSVs → %s", directories)
    elif config.get("csvList"):
        # config.yml has csvList
        directories = getDirList(config["csvList"])
        logger.debug("Using config.csvList → %s", directories)
    elif args.dir:
        directories = [args.dir]
        logger.debug("Using --dir → %s", directories)
    elif config.get("directories"):
        # fallback to config.yml directories
        directories = config["directories"]
        logger.debug(f"Using config.directories → %s", directories)
    else:
        logger.error("No source directories specified. Exiting.")
        exit(1)

    # board generation standar case
    if args.random is None and not usingLists:
        if upload:
            boards.append(uploadBoards(directories, outputDir, paginate, upload=True))
        else:
            boards.append(standardBoards(directories, outputDir, paginate, upload=False))

    def assign_nested_boards(boards):
        board_map = {b.name: b for b in boards}
        logger.debug("Board Map Keys:  %s", list(board_map.keys()))
        nested_set = set()

        for b in boards:
            parts = b.name.split("_~")
            if len(parts) > 1:
                for depth in range(len(parts) - 1, 0, -1):
                    parent_name = "_~".join(parts[:depth])
                    parent = board_map.get(parent_name)
                    if parent:
                        parent.nested_boards.append(b)
                        nested_set.add(b)
                        break

        # Only boards that are not nested under any parent are roots
        root_boards = [b for b in boards if b not in nested_set]
        return root_boards

    root_boards = assign_nested_boards(boards)
    logger.debug(root_boards)

    # Group boards by output directory and create output
    # boards_by_directory = defaultdict(list)
    logger.info(f"Total boards to generate HTML for: {len(boards)}")

    if not args.saveBoards:
        for b in boards:
            for p in b.pages:
                create_html_file(p)
    else:
        for b in boards:
            for p in b.pages:
                create_html_file(p)
                save_board(conn, b)


    # root_boards = [b for b in boards if Path(os.path.dirname(b.output_file_loc)).resolve() in {Path(d).resolve() for d in root_output_dirs}]
    os.makedirs(outputDir, exist_ok=True)
    create_index_file(root_boards, outputDir)
    create_css_file(outputDir, configCss)
    create_js_file(outputDir)

    # Print nested board tree
    def print_board_tree(boards, depth=0):
        for b in boards:
            print("  " * depth + f"- {b.name}")
            print_board_tree(b.nested_boards, depth + 1)

    print("Boards structure - ")
    print_board_tree(root_boards)

    logger.debug(root_boards)
    # for b in boards:
    #     print('link hash maps')
    # #     print(b.nested_boards)
    #     print(b.link_hash_map)

    print(f"browse boards at - {outputDir}")

    elapsed_time = time.time() - start_time
    logger.info(f"Finished in {elapsed_time:.2f} seconds.")
    conn.close()


if __name__ == "__main__":
    main()

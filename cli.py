import csv
import os
import subprocess
import time
from datetime import date

import psycopg2
import yaml

from boards.boardmakers import boardsForImglist, standardBoards, uploadBoards, randomBoard
from boards.create import (
    create_css_file,
    create_html_file,
    create_index_file,
    create_js_file,
)
from boards.log_utils import setup_logger

logger = setup_logger(__name__)


from boards.arguments import args
from boards.db import create_boards_table, save_board

from boards.config_loader import config, outputDir




def main():

    # def getDirList(csvList):
    #     source_dirs = []
    #     for csv_path in csvList:
    #         with open(csv_path, newline="", encoding="utf-8") as csvfile:
    #             reader = csv.DictReader(csvfile)
    #             for row in reader:
    #                 source_dirs.append(row["source_directory"])
    #     return source_dirs

    # Setup logger
    start_time = time.time()
    today = date.today()

    logger.info(f"Today is {today}, Starting ...")

    # Load config

    # def load_config(yml_path):
    #     with open(yml_path, "r", encoding="utf-8") as f:
    #         return yaml.safe_load(f)

    # if args.config:
    #     configFile = args.config
    # else:
    #     configFile = "config.yml"
    # config = load_config(configFile)

    if args.saveBoards:
        conn = psycopg2.connect(
            dbname="boards",
            user="postgres",
            password="password",
            host="localhost",
        )
        create_boards_table(conn)

    masterDir = config["masterDir"]
    # token = os.getenv("GITHUB_PAT")  # Set this in your environment or a .env file

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
        # outputDir = os.path.join(os.path.dirname(config["masterDir"]), "imglists_v2")
        boards.extend(boardsForImglist(imgList_List, outputDir, paginate))

        if input("Do you want to include local images as well?  (y/N)") == "y":
            usingLists = False
    else:
        usingLists = False

    # Handle upload
    if args.upload:
        logger.info("Upload case")
        # outputDir =  os.path.join(os.path.dirname(masterDir), masterDir + "upload")
        # outputDir = masterDir + "_upload"
        upload = True
    else:
        upload = False

    # if not (args.useLists or args.imageLists or args.upload):
    #     outputDir = masterDir

    # Determine directories to process
    # if args.csvs:
    #     directories = getDirList(args.csvs)
    #     logger.debug("Using CSVs → %s", directories)
    # elif config.get("csvList"):
    #     directories = getDirList(config["csvList"])
    #     logger.debug("Using config.csvList → %s", directories)
    # elif args.dir:
    #     directories = [args.dir]
    #     logger.debug("Using --dir → %s", directories)
    # elif config.get("directories"):
    #     directories = config["directories"]
    #     logger.debug(f"Using config.directories → %s", directories)
    # else:
    #     logger.error("No source directories specified.")
        # exit(1)
    
    if args.dir:
        directories =  [args.dir]
        logger.debug("Using --dir → %s", directories)
    elif config.get("directories"):
        directories = config["directories"]
        logger.debug(f"Using config.directories → %s", directories)

    # board generation standar case
    if not usingLists:
        if upload:
            boards.extend(uploadBoards(directories, outputDir, paginate, upload=True))
        else:
            boards.extend(
                standardBoards(directories, outputDir, paginate, upload=False)
            )
    
    if args.random:
        rancount = args.random

    # for random case
    if args.random:
        boards.append(randomBoard(boards, rancount, outputDir, paginate, upload))


    from boards.nest_boards import assign_nested_boards


    root_boards = assign_nested_boards(boards)
    logger.debug(root_boards)

    # Group boards by output directory and create output
    logger.info(f"Total boards to generate HTML for: {len(boards)}")


    # Print nested board tree
    def print_board_tree(boards, depth=0):
        for b in boards:
            print("  " * depth + f"- {b.name}")
            print_board_tree(b.nested_boards, depth + 1)

    print("Boards structure - ")
    print_board_tree(root_boards)

    logger.debug(root_boards)
    print(f"browse boards at - {outputDir}")

    elapsed_time = time.time() - start_time
    logger.info(f"Finished in {elapsed_time:.2f} seconds.")


if __name__ == "__main__":
    main()

from boards.classes import board
from boards.create import *

import csv
import os
import time
import re
import yaml
import argparse
from datetime import date
from collections import defaultdict

from boards.boardmakers import *
from pathlib import Path

def getDirList(csvList, masterDir):
    all_rows = []
    for csv_path in csvList:
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                row["target_directory"] = os.path.join(masterDir, row["target_directory"])
                all_rows.append(row)
    return all_rows


# Setup logger
start_time = time.time()
today = date.today()
from boards.log_utils import setup_logger
logger = setup_logger(__name__)
logger.info(f"Today is {today}, Starting application...")

# Parse arguments
parser = argparse.ArgumentParser(description="Generate HTML for media directories.")
parser.add_argument('--random', type=int, help="Select N random images from a directory and generate HTML.")
parser.add_argument('--ranDir', type=str, help="Directory to search images in for --random")
parser.add_argument('--dir', type=str, help="Directory to use for the images")
parser.add_argument('--csvs', nargs='+', help='List of CSV files to use')
parser.add_argument('--useLists', action='store_true', help='Use list files from config')
parser.add_argument('--imageLists', nargs='+', help='List of imagelist files to use.')
parser.add_argument('--col', type=int, help='Number of columns to default to')
parser.add_argument('--margin', type=int, help='Margin in px')
parser.add_argument('--upload', action='store_true', help='Upload images to Imgchest')
args = parser.parse_args()

# Load config
def load_config(yml_path="config.yml"):
    with open(yml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

config = load_config()
masterDir = config['masterDir']
configCss = {
    'col_count': args.col if args.col else config.get("col_count", []),
    'margin': args.margin if args.margin else config.get("margin", []),
}
paginate = bool(config.get('paginate', True))
boards = []

# Handle imagelist mode
if args.useLists or args.imageLists:
    usingLists = True
    imgList_List = args.imageLists if args.imageLists else config.get("imageLists", [])
    masterDir = os.path.join(os.path.dirname(config["masterDir"]), 'imglists_v2')
    boards.extend(boardsForImglist(imgList_List, masterDir, paginate))
else:
    usingLists = False

# Handle upload
if args.upload:
    logger.info("Upload case")
    masterDir = os.path.join(os.path.dirname(config["masterDir"]), 'boardsUpload')
    upload = True
else:
    upload = False

# Determine directories to process
csvList = args.csvs if args.csvs else config.get("csvList", [])
if not csvList:
    logger.info("No CSV files provided. Set them in config.yml or pass using --csvs.")
    exit(1)

if args.dir:
    directories = [{'source_directory': args.dir, 'target_directory': masterDir + '_specified'}]
else:
    directories = getDirList(csvList, masterDir)

from boards.boardmakers import *

# Handle standard board generation
if not args.random and not usingLists:
    boards = standardBoards(directories, masterDir, paginate, upload)
    # logger.info('masterdir is - ' + masterDir)

def assign_nested_boards(boards):
    board_map = {b.name: b for b in boards}
    print("Board Map Keys:", list(board_map.keys()))
    nested_set = set()

    for b in boards:
        parts = b.name.split('_~')
        if len(parts) > 1:
            for depth in range(len(parts) - 1, 0, -1):
                parent_name = '_~'.join(parts[:depth])
                parent = board_map.get(parent_name)
                if parent:
                    parent.nested_boards.append(b)
                    nested_set.add(b)
                    break

    # Only boards that are not nested under any parent are roots
    root_boards = [b for b in boards if b not in nested_set]
    return root_boards

root_boards = assign_nested_boards(boards)
print(root_boards)

# Group boards by output directory and create output
# boards_by_directory = defaultdict(list)
for b in boards:
    boardDir = os.path.dirname(b.output_file_loc)
    # boards_by_directory[boardDir].append(b)
    create_js_file(boardDir)
    create_css_file(boardDir, configCss)
    for p in b.pages:
        create_html_file(p)

# root_boards = [b for b in boards if Path(os.path.dirname(b.output_file_loc)).resolve() in {Path(d).resolve() for d in root_output_dirs}]
create_index_file(root_boards, masterDir)
create_css_file(masterDir, configCss)
create_js_file(masterDir)

# Print nested board tree
def print_board_tree(boards, depth=0):
    for b in boards:
        print("  " * depth + f"- {b.name}")
        print_board_tree(b.nested_boards, depth + 1)

print_board_tree(root_boards)

print(root_boards)
for b in boards:
    print(b.name)
#     print('nested boards')
#     print(b.nested_boards)

elapsed_time = time.time() - start_time
logger.info(f"Finished in {elapsed_time:.2f} seconds.")

import os

from boards.arguments import args
from boards.config_loader import outputDir
from boards.create import (
    create_css_file,
    create_html_file,
    create_index_file,
    create_js_file,
)
from boards.db import save_board


def create_output_files(root_boards, boards, conn):
    def create_semi_indexes(boards):
        for b in boards:
            if b.dummy_status == True:
                create_index_file(b.nested_boards, outputDir, b.name, sub_index=True)

    if not args.saveBoards:
        for b in boards:
            for p in b.pages:
                create_html_file(p)
    else:
        for b in boards:
            save_board(conn, b)
            for p in b.pages:
                create_html_file(p)

    os.makedirs(outputDir, exist_ok=True)
    create_index_file(root_boards, outputDir)
    create_semi_indexes(boards)
    create_css_file(outputDir)
    create_js_file(outputDir)

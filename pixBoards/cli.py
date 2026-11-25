import logging
import os
import sys
import time
from datetime import date

from pixBoards.arguments import parse_args
from pixBoards.boardmakers import (
    boardsForImglist,
    descBoard,
    dump_json,
    randomBoard,
    standardBoards,
    uploadBoards,
)
from pixBoards.config_loader import ConfigError, build_config, make_config
from pixBoards.create import write_output
from pixBoards.db import DatabaseUnavailable, create_boards_table, create_conn, save_boards
from pixBoards.log_utils import setup_logging
from pixBoards.mediacache import MediaCache
from pixBoards.nest_boards import assign_nested_boards

logger = logging.getLogger(__name__)


def print_board_tree(boards, depth=0):
    for b in boards:
        print("  " * depth + f"- {b.clean_name}")
        print_board_tree(b.nested_boards, depth + 1)


def build_boards(args, config, conn, cache):
    output_dir = config["outputDir"]
    boards = []

    using_lists = False
    if args.useLists or args.imageLists:
        using_lists = not args.includeLocal
        list_files = args.imageLists or config.get("imageLists") or []
        boards.extend(boardsForImglist(list_files, output_dir))

    if args.dir:
        directories = [args.dir]
        logger.debug("Using --dir → %s", directories)
    else:
        directories = config["directories"]
        logger.debug("Using config.directories → %s", directories)

    if directories and not using_lists:
        if args.upload:
            logger.info("Upload case")
            boards.extend(
                uploadBoards(
                    directories,
                    output_dir,
                    conn,
                    config,
                    cache,
                    use_sidecar=args.sidecar,
                    use_saved=args.useSaved,
                )
            )
        else:
            boards.extend(standardBoards(directories, output_dir, cache))

    source_boards = list(boards)
    if args.random:
        boards.append(randomBoard(source_boards, args.random, output_dir))
    if args.recent:
        boards.append(descBoard(source_boards, args.recent, output_dir, reddit=args.reddit))

    for b in boards:
        b.paginate(config["page_size"], config["padding"], paginate=config["paginate"] is True)
    return boards


def main(argv=None):
    args = parse_args(argv)
    setup_logging()

    if args.makeConfig:
        return 0 if make_config() else 1

    try:
        config = build_config(args)
    except ConfigError as e:
        logger.error(e)
        return 1

    start_time = time.time()
    logger.info(f"Today is {date.today()}, Starting ...")

    conn = None
    try:
        if args.upload or args.saveBoards:
            conn = create_conn(config)
        if args.saveBoards:
            create_boards_table(conn)

        with MediaCache(config.get("cache_file")) as cache:
            boards = build_boards(args, config, conn, cache)

        root_boards = assign_nested_boards(boards)
        logger.info(f"Total boards to generate HTML for: {len(boards)}")
        write_output(root_boards, boards, config)
        if config["json_dump"]:
            dump_json(boards, os.path.join(config["outputDir"], "dump.json"))
        if args.saveBoards:
            save_boards(conn, boards)
    except DatabaseUnavailable as e:
        logger.error(e)
        return 1
    finally:
        if conn is not None:
            conn.close()

    print("Boards structure - ")
    print_board_tree(root_boards)
    print(f"browse boards at - {config['outputDir']}")

    if args.gitPush:
        from pixBoards.git import push_output

        if not push_output(config):
            return 1

    logger.info(f"Finished in {time.time() - start_time:.2f} seconds.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

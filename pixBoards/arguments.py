import argparse


def build_parser():
    parser = argparse.ArgumentParser(description="Generate HTML for media directories.")
    parser.add_argument(
        "--random",
        type=int,
        help="add a 'randomised_set' board with N random images from all boards; "
        "-1 (or more than the total) shuffles everything",
    )
    parser.add_argument(
        "--recent",
        "--desc",
        type=int,
        help="add a 'recent imgs' board, newest first (EXIF date, else file time), "
        "keeping the newest N; -1 keeps all",
    )
    parser.add_argument("--dir", type=str, help="Directory to use for the images")
    parser.add_argument("--useLists", action="store_true", help="Use list files from config")
    parser.add_argument("--imageLists", nargs="+", help="List of imagelist files to use.")
    parser.add_argument("--col", type=int, help="Number of columns to default to")
    parser.add_argument("--margin", type=int, help="Margin in px")
    parser.add_argument(
        "--sidecar",
        action="store_true",
        default=False,
        help="use links from sidecar files",
    )
    parser.add_argument(
        "--includeLocal",
        action="store_true",
        default=False,
        help="include local files if using lists",
    )
    parser.add_argument(
        "--makeConfig",
        action="store_true",
        default=False,
        help="write a template config.yml to the current directory and exit",
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        default=False,
        help="Upload images to Imgchest",
    )
    parser.add_argument("--config", type=str, default=None, help="config file to use")
    parser.add_argument(
        "--saveBoards", action="store_true", help="Save generated boards to PostgreSQL"
    )
    parser.add_argument(
        "--gitPush", action="store_true", help="Push outputDir to existing Git repo"
    )
    parser.add_argument("--useSaved", action="store_true", help="use only saved images")
    parser.add_argument(
        "--reddit",
        action="store_true",
        help="with --recent: sort by the reddit post id at the start of the file "
        "name (base 36) instead of by date",
    )
    parser.add_argument("--pageSize", type=int, help="edit page size")
    parser.add_argument("--height", type=int, help="row height in px for the justified layout")
    return parser


def parse_args(argv=None):
    return build_parser().parse_args(argv)

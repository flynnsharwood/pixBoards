import argparse

# Parse arguments
parser = argparse.ArgumentParser(description="Generate HTML for media directories.")
parser.add_argument(
    "--random",
    type=int,
    help="Select N random images from a directory and generate HTML. does not work yet",
)
parser.add_argument(
    "--ranDir",
    type=str,
    help="Directory to search images in for --random",
)
parser.add_argument("--dir", type=str, help="Directory to use for the images")
parser.add_argument("--csvs", nargs="+", help="List of CSV files to use")
parser.add_argument(
    "--useLists", action="store_true", help="Use list files from config"
)
parser.add_argument("--imageLists", nargs="+", help="List of imagelist files to use.")
parser.add_argument("--col", type=int, help="Number of columns to default to")
parser.add_argument("--margin", type=int, help="Margin in px")
parser.add_argument("--upload", action="store_true", help="Upload images to Imgchest")
parser.add_argument("--config", type=str, help="config file to use")
parser.add_argument('--saveBoards', action='store_true', help='Save generated boards to PostgreSQL')

args = parser.parse_args()

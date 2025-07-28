from gooey import Gooey, GooeyParser
from cli import parse_directories
from boards.create import uploadBoards

@Gooey(program_name="Masonry Board Generator", default_size=(700, 600))
def run():
    parser = GooeyParser(description="Gooey Board Generator")
    parser.add_argument('config_file', widget='FileChooser')
    parser.add_argument('-o', '--output', widget='DirChooser', default='output')
    parser.add_argument('--paginate', action='store_true')
    parser.add_argument('--upload', action='store_true')
    args = parser.parse_args()

    directories = parse_directories(args.config_file)

    boards = uploadBoards(
        directories=directories,
        masterDir=args.output,
        paginate=args.paginate,
        upload=args.upload
    )

    print(f" {len(boards)} boards generated.")

if __name__ == '__main__':
    run()

class page:
    def __init__(self, page_number, total_pages, images, file_location):
        self.page_number = page_number          # Current page number
        self.images = images                    # image list for the page
        self.total_pages = len(images)          
        self.file_location = file_location 

from math import ceil

class board:
    def __init__(self, name, output_file_loc, image_paths, paginate=True, images_per_page=42,  upload=False):
        self.name = name
        self.image_paths = image_paths
        self.pages = []                                 # will be storing a list of instances of class, page.
        self.images_per_page = images_per_page
        self.output_file_loc = output_file_loc
        self.upload_status = upload
        self.paginate_status = paginate
        self.link_hash_map = {} if self.upload_status else None


    def paginate_board(self):
        total_images = len(self.image_paths)
        total_pages = ceil(total_images/self.images_per_page)

        for i in range(total_pages):
            
            start = i * self.images_per_page
            end = start + self.images_per_page
            page_images = self.image_paths[start:end]

            file_loc = self.output_file_loc.replace('.html', f'_{(i+1):03}.html') # padded to 3 digits. 

            Page = page(
                page_number=i+1,
                total_pages=total_pages,
                images=page_images,
                file_location=file_loc
            )
            self.pages.append(Page)
            logger.info(f'Finished with - Board: {self.name}, page {i + 1} of {total_pages}')


import csv
def getDirList(csvList, masterDir):
    all_rows = []
    for csv_path in csvList:
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Prepend masterDir to target_directory
                row["target_directory"] = os.path.join(masterDir, row["target_directory"])
                all_rows.append(row)
    # print(all_rows)
    return all_rows

# -- media blocks
imageBlock = """
<div class="masonry-item">
    <a href="{{ media_path }}" onclick="copyToClipboard('{{ hash }}'); event.preventDefault();">
        <img src="{{ media_path }}" alt="{{ hash }}" loading="lazy">
    </a>
</div>
"""

videoBlock = """
<div class="masonry-item">
    <video width="300" controls>
        <source src="{{ uploaded_url }}" type="video/mp4" loading="lazy">
        Your browser does not support the video tag. {{ hashVal }}
    </video>
</div>
"""



# -- create funtions

from jinja2 import Template
from collections import defaultdict

def create_css_file(target_directory, config, css_template_path='templates/template.css'):
    with open(css_template_path, "r", encoding="utf-8") as template_file:
        template = Template(template_file.read())
        rendered_css = template.render(config)
    with open(os.path.join(target_directory, "styles.css"), "w", encoding="utf-8") as output_file:
        output_file.write(rendered_css)


def create_js_file(target_directory, js_template_path='templates/template.js'):
    with open(js_template_path, "r", encoding="utf-8") as template:
        js_content = template.read()
    with open(os.path.join(target_directory, "script.js"), "w", encoding="utf-8") as f:
        f.write(js_content)

def create_master_index(directories, output_path, template_path='templates/master_index_template.html'):
    css_filename = "styles.css"

    # Prepare links: List of (name, link)
    links = []
    for d in directories:
        target_dir = d.target_directory if hasattr(d, 'target_directory') else d["target_directory"]
        index_file = os.path.join(target_dir, "index.html")
        folder_name = os.path.basename(target_dir)
        links.append((folder_name, index_file))

    # Load and render template
    with open(template_path, "r", encoding="utf-8") as f:
        template = Template(f.read())

    rendered_html = template.render(css_filename=css_filename, links=links)

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered_html)

def create_index_file(subfolders, target_directory, template_path='templates/index_template.html'):
    index_file = os.path.join(target_directory, "index.html")

    with open(template_path, "r", encoding="utf-8") as template:
        index_template = template.read()

    # Convert subfolder list into a nested tree
    def build_tree(paths):
        tree = defaultdict(dict)
        for path in paths:
            parts = path.split(os.sep)
            current = tree
            for part in parts:
                current = current.setdefault(part, {})
        return tree

    # Recursively turn tree into nested HTML
    def tree_to_html(tree, path_prefix=""):
        html = "<ul>\n"
        for name in sorted(tree.keys()):
            full_path = os.path.join(path_prefix, name) if path_prefix else name
            file_link = f"{full_path.replace(os.sep, '_')}.html"
            if tree[name]:  # has children
                html += f'<li><a href="{file_link}">{name}\n{tree_to_html(tree[name], full_path)}</a></li>\n'
            else:
                html += f'<li><a href="{file_link}">{name}</a></li>\n'
        html += "</ul>\n"
        return html

    folder_tree = build_tree(subfolders)
    nested_html = tree_to_html(folder_tree)

    html_content = index_template.replace("{{  index_links  }}", nested_html)
    with open(index_file, "w", encoding="utf-8") as f:
        f.write(html_content)

def create_html_file(p):
    media_blocks = []

    for idx, media_path in enumerate(p.images):
        ext = os.path.splitext(media_path)[1].lower()
        imgTemplate = Template(imageBlock)
        vidTemplate = Template(videoBlock)

        hash = getattr(p, 'hashes', {}).get(media_path, media_path) if upload else media_path
        # hash = media_path

        #image
        if ext in ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'):
            block = imgTemplate.render(media_path=media_path, hash=hash)
        # video
        elif ext in ('.mp4', '.avi', '.mov', '.webm'):
            block = vidTemplate.render(media_path=media_path, hash=hash)
        else:
            continue

        media_blocks.append(block)

    pagination_html = ""
    if p.total_pages > 1:
        pagination_html += '<div class="pagination">\n'
        for i in range(1, p.total_pages + 1):
            page_file = os.path.basename(p.file_location).replace(f'_{p.page_number:03}', f'_{i:03}')
            if i == p.page_number:
                pagination_html += f'<strong>{i}</strong> '
            else:
                pagination_html += f'<a href="{page_file}">{i}</a> '
        pagination_html += '</div>'
    
    with open("templates/template.html", encoding="utf-8") as f:
        base_template = Template(f.read())

    final_html = base_template.render(
        title=f"Page {p.page_number} of {p.total_pages}",
        media_content="\n".join(media_blocks),
        pagination=pagination_html
    )

    os.makedirs(os.path.dirname(p.file_location), exist_ok=True)
    with open(p.file_location, "w", encoding="utf-8") as f:
        f.write(final_html)

# --- the previous part has stuff that I might shift to a different file ---

import time
start_time = time.time()
from datetime import date
import argparse
import yaml
import os
import re
# from boards.filemaking.file_utils import create_html_file, create_css_file, create_js_file, create_index_file, create_master_index_file
# from boards.dir_utils import getDirList
# from boards.ranPick import gen_random
# from math import ceil
# import traceback

# set up logger
today = date.today()
from boards.log_utils import setup_logger
logger = setup_logger(__name__)
logger.info(f"today is {today}, Starting application...")

# arguments 
parser = argparse.ArgumentParser(description="Generate HTML for media directories.")
parser.add_argument('--random', type=int, help="Select N random images from a directory and generate HTML.")
parser.add_argument('--ranDir', type=str, help="Directory to search images in for --random")
parser.add_argument('--dir', type=str, help="Directory to use for the images")
parser.add_argument('--csvs', nargs='+', help='List of CSV files to use')
parser.add_argument('--useLists', action='store_true', help='use list files from config')
parser.add_argument('--imageLists', nargs='+', help='List of imagelist files to use. videos can be used too, probably')
parser.add_argument('--col', type=int, help='number of columns to default to (default is set in the config)')
parser.add_argument('--margin', type=int, help='Margin in px (default is set in the config)')
parser.add_argument('--upload', action='store_true', help='Upload images to Imgchest and replace local paths with uploaded URLs')
args = parser.parse_args()

# config
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

boards = [] # board instances to be stored in here

# imagelist case
if args.useLists or args.imageLists:
    usingLists = True
    imgList_List = args.imageLists if args.imageLists else config.get("imageLists", []) # list of list of images.
    # Now I might need to sanitise the image list so that there aren't instances with the same name.
    # But as the imagelist files are in the same folder, they won't have the same name, so I leave this for the future me.
    listDir = os.path.join(os.path.dirname(config["masterDir"]), 'imglists_v2')
    os.makedirs(listDir, exist_ok=True)

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
else:
    usingLists = False

# pages for each board has been made, in the case of using image lists.
# aaaand now I gotta do this for the upload, and non upload modes
# and who would forget the freakign random board option. fml.
# Ooo what if I saved these board instances to disk?

# if using localfiles
if args.upload:
    logger.info("upload case")
    masterDir = os.path.join(os.path.dirname(config["masterDir"]), 'boardsUpload')
    upload = True
else:
    upload = False

csvList = args.csvs if args.csvs else config.get("csvList", [])
if not csvList:
    logger.info("No CSV files provided. Set them in config.yml or pass using --csvs.")
    exit(1)
if args.dir:
    directories = [{'source_directory': args.dir, 'target_directory': masterDir + '_specified'}] # only one board for the directory specified
else:
    directories = getDirList(csvList, masterDir)

# we now have the directories to be used. Boards class do not contain other boards, but they might not need to
# The nesting only matters while making the index file. And while making the actual board html files.

# Now, create a board for each sub directory.

if not args.random and not usingLists:  # normal and upload case
    for directory in directories:
        source_dir = directory["source_directory"]
        target_dir = directory["target_directory"]
        
        os.makedirs(target_dir, exist_ok=True)

        for root, _, files in os.walk(source_dir):
            # Collect all image files in this subdirectory
            image_paths = [
                os.path.relpath(os.path.join(root, f), start=target_dir).replace("\\", "/")
                for f in sorted(files)
                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.mp4', '.avi', '.webm'))
            ]



            if not image_paths:
                continue  # Skip folders with no images

            # Compute board name based on relative path from source_root
            rel_path = os.path.relpath(root, source_dir)
            board_name = os.path.basename(root) if rel_path == '.' else rel_path.replace('\\', '/')

            # Create a matching output file location in the target directory
            output_filename = re.sub(r'[^a-zA-Z0-9_\-]', '_', board_name) + ".html"
            output_file_loc = os.path.join(target_dir, output_filename)

            # Create the board
            b = board(
                name=board_name,
                output_file_loc=output_file_loc,
                image_paths=image_paths,
                paginate= paginate,
                images_per_page=42 if paginate else 10000,
                upload=upload,
            )
            b.paginate_board()
            boards.append(b)
            logger.info(f"Board created for: {board_name}, with {len(image_paths)} images.")

# now we have all the boards that we need to generate.
# We have all the info needed to create each board, so it should be easy enough to do it.
# Actually we should go page by page, I think.


# Okay so most of the time is being spent in this function. Why? Is there some sort of inefficiency in here?
from collections import defaultdict

# Group boards by their target_directory
boards_by_directory = defaultdict(list)
for b in boards:
    boardDir = os.path.dirname(b.output_file_loc)
    boards_by_directory[boardDir].append(b)
    create_js_file(boardDir)
    create_css_file(boardDir, configCss)
    for p in b.pages:
        create_html_file(p)

# Now create index file for each directory
for target_directory, board_group in boards_by_directory.items():
    subfolders = [b.name for b in board_group]
    create_index_file(subfolders, target_directory)


create_master_index(directories, output_path=os.path.join(config["masterDir"], "index.html"))
create_css_file(masterDir, configCss)
create_js_file(masterDir)


elapsed_time = time.time() - start_time
logger.info(f"Finished in {elapsed_time:.2f} seconds.")

# psycopg integration and --random  features left.
# index files for individual boards is not being made.
# file not being shown properly.

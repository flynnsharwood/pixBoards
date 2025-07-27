from datetime import date

# set up logger
today = date.today()
from boards.log_utils import setup_logger
logger = setup_logger(__name__)

import yaml

def load_config(yml_path="config.yml"):
    with open(yml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

config = load_config()

padding = config['padding']


class page:
    def __init__(self, page_number, total_pages, images, file_location):
        self.page_number = page_number          # Current page number
        self.images = images                    # image list for the page
        self.total_pages = total_pages       
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
        # self.subfolders = []
        self.nested_boards = []


    def paginate_board(self):
        total_images = len(self.image_paths)
        total_pages = ceil(total_images/self.images_per_page)
        print ()

        for i in range(total_pages):
            
            start = i * self.images_per_page
            end = start + self.images_per_page
            page_images = self.image_paths[start:end]

            if self.output_file_loc[-5:] == '.html':
                file_loc = self.output_file_loc.replace('.html', f'_{(i+1):0{padding}}.html') # padded to 3 digits. 
            else:
                file_loc = self.output_file_loc + f'_{(i+1):0{padding}}.html'
            Page = page(
                page_number=i+1,
                total_pages=total_pages,
                images=page_images,
                file_location=file_loc
            )
            self.pages.append(Page)
            logger.info(f'Finished with - Board: {self.name}, page {i + 1} of {total_pages}')

import os
from boards.classes import * 
from boards.create import create_index_file
def boardsForImglist(imgList_List, listDir, paginate):
    # Now I might need to sanitise the image list so that there aren't instances with the same name.
    # But as the imagelist files are in the same folder, they won't have the same name, so I leave this for the future me.
    os.makedirs(listDir, exist_ok=True)

    boards = []

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
    

    return boards
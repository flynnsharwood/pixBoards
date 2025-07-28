from jinja2 import Template
import os

from boards.log_utils import setup_logger

logger = setup_logger(__name__)

from . import __version__

import yaml

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


def load_config(yml_path="config.yml"):
    with open(yml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


config = load_config()
padding = config["padding"]

imgTemplate = Template(imageBlock)
vidTemplate = Template(videoBlock)


def create_css_file(
    target_directory, config, css_template_path="templates/template.css"
):
    logger.debug(f"creating css file at {target_directory}")
    with open(css_template_path, "r", encoding="utf-8") as template_file:
        template = Template(template_file.read())
        rendered_css = template.render(config)
    with open(
        os.path.join(target_directory, "styles.css"), "w", encoding="utf-8"
    ) as output_file:
        output_file.write(rendered_css)


def create_js_file(target_directory, js_template_path="templates/template.js"):
    logger.debug(f"creating js file at {target_directory}")
    with open(js_template_path, "r", encoding="utf-8") as template:
        js_content = template.read()
    with open(os.path.join(target_directory, "script.js"), "w", encoding="utf-8") as f:
        f.write(js_content)


def create_index_file(
    root_boards, target_directory, template_path="templates/index_template.html"
):
    from collections import defaultdict
    import os

    index_file = os.path.join(target_directory, "index.html")

    # Load the HTML template
    with open(template_path, "r", encoding="utf-8") as template:
        index_template = template.read()

    def board_tree_to_html(boards, depth=0):
        html = "<ul>\n"
        for b in boards:
            relative_path = (
                "" * depth
            )  # Goes up one level for each depth # not needed rn as flat structure exists
            link = f"{relative_path}{b.name}_{1:0{padding}d}.html"
            html += f'<li><a class="link" href="{link}">{b.name}</a>\n'
            if b.nested_boards:
                html += board_tree_to_html(b.nested_boards, depth + 1)
            html += "</li>\n"
        html += "</ul>\n"
        return html

    nested_html = board_tree_to_html(root_boards)
    logger.debug("nestedhtml")
    logger.debug(nested_html)

    # Replace template placeholder with generated HTML
    html_content = index_template.replace("{{ index_links }}", nested_html)
    html_content = html_content.replace("{{ version }}", __version__)

    # print(index_file)

    # Write index file
    with open(index_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    logger.info(f"index file created, location is - {index_file}")


back_href = "index.html"


def create_html_file(p):
    media_blocks = []
    output_file = p.file_location
    os.makedirs(os.path.dirname(p.file_location), exist_ok=True)
    parent_dir = os.path.dirname(output_file)
    # back_href = os.path.join(parent_dir, 'index.html').replace('\\', '/')
    back_ref = "index.html"

    for idx, media_path in enumerate(p.images):
        ext = os.path.splitext(media_path)[1].lower()
        hash = media_path  # or use hash mapping if needed

        if ext in (".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"):
            block = imgTemplate.render(media_path=media_path, hash=hash)
        elif ext in (".mp4", ".avi", ".mov", ".webm"):
            block = vidTemplate.render(media_path=media_path, hash=hash)
        else:
            continue

        media_blocks.append(block)

    pagination_html = ""
    if p.total_pages > 1:
        pagination_html += '<div class="pagination">\n'
        for i in range(1, p.total_pages + 1):
            page_file = os.path.basename(p.file_location).replace(
                f"_{p.page_number:0{padding}}", f"_{i:03}"
            )
            if i == p.page_number:
                pagination_html += f"<strong>{i}</strong> "
            else:
                pagination_html += f'<a href="{page_file}">{i}</a> '
        pagination_html += "</div>"

    with open("templates/template.html", encoding="utf-8") as f:
        base_template = Template(f.read())

    final_html = base_template.render(
        title=f"Page {p.page_number} of {p.total_pages}",
        media_content="\n".join(media_blocks),
        pagination=pagination_html,
        back_button=f'<a class="button" href="{back_href}">⬅ Back to Index</a>',
    )
    final_html = final_html.replace("{{ version }}", __version__)

    logger.debug("Writing file at: " + p.file_location)
    with open(p.file_location, "w", encoding="utf-8") as f:
        f.write(final_html)


# from jinja2 import Template
# import os

# def generate_master_index(boards):
#     def build_index_tree(board):
#         children_html = ""
#         for sub in sorted(board.nested_boards, key=lambda b: b.name):
#             children_html += build_index_tree(sub)

#         link = f'<li><a href="{board.html_filename}">{board.name}</a></li>'
#         if children_html:
#             return f"<ul>{link}{children_html}</ul>"
#         else:
#             return f"<ul>{link}</ul>"

#     def create_index_file(board):
#         index_content = "<!DOCTYPE html>\n<html>\n<head>\n"
#         index_content += f"<title>Index of {board.name}</title>\n</head>\n<body>\n"
#         index_content += f"<h1>{board.name}</h1>\n"
#         index_content += build_index_tree(board)
#         index_content += "\n</body>\n</html>"

#         output_path = os.path.join(board.output_file_loc, "index.html")
#         with open(output_path, "w", encoding="utf-8") as f:
#             f.write(index_content)

#         for subboard in board.nested_boards:
#             create_index_file(subboard)

#     for root_board in boards:
#         create_index_file(root_board)

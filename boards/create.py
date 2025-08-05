import os

from jinja2 import Template

from boards.log_utils import setup_logger

logger = setup_logger(__name__)

import yaml

from boards.arguments import args

from . import __version__

imageBlock = """
<div class="masonry-item">
    <a href="{{ media_path }}" onclick="copyToClipboard('{{ hash }}'); event.preventDefault();">
        <img src="{{ media_path }}" alt="{{ hash }}" loading="lazy">
    </a>
</div>
"""

videoBlock = """
<div class="masonry-item">
    <video controls>
        <source src="{{ media_path }}" type="video/mp4" loading="lazy">
        Your browser does not support the video tag. {{ hash }}
    </video>
</div>
"""

from datetime import datetime

now = datetime.now()

timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

# Load config


def load_config(yml_path):
    with open(yml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


if args.config:
    configFile = args.config
else:
    configFile = "config.yml"
config = load_config(configFile)

padding = config["padding"]
masterDir = config["masterDir"]

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


# def create_index_file(
#     root_boards,
#     target_directory,
#     index_name="",
#     sub_index=False,
#     template_path="templates/index_template.html",
# ):
#     if sub_index == False:
#         index_file = os.path.join(target_directory, "index.html")
#     else:
#         index_file = os.path.join(target_directory, f"{index_name}_001.html")

#     # Load the HTML template
#     with open(template_path, "r", encoding="utf-8") as template:
#         index_template = template.read()

#     def board_tree_to_html(boards, depth=0):
#         html = "<ul>\n"
#         for b in boards:
#             relative_path = (
#                 "" * depth
#             )  # Goes up one level for each depth # not needed rn as flat structure exists
#             link = f"{relative_path}{b.name}_{1:0{padding}d}.html"
#             html += f'<li><a class="link" href="{link}">{b.name}</a>\n'
#             if b.nested_boards:
#                 html += board_tree_to_html(b.nested_boards, depth + 1)
#             html += "</li>\n"
#         html += "</ul>\n"
#         return html

#     nested_html = board_tree_to_html(root_boards)
#     logger.debug("nestedhtml")
#     logger.debug(nested_html)

#     # Replace template placeholder with generated HTML
#     html_content = index_template.replace("{{ index_links }}", nested_html)
#     html_content = html_content.replace("{{ version }}", __version__)
#     html_content = html_content.replace("{{ timestamp }}", timestamp)

#     # print(index_file)

#     # Write index file
#     with open(index_file, "w", encoding="utf-8") as f:
#         f.write(html_content)
#     logger.info(f"index file created, location is - {index_file}")


def create_index_file(
    root_boards,
    target_directory,
    index_name="",
    sub_index=False,
    template_path="templates/index_template.html",
):
    if not sub_index:
        index_file = os.path.join(target_directory, "index.html")
    else:
        index_file = os.path.join(target_directory, f"{index_name}_001.html")

    with open(template_path, "r", encoding="utf-8") as template:
        index_template = template.read()

    def board_tree_to_html(boards, depth=0):
        html_parts = ["<ul>\n"]
        for b in boards:
            link = f"{b.name}_{1:0{padding}d}.html"
            html_parts.append(f'<li><a class="link" href="{link}">{b.name}</a>\n')
            if b.nested_boards:
                html_parts.append(board_tree_to_html(b.nested_boards, depth + 1))
            html_parts.append("</li>\n")
        html_parts.append("</ul>\n")
        return "".join(html_parts)

    nested_html = board_tree_to_html(root_boards)

    html_content = index_template.replace("{{ index_links }}", nested_html)
    html_content = html_content.replace("{{ version }}", __version__)
    html_content = html_content.replace("{{ timestamp }}", timestamp)

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

        if ext in (".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".heic"):
            block = imgTemplate.render(media_path=media_path, hash=hash)
        elif ext in (".mp4", ".avi", ".mov", ".webm"):
            block = vidTemplate.render(media_path=media_path, hash=hash)
        else:
            block = imgTemplate.render(media_path=media_path, hash=hash)

        media_blocks.append(block)

    pagination_html = ""
    if p.total_pages > 1:
        pages = 1
        pagination_html += '<div class="pagination">\n'
        for i in range(1, p.total_pages + 1):
            page_file = os.path.basename(p.file_location).replace(
                f"_{p.page_number:0{padding}}", f"_{i:03}"
            )
            if i == p.page_number:
                pagination_html += f"<strong>{i}</strong> "
            else:
                pagination_html += f'<a href="{page_file}">{i}</a> '
            if pages % 15 == 0:
                pagination_html += "\n"
        pagination_html += "</div>"

    with open("templates/template.html", encoding="utf-8") as f:
        base_template = Template(f.read())

    final_html = base_template.render(
        title=f"Page {p.page_number} of {p.total_pages}",
        media_content="\n".join(media_blocks),
        pagination=pagination_html,
        back_button=f'<a class="button" href="{back_href}">⬅ Back to Index</a>',
        version=__version__,
        timestamp=timestamp,
    )
    # final_html = final_html.replace("{{ version }}", __version__)
    # final_html = final_html.replace("{{ timestamp }}", timestamp)

    logger.debug("Writing file at: " + p.file_location)
    with open(p.file_location, "w", encoding="utf-8") as f:
        f.write(final_html)

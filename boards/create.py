from jinja2 import Template
import os

from boards.log_utils import setup_logger
logger = setup_logger(__name__)

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
padding = config['padding']

imgTemplate = Template(imageBlock)
vidTemplate = Template(videoBlock)

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

def create_index_file(root_boards, target_directory, template_path='templates/index_template.html'):
    from collections import defaultdict
    import os

    index_file = os.path.join(target_directory, "index.html")

    # Load the HTML template
    with open(template_path, "r", encoding="utf-8") as template:
        index_template = template.read()

    # Recursive HTML tree generation
    def board_tree_to_html(boards):
        html = "<ul>\n"
        for b in boards:
            html += f'<li><a class="link" href="{b.name}_{1:0{padding}d}.html">{b.name}</a>\n'
            if b.nested_boards:
                html += board_tree_to_html(b.nested_boards)
            html += "</li>\n"
        html += "</ul>\n"
        return html

    nested_html = board_tree_to_html(root_boards)

    # Replace template placeholder with generated HTML
    html_content = index_template.replace("{{ index_links }}", nested_html)

    # Write index file
    with open(index_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    logger.info(f'index file created, location is - {index_file}')

def create_html_file(p):
    media_blocks = []
    logger.info(f'images - {p.images}')
    for idx, media_path in enumerate(p.images):
        ext = os.path.splitext(media_path)[1].lower()

        # hash = getattr(p, 'hashes', {}).get(media_path, media_path) if upload else media_path
        hash = media_path

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
            page_file = os.path.basename(p.file_location).replace(f'_{p.page_number:0{padding}}', f'_{i:03}')
            
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

    # os.makedirs(os.path.dirname(p.file_location), exist_ok=True)
    print(p.file_location)
    with open(p.file_location, "w", encoding="utf-8") as f:
        f.write(final_html)





## old 

# def create_master_index(directories, output_path, template_path='templates/master_index_template.html'):
#     css_filename = "styles.css"

#     # Prepare links: List of (name, link)
#     links = []
#     for d in directories:
#         target_dir = d.target_directory if hasattr(d, 'target_directory') else d["target_directory"]
#         index_file = target_dir + '_001.html'
#         folder_name = os.path.basename(target_dir)
#         links.append((folder_name, index_file))

#     # Load and render template
#     with open(template_path, "r", encoding="utf-8") as f:
#         template = Template(f.read())

#     rendered_html = template.render(css_filename=css_filename, links=links)

#     # Ensure the output directory exists
#     os.makedirs(os.path.dirname(output_path), exist_ok=True)
#     with open(output_path, "w", encoding="utf-8") as f:
#         f.write(rendered_html)

# def create_index_file(subfolders, target_directory, template_path='templates/index_template.html'):
#     index_file = os.path.join(target_directory, "index.html")

#     with open(template_path, "r", encoding="utf-8") as template:
#         index_template = template.read()

#     # Convert subfolder list into a nested tree
#     def build_tree(paths):
#         tree = defaultdict(dict)
#         for path in paths:
#             parts = path.split(os.sep)
#             current = tree
#             for part in parts:
#                 current = current.setdefault(part, {})
#         return tree

#     # Recursively turn tree into nested HTML
#     def tree_to_html(tree, path_prefix=""):
#         html = "<ul>\n"
#         for name in sorted(tree.keys()):
#             file_link = f"{name.replace(os.sep, '_')}_001.html"  # always links to page 1
#             if tree[name]:  # has children
#                 html += f'<li><a class="link" href="{file_link}">{name}\n{tree_to_html(tree[name], os.path.join(path_prefix, name))}</a></li>\n'
#             else:
#                 html += f'<li><a class="link" href="{file_link}">{name}</a></li>\n'
#         html += "</ul>\n"
#         return html

#     folder_tree = build_tree(subfolders)
#     nested_html = tree_to_html(folder_tree)

#     html_content = index_template.replace("{{  index_links  }}", nested_html)
#     with open(index_file, "w", encoding="utf-8") as f:
#         f.write(html_content)

# def create_index_file(b, target_directory, template_path='templates/index_template.html'):
#     index_file = os.path.join(target_directory, f"{b.name}.html")

#     subfolders = b.subfolders

#     with open(template_path, "r", encoding="utf-8") as template:
#         index_template = template.read()

#     def build_tree(paths):
#         tree = defaultdict(dict)
#         for path in paths:
#             parts = path.split(os.sep)
#             current = tree
#             for part in parts:
#                 current = current.setdefault(part, {})
#         return tree

#     def tree_to_html(tree):
#         html = "<ul>\n"
#         for name in sorted(tree.keys()):
#             baseName = os.path.basename(name)
#             file_link = f"{baseName}.html"
#             if tree[name]:  # has children
#                 html += f'<li><a class="link" href="{file_link}">{name}\n{tree_to_html(tree[name])}</a></li>\n'
#             else:
#                 html += f'<li><a class="link" href="{file_link}">{name}</a></li>\n'
#         html += "</ul>\n"
#         return html

#     folder_tree = build_tree(subfolders)
#     nested_html = tree_to_html(folder_tree)

#     html_content = index_template.replace("{{  index_links  }}", nested_html)
#     with open(index_file, "w", encoding="utf-8") as f:
#         f.write(html_content)
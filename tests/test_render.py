from html.parser import HTMLParser

from pixBoards.classes import Board
from pixBoards.create import breadcrumb, pagination, render_index, render_page
from pixBoards.media import MediaItem

CONFIG = {
    "padding": 3,
    "default_layout": "justified",
    "col_count": 4,
    "row_height": 200,
    "margin": 10,
    "lazy_loading": True,
}


class Collector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    def find(self, tag, **attrs):
        return [
            a for t, a in self.tags if t == tag and all(a.get(k) == v for k, v in attrs.items())
        ]


def parse(html):
    c = Collector()
    c.feed(html)
    return c


def test_breadcrumb():
    assert breadcrumb("", 3) == [("index", "index.html")]
    assert breadcrumb("a_~b_~c", 3) == [
        ("index", "index.html"),
        ("a", "a_001.html"),
        ("b", "a_~b_001.html"),
        ("c", None),
    ]


def test_pagination_window_and_links():
    b = Board("x", "/o", [MediaItem(f"http://h/{i}.jpg") for i in range(30)]).paginate(1, 3)
    p = pagination(b.pages[14], 3)  # page 15 of 30
    assert [n for n, _ in p["pages"]] == list(range(10, 21))
    assert p["first"] == "x_001.html" and p["last"] == "x_030.html"
    assert p["prev"] == "x_014.html" and p["next"] == "x_016.html"
    first = pagination(b.pages[0], 3)
    assert first["first"] is None and first["prev"] is None
    single = Board("y", "/o", [MediaItem("http://h/a.jpg")]).paginate(5, 3)
    assert pagination(single.pages[0], 3) is None


def test_page_escapes_names_and_has_random_button():
    evil = 'x" onerror="alert(1)<b>.jpg'
    items = [
        MediaItem("http://h/1.jpg", width=200, height=100, hash="abc"),
        MediaItem("http://h/" + evil.replace(" ", "%20")),
        MediaItem("http://h/clip.webm"),
    ]
    board = Board("we'ird <board>", "/o", items * 3).paginate(4, 3)
    html = render_page(board.pages[0], CONFIG, "now")
    doc = parse(html)

    assert "<b>" not in html and 'onerror="alert' not in html
    imgs = [a for a in doc.find("img") if a.get("title")]  # gallery images, not the lightbox
    assert imgs[1]["alt"] == 'x" onerror="alert(1)<b>.jpg'  # escaped, then decoded by the parser
    assert doc.find("div", **{"class": "item", "data-ar": "2.0000"})
    assert doc.find("a", **{"data-copy": "abc"})
    assert doc.find("source", type="video/webm")
    assert all(i.get("loading") == "lazy" for i in imgs)

    buttons = doc.find("button", **{"class": "random-page-btn"})
    assert len(buttons) == 2  # under the counts and in the pagination bar
    assert buttons[0]["data-prefix"] == "we'ird <board>_"
    assert buttons[0]["data-total"] == "3"
    assert doc.find("link", rel="next")[0]["href"] == "we%27ird%20%3Cboard%3E_002.html"
    assert doc.find("body")[0]["data-layout"] == "justified"


def test_single_page_has_no_random_button():
    board = Board("one", "/o", [MediaItem("http://h/a.jpg")]).paginate(10, 3)
    html = render_page(board.pages[0], CONFIG, "now")
    assert "random-page-btn" not in html


def test_index_tree():
    root = Board("r", "/o", [], dummy=True)
    child = Board("r_~c", "/o", [MediaItem("http://h/a.jpg")])
    root.nested_boards.append(child)
    doc = parse(render_index([root], CONFIG, "now"))
    assert [a["href"] for a in doc.find("a", **{"class": "link"})] == [
        "r_001.html",
        "r_~c_001.html",
    ]
    assert doc.find("img", **{"class": "thumb", "src": "http://h/a.jpg"})
    assert doc.find("details")
    assert doc.find("input", id="boardSearch")

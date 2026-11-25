// pixBoards page script (static; per-page settings come from data-* attributes).
"use strict";

// ---------------------------------------------------------------------------
// Settings: localStorage with a cookie fallback (file:// pages in some
// browsers have no localStorage).
// ---------------------------------------------------------------------------
function setSetting(name, value, days = 365) {
    try { localStorage.setItem(name, value); } catch (e) {}
    try {
        const d = new Date();
        d.setTime(d.getTime() + days * 24 * 60 * 60 * 1000);
        document.cookie = `${name}=${encodeURIComponent(value)};expires=${d.toUTCString()};path=/`;
    } catch (e) {}
}

function getSetting(name, defaultValue = null) {
    try {
        const value = localStorage.getItem(name);
        if (value !== null) return value;
    } catch (e) {}
    try {
        const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
        if (match) return decodeURIComponent(match[2]);
    } catch (e) {}
    return defaultValue;
}

// ---------------------------------------------------------------------------
// Clipboard + toast
// ---------------------------------------------------------------------------
let toastTimer = null;
function toast(message) {
    const el = document.getElementById("toast");
    if (!el) return;
    el.textContent = message;
    el.classList.add("visible");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.remove("visible"), 1200);
}

function copyToClipboard(text) {
    const fallback = () => {
        const ta = document.createElement("textarea");
        ta.value = text;
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        let ok = false;
        try { ok = document.execCommand("copy"); } catch (e) {}
        ta.remove();
        toast(ok ? "Copied" : "Copy failed");
    };
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(() => toast("Copied"), fallback);
    } else {
        fallback();
    }
}

// ---------------------------------------------------------------------------
// Page navigation helpers
// ---------------------------------------------------------------------------
function pageFile(prefix, padding, page) {
    return encodeURIComponent(prefix + String(page).padStart(padding, "0") + ".html");
}

// Used by every "Random Page" button (data-total, data-current, data-padding, data-prefix).
function goToRandomPage(button) {
    const total = parseInt(button.dataset.total, 10);
    const current = parseInt(button.dataset.current, 10);
    if (!(total > 1)) return;
    let page = current;
    while (page === current) page = Math.floor(Math.random() * total) + 1;
    window.location.href = pageFile(button.dataset.prefix, parseInt(button.dataset.padding, 10), page);
}

// ---------------------------------------------------------------------------
// Justified layout. Every box gets exactly the image's aspect ratio, so with
// object-fit: contain nothing is cropped. Rows are filled edge to edge by
// either shrinking (one more image) or growing (one fewer) - whichever stays
// closer to the target height - but never grow beyond MAX_SCALE. The last row
// keeps the target height and stays left-aligned.
// ---------------------------------------------------------------------------
const MAX_SCALE = 1.4;
const PLACEHOLDER_AR = 1.5;

function aspectOf(item) {
    if (item.dataset.ar) return parseFloat(item.dataset.ar);
    const m = item.querySelector("img, video");
    const w = m && (m.naturalWidth || m.videoWidth);
    const h = m && (m.naturalHeight || m.videoHeight);
    return w && h ? w / h : PLACEHOLDER_AR;
}

function justifyGallery(container, rowHeight) {
    if (!container || !container.classList.contains("justified-container")) return;
    const gap = parseFloat(getComputedStyle(container).columnGap) || 6;
    const W = Math.floor(container.getBoundingClientRect().width);
    if (W <= 0) return;

    let row = [];   // {item, w} with w = width at rowHeight
    let sum = 0;

    const place = (items, total, fill) => {
        const avail = W - gap * (items.length - 1);
        let scale = avail / total;
        if (!fill) scale = Math.min(scale, 1);
        const h = Math.max(1, Math.floor(rowHeight * scale));
        let used = 0;
        items.forEach(({ item, w }, i) => {
            let px = Math.max(1, Math.floor(w * scale));
            if (fill && i === items.length - 1) px = Math.max(1, avail - used); // absorb rounding
            used += px;
            item.style.width = px + "px";
            item.style.height = h + "px";
        });
    };

    for (const item of container.children) {
        const w = rowHeight * aspectOf(item);
        const withSum = sum + w;
        const withAvail = W - gap * row.length;            // gaps if this item joins
        if (withSum < withAvail) {
            row.push({ item, w });
            sum = withSum;
            continue;
        }
        // Row is full: shrink with this item, or grow without it?
        const shrink = withAvail / withSum;                 // <= 1
        const grow = row.length ? (W - gap * (row.length - 1)) / sum : Infinity;
        if (grow <= MAX_SCALE && grow - 1 < 1 / shrink - 1) {
            place(row, sum, true);
            row = [{ item, w }];
            sum = w;
        } else {
            row.push({ item, w });
            place(row, withSum, true);
            row = [];
            sum = 0;
        }
    }
    if (row.length) {
        // last row: target height (shrunk only if it would overflow)
        const fits = sum + gap * (row.length - 1) <= W;
        place(row, sum, !fits);
    }
}

function clearJustified(container) {
    for (const item of container.children) {
        item.style.width = "";
        item.style.height = "";
    }
}

// ---------------------------------------------------------------------------
// Board page
// ---------------------------------------------------------------------------
function initBoardPage() {
    const body = document.body;
    const gallery = document.getElementById("gallery");
    if (!gallery) return;

    const colsInput = document.getElementById("columnCountInput");
    const heightInput = document.getElementById("rowHeightInput");
    const toggle = document.getElementById("toggleLayout");

    const valid = (l) => (l === "masonry" || l === "justified" ? l : null);
    // older versions stored "masonry-container" / "justified-container"
    const saved = (getSetting("layout") || "").replace("-container", "");
    let layout = valid(saved) || valid(body.dataset.layout) || "masonry";
    let cols = parseInt(getSetting("columns") || body.dataset.cols, 10) || 5;
    let rowHeight = parseInt(getSetting("rowHeight") || body.dataset.rowHeight, 10) || 240;

    let queued = false;
    const relayout = () => {
        if (queued) return;
        queued = true;
        requestAnimationFrame(() => {
            queued = false;
            if (layout === "justified") justifyGallery(gallery, rowHeight);
        });
    };

    const applyLayout = () => {
        gallery.classList.toggle("masonry-container", layout === "masonry");
        gallery.classList.toggle("justified-container", layout === "justified");
        body.dataset.activeLayout = layout;
        if (toggle) toggle.textContent = layout === "masonry" ? "Switch to Justified" : "Switch to Masonry";
        if (layout === "masonry") {
            clearJustified(gallery);
            body.style.setProperty("--cols", cols);
        } else {
            relayout();
        }
    };

    if (colsInput) {
        colsInput.value = cols;
        colsInput.addEventListener("input", () => {
            cols = Math.max(1, parseInt(colsInput.value || "1", 10));
            body.style.setProperty("--cols", cols);
            setSetting("columns", cols);
        });
    }
    if (heightInput) {
        heightInput.value = rowHeight;
        heightInput.addEventListener("input", () => {
            rowHeight = parseInt(heightInput.value, 10) || 240;
            setSetting("rowHeight", rowHeight);
            relayout();
        });
    }
    const toggleLayout = () => {
        layout = layout === "masonry" ? "justified" : "masonry";
        setSetting("layout", layout);
        applyLayout();
    };
    if (toggle) toggle.addEventListener("click", toggleLayout);

    // fade images in and re-justify once real sizes are known
    const markLoaded = (img) => img.classList.add("loaded");
    gallery.querySelectorAll("img").forEach((img) => { if (!img.complete) img.classList.add("fading"); });
    gallery.addEventListener("load", (e) => {
        if (e.target.tagName === "IMG") markLoaded(e.target);
        if (!e.target.closest(".item").dataset.ar) relayout();
    }, true);
    gallery.addEventListener("error", (e) => { if (e.target.tagName === "IMG") markLoaded(e.target); }, true);
    gallery.addEventListener("loadedmetadata", relayout, true);
    if ("ResizeObserver" in window) new ResizeObserver(relayout).observe(gallery);
    else window.addEventListener("resize", relayout);

    applyLayout();
    initSourceLinks();
    initLightbox(gallery);

    // jump-to-page forms
    document.querySelectorAll("form.jump").forEach((form) => {
        form.addEventListener("submit", (e) => {
            e.preventDefault();
            const total = parseInt(form.dataset.total, 10);
            const n = parseInt(form.elements.page.value, 10);
            if (!(n >= 1 && n <= total)) { toast(`Pages 1-${total}`); return; }
            window.location.href = pageFile(form.dataset.prefix, parseInt(form.dataset.padding, 10), n);
        });
    });

    document.querySelectorAll(".random-page-btn").forEach((b) =>
        b.addEventListener("click", () => goToRandomPage(b)));

    // keyboard shortcuts
    document.addEventListener("keydown", (e) => {
        if (e.defaultPrevented || e.ctrlKey || e.metaKey || e.altKey) return;
        if (e.target.closest("input, textarea, select")) return;
        if (!document.getElementById("lightbox").hidden) return;
        const link = (rel) => document.querySelector(`link[rel="${rel}"]`);
        if (e.key === "ArrowLeft" && link("prev")) window.location.href = link("prev").href;
        else if (e.key === "ArrowRight" && link("next")) window.location.href = link("next").href;
        else if (e.key === "r" || e.key === "R") {
            const b = document.querySelector(".random-page-btn");
            if (b) goToRandomPage(b);
        } else if (e.key === "j" || e.key === "J") toggleLayout();
    });
}

// ---------------------------------------------------------------------------
// "Open on Pinterest" links (off by default; config source_links sets the
// starting state, the toolbar checkbox overrides it per browser)
// ---------------------------------------------------------------------------
function sourceLinksOn() {
    return document.body.classList.contains("show-sources");
}

function sourceOf(mediaLink) {
    const item = mediaLink && mediaLink.closest(".item");
    return item ? item.dataset.source || null : null;
}

function initSourceLinks() {
    const input = document.getElementById("sourceLinksInput");
    const saved = getSetting("sourceLinks");
    const on = saved !== null ? saved === "true" : document.body.dataset.sourceLinks === "true";
    const apply = (value) => {
        document.body.classList.toggle("show-sources", value);
        if (input) input.checked = value;
        document.dispatchEvent(new Event("sourcelinkschange"));
    };
    apply(on && !!input);
    if (input) {
        input.addEventListener("change", () => {
            setSetting("sourceLinks", input.checked);
            apply(input.checked);
        });
    }
}

// ---------------------------------------------------------------------------
// Lightbox: click opens, Shift+click copies, Ctrl/Cmd/middle click = browser default
// ---------------------------------------------------------------------------
function initLightbox(gallery) {
    const box = document.getElementById("lightbox");
    if (!box) return;
    const img = box.querySelector("img");
    const links = () => [...gallery.querySelectorAll(".item > a.media")];
    let index = -1;

    const updateLightboxSource = () => {
        const link = box.querySelector(".lb-source");
        const url = sourceOf(links()[index]);
        link.hidden = !(url && sourceLinksOn());
        if (url) link.href = url;
    };
    document.addEventListener("sourcelinkschange", () => { if (!box.hidden) updateLightboxSource(); });

    const show = (i) => {
        const all = links();
        if (!all.length) return;
        index = (i + all.length) % all.length;
        const a = all[index];
        img.src = a.href;
        img.alt = a.querySelector("img").alt;
        box.querySelector(".lb-name").textContent = img.alt;
        box.querySelector(".lb-count").textContent = `${index + 1} / ${all.length}`;
        box.querySelector(".lb-open").href = a.href;
        updateLightboxSource();
        box.hidden = false;
        document.body.style.overflow = "hidden";
    };
    const close = () => {
        box.hidden = true;
        img.removeAttribute("src");
        document.body.style.overflow = "";
    };

    gallery.addEventListener("click", (e) => {
        const a = e.target.closest(".item > a.media");
        if (!a || e.button !== 0 || e.ctrlKey || e.metaKey || e.altKey) return;
        e.preventDefault();
        if (e.shiftKey) copyToClipboard(a.dataset.copy || a.href);
        else show(links().indexOf(a));
    });

    box.querySelector(".lb-close").addEventListener("click", close);
    box.querySelector(".lb-prev").addEventListener("click", () => show(index - 1));
    box.querySelector(".lb-next").addEventListener("click", () => show(index + 1));
    box.querySelector(".lb-copy").addEventListener("click", () => {
        const a = links()[index];
        if (a) copyToClipboard(a.dataset.copy || a.href);
    });
    box.addEventListener("click", (e) => { if (e.target === box) close(); });
    document.addEventListener("keydown", (e) => {
        if (box.hidden) return;
        if (e.key === "Escape") close();
        else if (e.key === "ArrowLeft") show(index - 1);
        else if (e.key === "ArrowRight") show(index + 1);
        else if ((e.key === "p" || e.key === "P") && sourceLinksOn()) {
            const url = sourceOf(links()[index]);
            if (url) window.open(url, "_blank", "noopener,noreferrer");
        }
        else return;
        e.preventDefault();
    });
}

// ---------------------------------------------------------------------------
// Shared: back-to-top, index search
// ---------------------------------------------------------------------------
function initBackToTop() {
    const btn = document.getElementById("backToTop");
    if (!btn) return;
    const update = () => btn.classList.toggle("visible", window.scrollY > window.innerHeight);
    window.addEventListener("scroll", update, { passive: true });
    btn.addEventListener("click", () => window.scrollTo({ top: 0 }));
    update();
}

function initIndexSearch() {
    const input = document.getElementById("boardSearch");
    if (!input) return;
    const items = [...document.querySelectorAll(".board-tree li")];
    const empty = document.querySelector(".board-tree .no-results");
    input.addEventListener("input", () => {
        const q = input.value.trim().toLowerCase();
        if (q) document.querySelectorAll(".board-tree details").forEach((d) => { d.open = true; });
        // a board stays visible if it or anything below it matches
        let shown = 0;
        for (const li of items.slice().reverse()) {
            const match = !q || li.dataset.name.includes(q) || li.querySelector("li:not([hidden])");
            li.hidden = !match;
            if (match) shown++;
        }
        if (empty) empty.hidden = shown > 0;
    });
}

document.addEventListener("DOMContentLoaded", () => {
    initBoardPage();
    initBackToTop();
    initIndexSearch();
});

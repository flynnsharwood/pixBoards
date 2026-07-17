

function copyToClipboard(text) {
    navigator.clipboard.writeText(text);
}

// Cookie helpers
function setCookie(name, value, days = 365) {
  const d = new Date();
  d.setTime(d.getTime() + (days * 24 * 60 * 60 * 1000));
  document.cookie = `${name}=${value};expires=${d.toUTCString()};path=/`;
}

function getCookie(name) {
  const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
  return match ? match[2] : null;
}

// Column count apply
function applyColumnCount(gallery, count) {
  if (!gallery || !count) return;
  gallery.style.setProperty("--cols", count);
  if (gallery.classList.contains("masonry-container")) {
    gallery.style.columnCount = count;
  }
}

document.addEventListener("DOMContentLoaded", function () {
  const input   = document.getElementById("columnCountInput");
  const gallery = document.getElementById("gallery");
  const toggleButton = document.getElementById("toggleLayout");

// Restore saved settings
const savedCols = parseInt(getSetting("columns") || "{{ col_count }}", 10);

// strict layout validation
const layoutCookie = getSetting("layout");
const savedLayout =
  layoutCookie === "masonry-container" || layoutCookie === "justified-container"
    ? layoutCookie
    : "masonry-container";

if (gallery) {
  // reset classes
  gallery.classList.remove("masonry-container", "justified-container");
  gallery.classList.add(savedLayout);

  const items = gallery.querySelectorAll(":scope > div");

  // sync children classes
  items.forEach(item => {
    item.classList.toggle("masonry-item", savedLayout === "masonry-container");
    item.classList.toggle("justified-item", savedLayout === "justified-container");
    item.style.flex = ""; // reset any leftover flex
  });

  // apply correct layout behavior
  if (savedLayout === "masonry-container") {
    applyColumnCount(gallery, savedCols);
  } else {
    justifyGallery(".justified-container");
  }
}

if (input) input.value = savedCols;

// fix button label on load
if (toggleButton && gallery) {
  toggleButton.textContent =
    savedLayout === "masonry-container"
      ? "Switch to Justified"
      : "Switch to Masonry";
}

  // Column count change
  if (input && gallery) {
    input.addEventListener("input", function () {
      const count = Math.max(1, parseInt(input.value || "1", 10));
      applyColumnCount(gallery, count);
      setSetting("columns", count);
    });
  }

  // Toggle layout
  if (toggleButton && gallery) {
    toggleButton.addEventListener("click", () => {
      const isMasonry = gallery.classList.contains("masonry-container");
      const newClass  = isMasonry ? "justified-container" : "masonry-container";
      const oldClass  = isMasonry ? "masonry-container" : "justified-container";

      gallery.classList.remove(oldClass);
      gallery.classList.add(newClass);

      toggleButton.textContent = isMasonry ? "Switch to Masonry" : "Switch to Justified";
      setSetting("layout", newClass);

      // Update children classes
      const items = gallery.querySelectorAll(":scope > div");
      items.forEach(item => {
        item.classList.toggle("masonry-item", !isMasonry);
        item.classList.toggle("justified-item", isMasonry);
        if (isMasonry) item.style.flex = ""; // clear leftover flex
      });

      // Reapply column count if masonry
      if (!isMasonry && input) {
        const count = Math.max(1, parseInt(input.value || "1", 10));
        applyColumnCount(gallery, count);
      }

      // Justify if switching to justified
      if (isMasonry) {
        justifyGallery(".justified-container");
      }
    });
  }
});

// Justified layout logic
function justifyGallery(containerSelector, rowHeight = {{ just_height }}, gap = 6) {
  const container = document.querySelector(containerSelector);
  if (!container) return;

  const items = [...container.children];
  let row = [];
  let rowWidth = 0;
  const containerWidth = container.clientWidth - gap;

  items.forEach((item, i) => {
    const img = item.querySelector("img, video");
    if (!img) return;

    const aspectRatio = img.naturalWidth / img.naturalHeight || 1;
    const itemWidth = rowHeight * aspectRatio;

    row.push({ item, width: itemWidth });
    rowWidth += itemWidth + gap;

    if (rowWidth >= containerWidth || i === items.length - 1) {
      const scale = (containerWidth - gap * (row.length - 1)) / (rowWidth - gap);
      row.forEach(({ item, width }) => {
        item.style.flex = `0 0 ${width * scale}px`;
      });
      row = [];
      rowWidth = 0;
    }
  });
}

window.addEventListener("load", () => {
  justifyGallery(".justified-container");
});
window.addEventListener("resize", () => {
  justifyGallery(".justified-container");
});

function setSetting(name, value, days = 365) {
    // localStorage
    try {
        localStorage.setItem(name, value);
    } catch (e) {}

    // cookie
    try {
        const d = new Date();
        d.setTime(d.getTime() + (days * 24 * 60 * 60 * 1000));
        document.cookie =
            `${name}=${encodeURIComponent(value)};expires=${d.toUTCString()};path=/`;
    } catch (e) {}
}

function getSetting(name, defaultValue = null) {
    // Prefer localStorage
    try {
        const value = localStorage.getItem(name);
        if (value !== null) {
            return value;
        }
    } catch (e) {}

    // Fallback to cookie
    try {
        const match = document.cookie.match(
            new RegExp("(^| )" + name + "=([^;]+)")
        );

        if (match) {
            return decodeURIComponent(match[2]);
        }
    } catch (e) {}

    return defaultValue;
}

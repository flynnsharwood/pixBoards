

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
  const savedCols = parseInt(getCookie("columns") || "{{ col_count }}", 10);
  const savedLayout = getCookie("layout") || "masonry-container";

  if (gallery) {
    gallery.classList.remove("masonry-container", "justified-container");
    gallery.classList.add(savedLayout);
    applyColumnCount(gallery, savedCols);
  }
  if (input) input.value = savedCols;

  // Column count change
  if (input && gallery) {
    input.addEventListener("input", function () {
      const count = Math.max(1, parseInt(input.value || "1", 10));
      applyColumnCount(gallery, count);
      setCookie("columns", count);
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
      setCookie("layout", newClass);

      // Update children classes
      const items = gallery.querySelectorAll(":scope > div");
      items.forEach(item => {
        item.classList.toggle("masonry-item", !isMasonry);
        item.classList.toggle("justified-item", isMasonry);
        if (!isMasonry) item.style.flex = ""; // clear leftover flex
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
function justifyGallery(containerSelector, rowHeight = 240, gap = 6) {
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



// function copyToClipboard(text) {
//     navigator.clipboard.writeText(text)
// }

// function applyColumnCount(gallery, count) {
//   if (!gallery || !count) return;
//   gallery.style.setProperty('--cols', count);
//   // also set direct style when in masonry (helps older browsers)
//   if (gallery.classList.contains('masonry-container')) {
//     gallery.style.columnCount = count;
//   }
// }


// document.addEventListener("DOMContentLoaded", function () {
//   const input   = document.getElementById("columnCountInput");
//   const gallery = document.getElementById("gallery");

//   if (input && gallery) {
//     // initialize from current input value
//     const initial = parseInt(input.value || "{{ col_count }}", 10);
//     applyColumnCount(gallery, initial);

//     input.addEventListener("input", function () {
//       const count = Math.max(1, parseInt(input.value || "1", 10));
//       applyColumnCount(gallery, count);
//     });
//   }

//   const toggleButton = document.getElementById("toggleLayout");
//   if (!gallery || !toggleButton) return;

//   toggleButton.addEventListener("click", () => {
//     const isMasonry = gallery.classList.contains("masonry-container");
//     const newClass  = isMasonry ? "justified-container" : "masonry-container";
//     const oldClass  = isMasonry ? "masonry-container" : "justified-container";

//     gallery.classList.remove(oldClass);
//     gallery.classList.add(newClass);

//     toggleButton.textContent = isMasonry ? "Switch to Masonry" : "Switch to Justified";

//     // update children classes
//     const items = gallery.querySelectorAll(":scope > div"); // only direct children
//     items.forEach(item => {
//       item.classList.toggle("masonry-item", !isMasonry);
//       item.classList.toggle("justified-item", isMasonry);
//       // clear flex basis leftovers when going back to masonry
//       if (!isMasonry) item.style.flex = "";
//     });

//     // re-apply column count if we just switched to masonry
//     if (!isMasonry && input) {
//       const count = Math.max(1, parseInt(input.value || "1", 10));
//       applyColumnCount(gallery, count);
//     }

//     // run justification logic when switching to justified
//     if (isMasonry) {
//       justifyGallery(".justified-container");
//     }
//   });
// });

// function goToPage(page) {
//     const base = window.location.pathname.replace(/_\d+\.html$/, '');
//     window.location.href = `${base}_${page}.html`;
// }

// document.addEventListener("DOMContentLoaded", function () {
//   const toggleButton = document.getElementById("toggleLayout");
//   const gallery = document.getElementById("gallery");

//   if (!gallery || !toggleButton) return;

//   toggleButton.addEventListener("click", () => {
//     const isMasonry = gallery.classList.contains("masonry-container");
//     const newClass = isMasonry ? "justified-container" : "masonry-container";
//     const oldClass = isMasonry ? "masonry-container" : "justified-container";

//     gallery.classList.remove(oldClass);
//     gallery.classList.add(newClass);

//     toggleButton.textContent = isMasonry ? "Switch to Masonry" : "Switch to Justified";

//     // update children classes
//     const items = gallery.querySelectorAll("div");
//     items.forEach(item => {
//       item.classList.toggle("masonry-item", !isMasonry);
//       item.classList.toggle("justified-item", isMasonry);
//     });

//     // run justification logic when switching
//     if (!isMasonry) {
//       justifyGallery(".justified-container");
//     }
//   });
// });


// function justifyGallery(containerSelector, rowHeight = 240, gap = 6) {
//   const container = document.querySelector(containerSelector);
//   if (!container) return;

//   const items = [...container.children];
//   let row = [];
//   let rowWidth = 0;
//   const containerWidth = container.clientWidth - gap; 

//   items.forEach((item, i) => {
//     const img = item.querySelector("img, video");
//     if (!img) return;

//     const aspectRatio = img.naturalWidth / img.naturalHeight;
//     const itemWidth = rowHeight * aspectRatio;

//     row.push({ item, width: itemWidth });
//     rowWidth += itemWidth + gap;

//     if (rowWidth >= containerWidth || i === items.length - 1) {
//       // scale row to fit perfectly
//       const scale = (containerWidth - gap * (row.length - 1)) / (rowWidth - gap);
//       row.forEach(({ item, width }) => {
//         item.style.flex = `0 0 ${width * scale}px`;
//       });
//       row = [];
//       rowWidth = 0;
//     }
//   });
// }

// window.addEventListener("load", () => {
//   justifyGallery(".justified-container");
// });

// window.addEventListener("resize", () => {
//   justifyGallery(".justified-container");
// });


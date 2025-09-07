// --- Cookie helpers ---
function setCookie(name, value, days) {
  let expires = "";
  if (days) {
    const d = new Date();
    d.setTime(d.getTime() + days * 24 * 60 * 60 * 1000);
    expires = "; expires=" + d.toUTCString();
  }
  document.cookie = name + "=" + (value || "") + expires + "; path=/";
}

function getCookie(name) {
  const nameEQ = name + "=";
  const ca = document.cookie.split(";");
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i].trim();
    if (c.indexOf(nameEQ) === 0)
      return c.substring(nameEQ.length, c.length);
  }
  return null;
}

// --- Apply column count ---
function applyColumnCount(gallery, count) {
  if (!gallery || !count) return;
  gallery.style.setProperty("--cols", count);
  if (gallery.classList.contains("masonry-container")) {
    gallery.style.columnCount = count;
  }
}

// --- Justified layout logic ---
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

    const aspectRatio = img.naturalWidth / img.naturalHeight;
    const itemWidth = rowHeight * aspectRatio;

    row.push({ item, width: itemWidth });
    rowWidth += itemWidth + gap;

    if (rowWidth >= containerWidth || i === items.length - 1) {
      const scale =
        (containerWidth - gap * (row.length - 1)) / (rowWidth - gap);
      row.forEach(({ item, width }) => {
        item.style.flex = `0 0 ${width * scale}px`;
      });
      row = [];
      rowWidth = 0;
    }
  });
}

// // --- Justified layout logic ---
// function justifyGallery(containerSelector, rowHeight = 240, gap = 6) {
//   const container = document.querySelector(containerSelector);
//   if (!container || !container.classList.contains("justified-container")) return;

//   const items = [...container.children];
//   if (items.length === 0) return;

//   // Reset styles for justified
//   items.forEach(item => {
//     item.style.flex = "";
//     item.style.height = "";   // reset first
//   });

//   let row = [];
//   let rowWidth = 0;
//   const containerWidth = container.clientWidth - gap;

//   items.forEach((item, i) => {
//     const img = item.querySelector("img, video");
//     if (!img || !img.naturalWidth || !img.naturalHeight) return;

//     const aspectRatio = img.naturalWidth / img.naturalHeight;
//     const itemWidth = rowHeight * aspectRatio;  // proportional width

//     row.push({ item, width: itemWidth });
//     rowWidth += itemWidth + gap;

//     if (rowWidth >= containerWidth || i === items.length - 1) {
//       const scale =
//         (containerWidth - gap * (row.length - 1)) / (rowWidth - gap);

//       row.forEach(({ item, width }) => {
//         item.style.flex = `0 0 ${width * scale}px`;
//         item.style.height = rowHeight * scale + "px";  
//       });

//       row = [];
//       rowWidth = 0;
//     }
//   });
// }




// --- Init ---
document.addEventListener("DOMContentLoaded", function () {
  const gallery = document.getElementById("gallery");
  const toggleButton = document.getElementById("toggleLayout");
  const input = document.getElementById("columnCountInput");
  const rowHeightInput = document.getElementById("rowHeightInput");


  if (!gallery) return;

  
  // if (rowHeightInput) {
  //   rowHeightInput.addEventListener("input", () => {
  //     const newHeight = parseInt(rowHeightInput.value, 10) || 240;
  //     justifyGallery(".justified-container", newHeight);
  //     setCookie("rowHeight", newHeight, 30);
  //   });
  // }
  
  if (rowHeightInput) {
    const rowHeightValue = document.getElementById("rowHeightValue");
    rowHeightInput.addEventListener("input", () => {
      const newHeight = parseInt(rowHeightInput.value, 10) || 240;
      justifyGallery(".justified-container", newHeight);
      setCookie("rowHeight", newHeight, 30);
      if (rowHeightValue) rowHeightValue.textContent = newHeight;
    });
  }
  // restore saved height
  const savedRowHeight = parseInt(getCookie("rowHeight") || "240", 10);
  if (rowHeightInput) rowHeightInput.value = savedRowHeight;
  justifyGallery(".justified-container", savedRowHeight);

  // Restore saved layout
  let savedLayout = getCookie("layout") || "masonry";
  gallery.classList.add(savedLayout + "-container");

  // Restore column count
  let savedCols = parseInt(getCookie("columns") || "3", 10);
  applyColumnCount(gallery, savedCols);
  if (input) input.value = savedCols;

  // Handle column input change
  if (input) {
    input.addEventListener("input", function () {
      const count = Math.max(1, parseInt(this.value || "1", 10));
      applyColumnCount(gallery, count);
      setCookie("columns", count, 30);
    });
  }

  // Handle toggle button
  if (toggleButton) {
    toggleButton.textContent =
      savedLayout === "masonry" ? "Switch to Justified" : "Switch to Masonry";

    toggleButton.addEventListener("click", () => {
      const isMasonry = gallery.classList.contains("masonry-container");
      const newClass = isMasonry
        ? "justified-container"
        : "masonry-container";
      const oldClass = isMasonry
        ? "masonry-container"
        : "justified-container";

      // Switch container
      gallery.classList.remove(oldClass);
      gallery.classList.add(newClass);

      // Switch items
      const items = gallery.children;
      for (let item of items) {
        if (isMasonry) {
          // switching to justified
          item.classList.remove("masonry-item");
          item.classList.add("justified-item");
        } else {
          // switching to masonry
          item.classList.remove("justified-item");
          item.classList.add("masonry-item");
        }
      }

      toggleButton.textContent = isMasonry
        ? "Switch to Masonry"
        : "Switch to Justified";

      setCookie("layout", isMasonry ? "justified" : "masonry", 30);

      if (!isMasonry) {
        // Re-apply column count in masonry
        const count = Math.max(
          1,
          parseInt(input?.value || savedCols || "3", 10)
        );
        applyColumnCount(gallery, count);
      } else {
        // Re-apply justified layout with current rowHeight
        const currentHeight =
          parseInt(rowHeightInput?.value || savedRowHeight || "240", 10);
        justifyGallery(".justified-container", currentHeight);
      }
    });
  }
});

// // Re-run justified layout on load + resize
// window.addEventListener("load", () => {
//   justifyGallery(".justified-container");
// });
// window.addEventListener("resize", () => {
//   justifyGallery(".justified-container");
// });

// Re-run justified layout on load + resize
window.addEventListener("load", () => {
  const currentHeight =
    parseInt(document.getElementById("rowHeightInput")?.value || "240", 10);
  justifyGallery(".justified-container", currentHeight);
});

window.addEventListener("resize", () => {
  const currentHeight =
    parseInt(document.getElementById("rowHeightInput")?.value || "240", 10);
  justifyGallery(".justified-container", currentHeight);
});



//--------//



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


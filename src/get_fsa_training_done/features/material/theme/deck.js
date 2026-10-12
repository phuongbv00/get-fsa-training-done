/* The FSA deck viewer: one slide at a time, scaled to the window.
 *
 *   → ↓ Space PgDn   next         ← ↑ PgUp   previous
 *   Home / End       first / last  N          speaker notes
 *   O                overview      F          full screen
 *
 * No dependencies and no network, except Mermaid, fetched only when a diagram
 * has no rendered image beside it. Without this script, or when printing, every
 * slide is laid out in turn, one per page.
 */
(function () {
  "use strict";

  var SLIDE_PX = { width: 960, height: 540 }; /* 720pt x 405pt */
  var MERMAID = "https://cdn.jsdelivr.net/npm/mermaid@11.17.2/dist/mermaid.min.js";
  /* Pinned with its hash: the browser refuses a file that is not this one. */
  var MERMAID_SRI = "sha384-EOXBFmc3gx5mb+vn0vPvvGqACToJD24hhacX5Yx+8NUUQrHIle/Qi5Bg9o3zKwW2";

  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  /* A word in the page's language, from the custom properties layouts.css
   * generates from core/i18n.py. */
  function word(name, fallback) {
    var value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return value ? value.replace(/^"|"$/g, "") : fallback;
  }

  function slotText(slide, name) {
    var slot = slide.querySelector(':scope > [data-slot="' + name + '"]');
    return slot ? slot.textContent.replace(/\s+/g, " ").trim() : "";
  }

  /* The table of contents lists the section covers, as the template does: a
   * numbered circle and a title per row, placed by layouts.css. */
  function fillToc(slides) {
    var titles = slides
      .filter(function (s) { return s.dataset.layout === "section"; })
      .map(function (s) { return slotText(s, "title"); })
      .slice(0, 5);
    slides.forEach(function (slide) {
      if (slide.dataset.layout !== "toc" || slide.querySelector(".toc-rows")) return;
      var list = document.createElement("ol");
      list.className = "toc-rows";
      titles.forEach(function (title, index) {
        var item = document.createElement("li");
        var number = document.createElement("span");
        number.className = "toc-num";
        number.textContent = String(index + 1);
        var label = document.createElement("span");
        label.className = "toc-title";
        label.textContent = title;
        item.appendChild(number);
        item.appendChild(label);
        list.appendChild(item);
      });
      slide.appendChild(list);
    });
  }

  /* Slide and section numbers, as attributes: CSS counters skip the slides the
   * viewer hides, so the footer and the section covers read them from here. */
  function numberSlides(slides) {
    var section = 0;
    slides.forEach(function (slide, index) {
      slide.setAttribute("data-number", String(index + 1));
      if (slide.dataset.layout === "section") {
        section += 1;
        var title = slide.querySelector(':scope > [data-slot="title"]');
        if (title) title.setAttribute("data-section", (section < 10 ? "0" : "") + section);
      }
    });
  }

  /* Shrink a title or text slot in steps until it fits — the same estimate as
   * layouts.fit_scale, with its constants read from layouts.css, so the browser,
   * the .pptx and the .pdf pick the same size. */
  /* fit:begin — a port of layouts.lines_needed and layouts.fit_scale, kept free
   * of the DOM so tests/features/material/test_layouts.py can run it in Node and
   * compare it with the Python. */
  function linesNeeded(text, widthPt, size, charEm, spaceEm) {
    var total = 0;
    text.split("\n").forEach(function (paragraph) {
      var lines = 1;
      var used = 0;
      paragraph.split(/\s+/).filter(Boolean).forEach(function (word) {
        var width = word.length * charEm * size;
        if (used && used + spaceEm * size + width > widthPt) {
          lines += 1;
          used = 0;
        } else {
          used += used ? spaceEm * size : 0;
        }
        /* A word wider than the box breaks across lines (overflow-wrap). */
        while (used + width > widthPt && width > 0 && used === 0 && width > widthPt) {
          lines += 1;
          width -= widthPt;
        }
        used += width;
      });
      total += lines;
    });
    return Math.max(total, 1);
  }

  function pickScale(text, widthPt, heightPt, size, charEm, spaceEm, lineHeight, scales) {
    for (var i = 0; i < scales.length; i++) {
      var at = size * scales[i];
      var room = Math.max(1, Math.floor((heightPt + 0.5) / (at * lineHeight)));
      if (linesNeeded(text, widthPt, at, charEm, spaceEm) <= room) return scales[i];
    }
    return scales[scales.length - 1];
  }
  /* fit:end */

  function fitSlots(slides) {
    var root = getComputedStyle(document.documentElement);
    var num = function (name) { return parseFloat(root.getPropertyValue(name)); };
    var scales = root.getPropertyValue("--fit-scales").trim().split(/\s+/).map(parseFloat);
    var lineHeight = num("--slot-line-height");
    var insetX = num("--slot-inset-x");
    var insetY = num("--slot-inset-y");
    var pxToPt = 0.75;
    var section = 0;
    slides.forEach(function (slide) {
      if (slide.dataset.layout === "section") section += 1;
      slide.querySelectorAll(":scope > [data-slot]").forEach(function (slot) {
        var style = getComputedStyle(slot);
        if (style.getPropertyValue("--slot-fit").trim() !== "1") return;
        var text = slot.innerText.replace(/\r/g, "").trim();
        if (slide.dataset.layout === "section" && slot.dataset.slot === "title") {
          text = (section < 10 ? "0" : "") + section + ".\n" + text;
        }
        if (!text) return;
        var bold = parseInt(style.fontWeight, 10) >= 600;
        var charEm = num(bold ? "--fit-char-em-bold" : "--fit-char-em");
        var spaceEm = num("--fit-space-em");
        var size = parseFloat(style.getPropertyValue("--slot-size"));
        /* The computed width and height, unrounded: clientWidth would round
         * 595.2px down to 595 and drift from layouts.py's box. */
        var width = parseFloat(style.width) * pxToPt - 2 * insetX;
        var height = parseFloat(style.height) * pxToPt - 2 * insetY;
        var chosen = pickScale(text, width, height, size, charEm, spaceEm, lineHeight, scales);
        slot.style.setProperty("--fit", String(chosen));
      });
    });
  }

  /* Mermaid measures what it draws, so a diagram on a hidden slide is drawn
   * only once its slide is shown. */
  var mermaidState = "idle";
  var waiting = [];

  function pendingDiagrams(root) {
    return Array.prototype.filter.call(root.querySelectorAll("pre.mermaid"), function (pre) {
      var figure = pre.closest("figure");
      return !pre.hasAttribute("data-processed") && !(figure && figure.querySelector("img"));
    });
  }

  function drawDiagrams(root) {
    var nodes = pendingDiagrams(root);
    if (!nodes.length) return;
    if (mermaidState === "ready") {
      try { window.mermaid.run({ nodes: nodes }); } catch (err) { /* keep the source */ }
      return;
    }
    waiting.push(root);
    if (mermaidState !== "idle") return;
    mermaidState = "loading";
    var script = document.createElement("script");
    script.src = MERMAID;
    script.integrity = MERMAID_SRI;
    script.crossOrigin = "anonymous";
    script.onload = function () {
      window.mermaid.initialize({ startOnLoad: false, theme: "neutral" });
      mermaidState = "ready";
      waiting.splice(0).forEach(drawDiagrams);
    };
    script.onerror = function () { mermaidState = "failed"; };
    document.head.appendChild(script);
  }

  ready(function () {
    var body = document.body;
    var slides = Array.prototype.slice.call(document.querySelectorAll(".slide"));
    if (!slides.length) return;
    numberSlides(slides);
    fillToc(slides);
    fitSlots(slides);

    var current = 0;
    var hud = document.createElement("div");
    hud.className = "deck-hud";
    var notes = document.createElement("div");
    notes.className = "deck-notes";
    body.appendChild(hud);
    body.appendChild(notes);

    function scale() {
      var factor = Math.min(
        window.innerWidth / SLIDE_PX.width,
        window.innerHeight / SLIDE_PX.height
      ) * 0.96;
      body.style.setProperty("--deck-scale", factor.toFixed(4));
    }

    function show(index) {
      current = Math.max(0, Math.min(slides.length - 1, index));
      slides.forEach(function (slide, i) {
        slide.classList.toggle("is-current", i === current);
      });
      var aside = slides[current].querySelector(":scope > aside.notes");
      notes.innerHTML = aside
        ? aside.innerHTML
        : "<em>" + word("--t-no-notes", "No speaker notes for this slide.") + "</em>";
      drawDiagrams(slides[current]);
      hud.textContent =
        current + 1 + " / " + slides.length + "   " + word("--t-hint", "N notes · O overview");
      if (location.hash !== "#" + (current + 1)) {
        history.replaceState(null, "", "#" + (current + 1));
      }
    }

    function overview(on) {
      body.classList.toggle("is-overview", on);
      body.classList.toggle("is-presenting", !on);
      if (!on) show(current);
      else {
        drawDiagrams(document);
        slides[current].scrollIntoView({ block: "center" });
      }
    }

    body.classList.add("is-presenting");
    scale();
    var start = parseInt((location.hash || "").slice(1), 10);
    show(isNaN(start) ? 0 : start - 1);

    window.addEventListener("resize", scale);
    window.addEventListener("hashchange", function () {
      var n = parseInt(location.hash.slice(1), 10);
      if (!isNaN(n) && n - 1 !== current) show(n - 1);
    });
    slides.forEach(function (slide, i) {
      slide.addEventListener("click", function () {
        if (body.classList.contains("is-overview")) {
          current = i;
          overview(false);
        }
      });
    });

    document.addEventListener("keydown", function (event) {
      if (event.metaKey || event.ctrlKey || event.altKey) return;
      var key = event.key;
      if (["ArrowRight", "ArrowDown", "PageDown", " "].indexOf(key) >= 0) show(current + 1);
      else if (["ArrowLeft", "ArrowUp", "PageUp"].indexOf(key) >= 0) show(current - 1);
      else if (key === "Home") show(0);
      else if (key === "End") show(slides.length - 1);
      else if (key === "n" || key === "N") body.classList.toggle("show-notes");
      else if (key === "o" || key === "O") overview(!body.classList.contains("is-overview"));
      else if (key === "f" || key === "F") {
        if (document.fullscreenElement) document.exitFullscreen();
        else if (document.documentElement.requestFullscreen) document.documentElement.requestFullscreen();
      } else return;
      event.preventDefault();
    });

    window.addEventListener("beforeprint", function () {
      body.classList.remove("is-overview");
      drawDiagrams(document);
    });
  });
})();

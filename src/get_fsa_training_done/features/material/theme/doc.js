/* The FSA document helper: the header band, a line of facts under the title
 * read from the page's <meta name="fsa:..."> tags, tickable checklists, and
 * Mermaid for a diagram with no rendered image. Optional: without it the page
 * reads the same, minus those conveniences.
 */
(function () {
  "use strict";

  var MERMAID = "https://cdn.jsdelivr.net/npm/mermaid@11.17.2/dist/mermaid.min.js";
  /* Pinned with its hash: the browser refuses a file that is not this one. */
  var MERMAID_SRI = "sha384-EOXBFmc3gx5mb+vn0vPvvGqACToJD24hhacX5Yx+8NUUQrHIle/Qi5Bg9o3zKwW2";
  /* A word in the page's language, from the custom properties layouts.css
   * generates from core/i18n.py. */
  function word(name, fallback) {
    var value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return value ? value.replace(/^"|"$/g, "") : fallback;
  }

  function meta(name) {
    var el = document.querySelector('meta[name="' + name + '"]');
    return el ? (el.getAttribute("content") || "").trim() : "";
  }

  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  ready(function () {
    var body = document.body;
    if (!body.querySelector(":scope > header.doc-band")) {
      var band = document.createElement("header");
      band.className = "doc-band";
      body.insertBefore(band, body.firstChild);
    }

    var FACTS = [
      ["fsa:module", ""],
      ["fsa:session", word("--t-session", "Session") + " "],
      ["fsa:minutes", "", " " + word("--t-min", "min")],
      ["fsa:stack", ""],
    ];
    var title = document.querySelector("main h1, article h1");
    if (title && !document.querySelector(".doc-meta")) {
      var line = document.createElement("p");
      line.className = "doc-meta";
      FACTS.forEach(function (fact) {
        var value = meta(fact[0]);
        if (!value) return;
        var span = document.createElement("span");
        span.textContent = fact[1] + value + (fact[2] || "");
        line.appendChild(span);
      });
      if (line.childNodes.length) title.insertAdjacentElement("afterend", line);
    }

    document.querySelectorAll("ul.checklist > li").forEach(function (item) {
      item.addEventListener("click", function () { item.classList.toggle("is-done"); });
    });

    var pending = Array.prototype.filter.call(
      document.querySelectorAll("pre.mermaid"),
      function (pre) {
        var figure = pre.closest("figure");
        return !(figure && figure.querySelector("img"));
      }
    );
    if (pending.length) {
      var script = document.createElement("script");
      script.src = MERMAID;
      script.integrity = MERMAID_SRI;
      script.crossOrigin = "anonymous";
      script.onload = function () {
        try {
          var dark = window.matchMedia("(prefers-color-scheme: dark)").matches;
          window.mermaid.initialize({ startOnLoad: false, theme: dark ? "dark" : "neutral" });
          window.mermaid.run({ nodes: pending });
        } catch (err) { /* leave the source visible */ }
      };
      document.head.appendChild(script);
    }
  });
})();

(() => {
  const root = document.documentElement;
  const savedTheme = localStorage.getItem("okf-docs-theme");
  if (savedTheme === "dark" || (!savedTheme && matchMedia("(prefers-color-scheme: dark)").matches)) {
    root.dataset.theme = "dark";
  }

  document.querySelector(".theme-toggle")?.addEventListener("click", () => {
    const next = root.dataset.theme === "dark" ? "light" : "dark";
    root.dataset.theme = next;
    localStorage.setItem("okf-docs-theme", next);
  });

  const sidebar = document.querySelector(".sidebar");
  const navToggle = document.querySelector(".nav-toggle");
  navToggle?.addEventListener("click", () => {
    const open = sidebar?.classList.toggle("open") ?? false;
    navToggle.setAttribute("aria-expanded", String(open));
  });

  const search = document.querySelector("#doc-search");
  search?.addEventListener("input", () => {
    const query = search.value.trim().toLocaleLowerCase("ja");
    document.querySelectorAll(".site-nav li[data-search]").forEach((item) => {
      item.hidden = query !== "" && !item.dataset.search.includes(query);
    });
    document.querySelectorAll(".site-nav section").forEach((section) => {
      const visible = [...section.querySelectorAll("li")].some((item) => !item.hidden);
      section.hidden = !visible;
    });
  });

  const diagrams = document.querySelectorAll(".mermaid[data-mermaid-source]");
  if (diagrams.length) {
    import("https://cdn.jsdelivr.net/npm/mermaid@11.15.0/dist/mermaid.esm.min.mjs")
      .then(({ default: mermaid }) => {
        mermaid.initialize({ startOnLoad: false, securityLevel: "strict", theme: root.dataset.theme === "dark" ? "dark" : "default" });
        return mermaid.run({ nodes: diagrams });
      })
      .catch(() => {
        diagrams.forEach((diagram) => diagram.classList.add("mermaid-fallback"));
      });
  }

  document.querySelectorAll("a[href^='http']").forEach((link) => {
    link.target = "_blank";
    link.rel = "noopener noreferrer";
  });
})();

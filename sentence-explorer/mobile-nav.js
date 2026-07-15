(() => {
  const pageLinks = [
    ["./", "Theme Viewer"],
    ["sentences.html", "Sentence Atlas"],
    ["grammar.html", "Observation Index"],
    ["reconciliation.html", "Dedup Reconciliation"],
    ["cross-language.html", "Cross-Language Reference"],
    ["zh-a1-curriculum.html", "zh-TW A1"],
    ["th-a1-curriculum.html", "Thai A1"],
    ["th-vocab.html", "Thai Vocab 5K"],
  ];

  const topbar = document.querySelector(".topbar");
  const container = topbar || createFloatingNav();
  if (!topbar) {
    const keepFloatingNavMounted = () => {
      if (!container.isConnected) document.body.appendChild(container);
    };
    new MutationObserver(keepFloatingNavMounted).observe(document.body, { childList: true });
    window.addEventListener("load", keepFloatingNavMounted, { once: true });
  }
  const nav = container.querySelector(":scope > nav");
  if (!nav) return;
  if (topbar) nav.innerHTML = renderPageLinks();

  if (!nav.id) nav.id = "site-page-navigation";
  const toggle = document.createElement("button");
  toggle.className = "site-nav-toggle";
  toggle.type = "button";
  toggle.setAttribute("aria-controls", nav.id);
  toggle.setAttribute("aria-expanded", "false");
  toggle.setAttribute("aria-label", "開啟頁面選單");
  toggle.innerHTML = '<span class="site-nav-toggle__icon" aria-hidden="true"></span><span>Pages</span>';
  container.insertBefore(toggle, nav);

  const close = () => {
    container.classList.remove("site-nav-open");
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-label", "開啟頁面選單");
  };

  toggle.addEventListener("click", () => {
    const willOpen = !container.classList.contains("site-nav-open");
    container.classList.toggle("site-nav-open", willOpen);
    toggle.setAttribute("aria-expanded", String(willOpen));
    toggle.setAttribute("aria-label", willOpen ? "關閉頁面選單" : "開啟頁面選單");
  });
  nav.addEventListener("click", event => {
    if (event.target.closest("a")) close();
  });
  document.addEventListener("click", event => {
    if (!container.contains(event.target)) close();
  });
  document.addEventListener("keydown", event => {
    if (event.key === "Escape") close();
  });
  window.matchMedia("(min-width: 761px)").addEventListener("change", close);

  function createFloatingNav() {
    const shell = document.createElement("aside");
    shell.className = "floating-site-nav";
    shell.setAttribute("aria-label", "頁面切換");
    shell.innerHTML = `<nav>${renderPageLinks()}</nav>`;
    document.body.appendChild(shell);
    return shell;
  }

  function renderPageLinks() {
    const current = location.pathname.split("/").pop() || "index.html";
    return pageLinks.map(([href, label]) => {
      const target = href === "./" ? "index.html" : href;
      const active = current === target ? ' class="active" aria-current="page"' : "";
      return `<a href="${href}"${active}>${label}</a>`;
    }).join("");
  }
})();

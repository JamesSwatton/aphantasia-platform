(function () {
  const panels = document.querySelectorAll(".sidebar-panel");
  const navLinks = document.querySelectorAll(".view-switch a");
  if (!panels.length || !navLinks.length) return;

  navLinks.forEach(function (link) {
    link.addEventListener("click", function (e) {
      e.preventDefault();
      const target = link.textContent.trim().toLowerCase() === "info" ? "info" : "domains";
      panels.forEach(function (panel) {
        panel.classList.toggle("is-active", panel.dataset.panel === target);
      });
      navLinks.forEach(function (a) {
        const aTarget = a.textContent.trim().toLowerCase() === "info" ? "info" : "domains";
        if (aTarget === target) a.setAttribute("aria-current", "true");
        else a.removeAttribute("aria-current");
      });
    });
  });
})();

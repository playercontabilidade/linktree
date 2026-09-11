(function () {
  var KEY = "player-theme";

  function current() {
    var attr = document.documentElement.getAttribute("data-theme");
    if (attr === "light" || attr === "dark") return attr;
    return window.matchMedia("(prefers-color-scheme: light)").matches
      ? "light"
      : "dark";
  }

  function sync(button) {
    button.setAttribute("aria-pressed", current() === "light" ? "true" : "false");
  }

  var button = document.querySelector("[data-theme-toggle]");
  if (!button) return;

  sync(button);

  button.addEventListener("click", function () {
    window.__setTheme(current() === "light" ? "dark" : "light");
    sync(button);
  });

  // Segue o sistema enquanto o usuário não tiver escolhido explicitamente.
  var query = window.matchMedia("(prefers-color-scheme: light)");
  var onChange = function () {
    var saved = null;
    try { saved = localStorage.getItem(KEY); } catch (e) {}
    if (!saved) sync(button);
  };
  if (query.addEventListener) query.addEventListener("change", onChange);
})();

(function () {
  var config = window.APP_CONFIG || {
    ENV: "development",
    BASE_PATH: "",
    SITE_URL: "",
  };

  document.documentElement.dataset.env = config.ENV || "development";

  var year = document.querySelector("[data-year]");
  if (year) {
    year.textContent = String(new Date().getFullYear());
  }

  if (config.ENV !== "development") return;

  document.querySelectorAll(".link").forEach(function (link) {
    link.addEventListener("click", function () {
      var label = link.querySelector(".link__label");
      console.info(
        "[linktree]",
        label ? label.textContent.trim() : link.href,
        "→",
        link.href
      );
    });
  });
})();

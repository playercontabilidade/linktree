(function () {
  var config = window.APP_CONFIG || {
    ENV: "development",
    BASE_PATH: "",
    SITE_URL: "",
  };

  document.documentElement.dataset.env = config.ENV || "development";

  var links = document.querySelectorAll(".link");

  links.forEach(function (link) {
    link.addEventListener("pointerdown", function () {
      link.classList.add("is-pressed");
    });

    link.addEventListener("pointerup", function () {
      link.classList.remove("is-pressed");
    });

    link.addEventListener("pointerleave", function () {
      link.classList.remove("is-pressed");
    });

    link.addEventListener("click", function () {
      if (config.ENV === "development") {
        console.info("[linktree]", link.textContent.trim(), "→", link.href);
      }
    });
  });
})();

/* ============================================================
   NaijaCipe — main.js
   ============================================================ */

document.addEventListener("DOMContentLoaded", () => {
  /* ── Fix: Hide any modal backdrops ───────────────────────────── */
  const hideBackdrops = () => {
    document.querySelectorAll(".modal-backdrop").forEach((el) => {
      el.style.display = "none";
    });
  };
  hideBackdrops();

  /* ── Ensure page is always clickable ────────────────────────── */
  document.body.style.pointerEvents = "auto";
  document.body.style.filter = "none";

  /* ── Favourite button toggle ────────────────────────────── */
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";

  document.querySelectorAll(".fav-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      e.preventDefault();
      const slug = btn.dataset.slug;
      if (!slug) return;

      fetch(`/favourites/toggle/${slug}`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: `csrf_token=${encodeURIComponent(csrfToken)}`,
        redirect: "follow",
      }).then((response) => {
        if (response.url && response.url.includes("/login")) {
          window.location.href = "/login";
          return;
        }
        const icon = btn.querySelector("i");
        if (icon.classList.contains("bi-heart")) {
          icon.classList.replace("bi-heart", "bi-heart-fill");
          btn.style.color = "var(--naija-red)";
        } else {
          icon.classList.replace("bi-heart-fill", "bi-heart");
          btn.style.color = "";
        }
      }).catch(() => {
        window.location.href = `/recipes/${slug}`;
      });
    });
  });

  /* ── Auto-dismiss flash messages after 5 s ──────────────── */
  document.querySelectorAll(".alert.alert-dismissible").forEach((alert) => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 5000);
  });

  /* ── Active nav link highlighting (fallback) ────────────── */
  const currentPath = window.location.pathname;
  document.querySelectorAll(".navbar-naija .nav-link").forEach((link) => {
    if (link.getAttribute("href") === currentPath) {
      link.classList.add("active");
    }
  });

  /* ── Admin sidebar view toggle (admin.html includes its
        own inline script, but this acts as a safety fallback) #}
  ──────────────────────────────────────────────────────────── */
  document.querySelectorAll("[data-adminview-go]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const target = btn.dataset.adminviewGo;
      document.querySelectorAll(".admin-view").forEach((v) => {
        v.style.display = v.dataset.adminview === target ? "block" : "none";
      });
      document.querySelectorAll(".admin-link[data-adminview]").forEach((l) => {
        l.classList.toggle("active", l.dataset.adminview === target);
      });
    });
  });
});

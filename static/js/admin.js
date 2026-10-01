document.addEventListener("DOMContentLoaded", function () {
  const copyButtons = document.querySelectorAll(".copy-btn");

  copyButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      const link = button.dataset.link;
      const originalText = button.innerText;

      navigator.clipboard
        .writeText(link)
        .then(function () {
          button.innerText = "คัดลอกแล้ว";
          button.classList.add("copied");

          setTimeout(function () {
            button.innerText = originalText;
            button.classList.remove("copied");
          }, 2000);
        })
        .catch(function () {
          alert("ไม่สามารถคัดลอกลิงก์ได้");
        });
    });
  });


  const deleteForms = document.querySelectorAll(".delete-form");
  deleteForms.forEach(function (form) {
    form.addEventListener("submit", function (event) {
      const confirmed = confirm("คุณแน่ใจหรือไม่ว่าต้องการลบลิงก์นี้?\n\nข้อมูลสถิติทั้งหมดของลิงก์นี้จะถูกลบด้วย");
      if (!confirmed) {
        event.preventDefault();
      }
    });
  });

  let refreshCheckRunning = false;
  async function checkForUpdates() {
    if (refreshCheckRunning || document.hidden) {
      return;
    }
    const statsCount = document.getElementById("stats-visit-count");
    const dashboardLinkCount = document.getElementById("dashboard-link-count");
    const dashboardVisitCount = document.getElementById("dashboard-visit-count");
    const query = statsCount
      ? `?link_id=${encodeURIComponent(window.adminStatsLinkId)}`
      : "";
    refreshCheckRunning = true;
    try {
      const response = await fetch(`/api/admin/updates${query}`, {
        headers: { "Accept": "application/json" },
        cache: "no-store"
      });
      if (!response.ok) {
        return;
      }

      const currentCounts = await response.json();
      if (statsCount) {
        const currentVisitCount = Number(statsCount.textContent.trim().split(" ")[0]);
        if (currentCounts.visit_count !== currentVisitCount) {
          window.location.reload();
        }
      } else if (
        dashboardLinkCount &&
        dashboardVisitCount &&
        (currentCounts.link_count !== Number(dashboardLinkCount.textContent) ||
          currentCounts.visit_count !== Number(dashboardVisitCount.textContent))
      ) {
        window.location.reload();
      }
    } catch (error) {
      console.error("Auto-refresh check failed:", error);
    } finally {
      refreshCheckRunning = false;
    }
  }

  async function refreshLiveLocations() {
    if (!window.adminStatsLinkId || document.hidden) {
      return;
    }
    try {
      const linkId = encodeURIComponent(window.adminStatsLinkId);
      const response = await fetch(`/api/admin/live-locations/${linkId}`, {
        headers: { "Accept": "application/json" },
        cache: "no-store"
      });
      if (!response.ok) {
        return;
      }
      const liveLocations = await response.json();
      liveLocations.forEach(function (location) {
        const row = document.querySelector(`[data-visit-id="${location.id}"]`);
        if (!row) {
          return;
        }
        const coordinates = row.querySelector("[data-live-coordinates]");
        const status = row.querySelector("[data-live-status]");
        const mapLink = row.querySelector("[data-live-map]");
        const ipAddress = row.querySelector(".stats-ip");
        if (ipAddress && location.ip_address) {
          ipAddress.textContent = location.ip_address;
        }
        if (coordinates && location.latitude !== null && location.longitude !== null) {
          const accuracy = location.accuracy_meters === null ? "" : ` ±${Math.round(location.accuracy_meters)} เมตร`;
          coordinates.textContent = `${Number(location.latitude).toFixed(5)}, ${Number(location.longitude).toFixed(5)}${accuracy}`;
        }
        if (status) {
          status.classList.toggle("success", Boolean(location.is_sharing));
          status.classList.toggle("denied", !location.is_sharing);
          status.textContent = location.is_sharing ? "● กำลังแชร์ตำแหน่ง" : "● หยุดแชร์แล้ว";
        }
        if (mapLink && location.latitude !== null && location.longitude !== null) {
          mapLink.href = `https://maps.google.com/?q=${location.latitude},${location.longitude}`;
        }
      });
    } catch (error) {
      console.error("Live location refresh failed:", error);
    }
  }

  window.setInterval(checkForUpdates, 5000);
  window.setInterval(refreshLiveLocations, 3000);
});
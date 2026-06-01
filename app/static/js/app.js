/**
 * app.js — OHS Risk Prediction Platform
 * Auto-fills dependent dropdowns, shows char counter, manages submit state.
 */

document.addEventListener("DOMContentLoaded", () => {

  // ── Auto-fill NAICS Description ──────────────────────────────────────────
  const naicsSelect  = document.getElementById("primary_naics");
  const naicsDesc    = document.getElementById("naics_description");

  if (naicsSelect && naicsDesc) {
    naicsSelect.addEventListener("change", () => {
      const selected = naicsSelect.options[naicsSelect.selectedIndex];
      naicsDesc.value = selected.dataset.desc || "";
    });
  }

  // ── Auto-fill Regulation Name ─────────────────────────────────────────────
  const regSelect  = document.getElementById("act_reg_id");
  const regName    = document.getElementById("act_regulation_name");

  if (regSelect && regName) {
    regSelect.addEventListener("change", () => {
      const selected = regSelect.options[regSelect.selectedIndex];
      regName.value = selected.dataset.name || "";
    });
  }

  // ── Character Counter for Inspection Text ─────────────────────────────────
  const textArea  = document.getElementById("inspection_text");
  const charCount = document.getElementById("textCharCount");

  if (textArea && charCount) {
    const update = () => {
      const len = textArea.value.length;
      charCount.textContent = `${len} character${len !== 1 ? "s" : ""}`;
      charCount.style.color = len < 20 ? "#dc3545" : "#6c757d";
    };
    textArea.addEventListener("input", update);
    update();
  }

  // ── Submit Loading State ───────────────────────────────────────────────────
  const form        = document.getElementById("predictionForm");
  const submitBtn   = document.getElementById("submitBtn");
  const submitLabel = document.getElementById("submitLabel");
  const submitSpinner = document.getElementById("submitSpinner");

  if (form && submitBtn) {
    form.addEventListener("submit", (e) => {
      // Run HTML5 native validation first
      if (!form.checkValidity()) {
        e.preventDefault();
        form.classList.add("was-validated");
        // Scroll to first invalid field
        const firstInvalid = form.querySelector(":invalid");
        if (firstInvalid) {
          firstInvalid.scrollIntoView({ behavior: "smooth", block: "center" });
          firstInvalid.focus();
        }
        return;
      }
      // Show spinner
      submitLabel.classList.add("d-none");
      submitSpinner.classList.remove("d-none");
      submitBtn.disabled = true;
    });
  }

  // ── Risk Gauge Animation (results page) ──────────────────────────────────
  document.querySelectorAll(".risk-bar-animated").forEach((bar) => {
    const target = parseInt(bar.dataset.target, 10) || 0;
    setTimeout(() => {
      bar.style.width = `${target}%`;
    }, 300);
  });

  // ── Tooltips ─────────────────────────────────────────────────────────────
  const tooltipEls = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltipEls.forEach((el) => new bootstrap.Tooltip(el));

});

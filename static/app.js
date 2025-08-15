document.addEventListener("DOMContentLoaded", () => {
  const copyBtn = document.getElementById("copy-btn");
  const hiddenInput = document.getElementById("answer_md_input");
  const loader = document.getElementById("loader");

  if (copyBtn && hiddenInput) {
    copyBtn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(hiddenInput.value || "");
        copyBtn.textContent = "Скопировано ✓";
        setTimeout(() => (copyBtn.textContent = "Скопировать"), 1500);
      } catch (e) {
        alert("Не удалось скопировать: " + e);
      }
    });
  }

  const forms = document.querySelectorAll("form.show-loader");
  forms.forEach((f) => {
    f.addEventListener("submit", () => {
      f.querySelectorAll("button[type=submit]").forEach((b) => (b.disabled = true));
      if (loader) loader.classList.remove("hidden");
    });
  });
});

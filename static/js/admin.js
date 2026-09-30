document.addEventListener("DOMContentLoaded", function () {
  const copyButtons = document.querySelectorAll(".copy-btn");

  copyButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      const link = button.dataset.link;
      const originalText = button.innerText;

      navigator.clipboard
        .writeText(link)
        .then(function () {
          button.innerText = "✓ คัดลอกแล้ว";
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
      const confirmed = confirm(
        "คุณแน่ใจหรือไม่ว่าต้องการลบลิงก์นี้?\n\nข้อมูลสถิติทั้งหมดของลิงก์นี้จะถูกลบด้วย"
      );

      if (!confirmed) {
        event.preventDefault();
      }
    });
  });
});
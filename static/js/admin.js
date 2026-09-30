function copyToClipboard(text, btnElement) {
navigator.clipboard
.writeText(text)
.then(() => {
const originalText = btnElement.innerText;
btnElement.innerText = "คัดลอกแล้ว!";
btnElement.style.backgroundColor = "#22c55e";
  setTimeout(() => {
    btnElement.innerText = originalText;
    btnElement.style.backgroundColor = "#0ea5e9";
  }, 2000);
})
.catch((err) => {
  alert("ไม่สามารถคัดลอกลิงก์ได้");
});
}

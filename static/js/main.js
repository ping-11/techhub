// 下拉菜单
function toggleMenu() {
  const menu = document.getElementById('dropMenu');
  menu?.classList.toggle('open');
}
document.addEventListener('click', (e) => {
  if (!e.target.closest('.avatar-menu')) {
    document.getElementById('dropMenu')?.classList.remove('open');
  }
});

// Flash 消息自动消失
setTimeout(() => {
  document.querySelectorAll('.flash').forEach(el => el.remove());
}, 5000);

// 表单提交防重复点击
document.querySelectorAll('form').forEach(form => {
  form.addEventListener('submit', () => {
    const btn = form.querySelector('button[type=submit]');
    if (btn) { btn.disabled = true; btn.style.opacity = '0.6'; }
  });
});

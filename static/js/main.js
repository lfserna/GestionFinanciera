document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', () => {
      const btn = form.querySelector('button[type="submit"],input[type="submit"]');
      if (btn) setTimeout(() => btn.disabled = true, 50);
    });
  });
  const alertsModal = document.getElementById('alertsModal');
  if (alertsModal && alertsModal.dataset.show === '1') new bootstrap.Modal(alertsModal).show();
  const changePasswordModal = document.getElementById('changePasswordModal');
  if (changePasswordModal && changePasswordModal.dataset.force === '1') new bootstrap.Modal(changePasswordModal, {backdrop:'static', keyboard:false}).show();
});

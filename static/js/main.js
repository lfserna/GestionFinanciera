document.addEventListener('DOMContentLoaded', () => {
  function formatCentsFromDigits(digits) {
    digits = (digits || '').replace(/\D/g, '');
    if (!digits) digits = '0';
    digits = String(parseInt(digits, 10) || 0);
    const cents = digits.padStart(3, '0');
    const whole = cents.slice(0, -2);
    const decimal = cents.slice(-2);
    return `${whole}.${decimal}`;
  }

  function setupMoneyInputs() {
    document.querySelectorAll('.gf-money-input').forEach(input => {
      input.setAttribute('type', 'text');
      input.setAttribute('inputmode', 'numeric');
      input.setAttribute('autocomplete', 'off');

      const initialDigits = (input.value || '').replace(/\D/g, '');
      input.dataset.moneyDigits = initialDigits || '0';
      input.value = formatCentsFromDigits(input.dataset.moneyDigits);

      input.addEventListener('focus', () => {
        setTimeout(() => input.select(), 0);
      });

      input.addEventListener('keydown', event => {
        const allowedKeys = ['Tab', 'ArrowLeft', 'ArrowRight', 'Home', 'End'];
        if (allowedKeys.includes(event.key)) return;

        if (event.ctrlKey || event.metaKey) return;

        event.preventDefault();

        let digits = input.dataset.moneyDigits || '';
        if (/^\d$/.test(event.key)) {
          digits = (digits + event.key).replace(/^0+(?=\d)/, '');
        } else if (event.key === 'Backspace' || event.key === 'Delete') {
          digits = digits.slice(0, -1) || '0';
        } else {
          return;
        }

        input.dataset.moneyDigits = digits;
        input.value = formatCentsFromDigits(digits);
      });

      input.addEventListener('paste', event => {
        event.preventDefault();
        const pasted = (event.clipboardData || window.clipboardData).getData('text') || '';
        let digits = pasted.replace(/\D/g, '');
        if (!digits) digits = '0';
        input.dataset.moneyDigits = digits.replace(/^0+(?=\d)/, '') || '0';
        input.value = formatCentsFromDigits(input.dataset.moneyDigits);
      });

      input.addEventListener('blur', () => {
        input.value = formatCentsFromDigits(input.dataset.moneyDigits || input.value);
      });
    });
  }

  setupMoneyInputs();

  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', event => {
      if (form.dataset.submitting === '1') {
        event.preventDefault();
        return false;
      }

      document.querySelectorAll('.gf-money-input').forEach(input => {
        input.value = formatCentsFromDigits(input.dataset.moneyDigits || input.value);
      });

      form.dataset.submitting = '1';
      const btn = form.querySelector('button[type="submit"],input[type="submit"]');
      if (btn) {
        btn.disabled = true;
        if (btn.tagName === 'BUTTON') {
          btn.dataset.originalText = btn.innerHTML;
          btn.innerHTML = 'Guardando...';
        }
      }
    });
  });

  const alertsModal = document.getElementById('alertsModal');
  if (alertsModal && alertsModal.dataset.show === '1') new bootstrap.Modal(alertsModal).show();
  const changePasswordModal = document.getElementById('changePasswordModal');
  if (changePasswordModal && changePasswordModal.dataset.force === '1') new bootstrap.Modal(changePasswordModal, {backdrop:'static', keyboard:false}).show();
});

// ShopKart Main JavaScript
document.addEventListener('DOMContentLoaded', function () {

  // Auto-dismiss toast messages after 4 seconds
  const toasts = document.querySelectorAll('.sk-toast');
  toasts.forEach((toast, i) => {
    setTimeout(() => {
      toast.style.animation = 'slideOut 0.3s ease forwards';
      setTimeout(() => toast.remove(), 300);
    }, 4000 + i * 500);
  });

  // Add slide-out animation style
  const style = document.createElement('style');
  style.textContent = '@keyframes slideOut{to{transform:translateX(120px);opacity:0}}';
  document.head.appendChild(style);

  // Quantity validation in cart
  document.querySelectorAll('.sk-qty-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      const form = this.closest('form');
      if (form) form.submit();
    });
  });

  // Checkout form validation
  const checkoutForm = document.getElementById('checkoutForm');
  if (checkoutForm) {
    checkoutForm.addEventListener('submit', function (e) {
      const phone = this.querySelector('[name="phone"]');
      if (phone && !/^[6-9]\d{9}$/.test(phone.value.trim())) {
        e.preventDefault();
        showAlert('❌ Enter a valid 10-digit Indian mobile number!', 'error');
        phone.focus();
        return;
      }
      const pincode = this.querySelector('[name="pincode"]');
      if (pincode && !/^\d{6}$/.test(pincode.value.trim())) {
        e.preventDefault();
        showAlert('❌ Pincode must be 6 digits!', 'error');
        pincode.focus();
        return;
      }
    });
  }

  // Register form password match check
  const registerForm = document.getElementById('registerForm');
  if (registerForm) {
    const p1 = registerForm.querySelector('[name="password1"]');
    const p2 = registerForm.querySelector('[name="password2"]');
    if (p2) {
      p2.addEventListener('input', function () {
        if (this.value && p1.value !== this.value) {
          this.style.borderColor = '#ff6584';
        } else {
          this.style.borderColor = '';
        }
      });
    }
  }

  // Add to cart animation (quick feedback)
  document.querySelectorAll('a[href*="/cart/add/"]').forEach(btn => {
    btn.addEventListener('click', function (e) {
      const icon = this.querySelector('i');
      if (icon) {
        icon.className = 'bi bi-check-circle-fill';
        setTimeout(() => { icon.className = 'bi bi-cart-plus'; }, 1500);
      }
    });
  });

  // Price filter — auto-submit after delay
  const priceInputs = document.querySelectorAll('[name="min_price"], [name="max_price"]');
  let priceTimer;
  priceInputs.forEach(inp => {
    inp.addEventListener('input', () => {
      clearTimeout(priceTimer);
    });
  });

  // Smooth scroll to sections
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', function (e) {
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
});

function showAlert(message, type) {
  const container = document.querySelector('.sk-toast-container') || createToastContainer();
  const toast = document.createElement('div');
  toast.className = `sk-toast sk-toast-${type}`;
  toast.innerHTML = `${message}<button onclick="this.parentElement.remove()" class="sk-toast-close">&times;</button>`;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

function createToastContainer() {
  const div = document.createElement('div');
  div.className = 'sk-toast-container';
  document.body.appendChild(div);
  return div;
}

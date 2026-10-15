const navToggle = document.querySelector('.nav-toggle');
const siteNav = document.getElementById('site-nav');
if (navToggle && siteNav) {
  navToggle.addEventListener('click', () => {
    const open = siteNav.classList.toggle('is-open');
    navToggle.classList.toggle('is-open', open);
    navToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    navToggle.setAttribute('aria-label', open ? 'Close menu' : 'Menu');
  });
  siteNav.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      siteNav.classList.remove('is-open');
      navToggle.classList.remove('is-open');
      navToggle.setAttribute('aria-expanded', 'false');
      navToggle.setAttribute('aria-label', 'Menu');
    });
  });
}

const io = new IntersectionObserver((entries) => entries.forEach((entry) => {
  if (entry.isIntersecting) {
    entry.target.classList.add('in');
    io.unobserve(entry.target);
  }
}), { threshold: .1 });
document.querySelectorAll('.reveal').forEach((el) => io.observe(el));

const consultForm = document.getElementById('consult-form');
const formStatus = document.getElementById('form-status');
if (consultForm && formStatus) {
  consultForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const submit = consultForm.querySelector('button[type="submit"]');
    submit.disabled = true;
    formStatus.textContent = 'Sending…';
    try {
      const response = await fetch(consultForm.action, {
        method: 'POST',
        headers: {
          Accept: 'application/json',
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams(new FormData(consultForm)),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok || !payload.ok) {
        throw new Error(payload.error || 'The booking service did not accept the form. Reload the page and try again.');
      }
      consultForm.reset();
      formStatus.textContent = 'Request received. We will reply by email.';
    } catch (error) {
      formStatus.textContent = error.message || 'Please try again, or email info@richardwinfred.com.';
    } finally {
      submit.disabled = false;
    }
  });
}

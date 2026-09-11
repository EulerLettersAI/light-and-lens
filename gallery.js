document.querySelectorAll('[data-copy-attribution]').forEach(button => {
  button.addEventListener('click', async () => {
    const card = button.closest('.photo-card');
    const text = card.querySelector('.attribution p').textContent;
    const status = card.querySelector('.copy-status');
    try {
      await navigator.clipboard.writeText(text);
      status.textContent = 'Attribution copied.';
    } catch {
      card.querySelector('.attribution').open = true;
      status.textContent = 'Please select and copy the attribution shown above.';
    }
  });
});

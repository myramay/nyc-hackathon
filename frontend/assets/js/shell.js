// Presentation only: switches List / Map previews. No data, no API calls yet.
document.querySelectorAll('[data-toggle]').forEach(group => {
  const buttons = group.querySelectorAll('button[data-view]');
  buttons.forEach(b => b.addEventListener('click', () => {
    buttons.forEach(x => x.setAttribute('aria-selected', String(x === b)));
    document.querySelectorAll(`[data-panel-for="${group.dataset.toggle}"]`).forEach(p => { p.hidden = p.dataset.view !== b.dataset.view; });
  }));
});

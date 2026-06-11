(function(){
  const searchInput = document.getElementById('search');
  const statusFilter = document.getElementById('filter-status');
  if (!searchInput) return;

  function filter() {
    const q = searchInput.value.toLowerCase();
    const status = statusFilter ? statusFilter.value : '';
    document.querySelectorAll('.card').forEach(card => {
      const text = card.textContent.toLowerCase();
      const badgeEl = card.querySelector('.badge');
      const badgeClass = badgeEl ? badgeEl.className : '';
      const matchQ = !q || text.includes(q);
      const matchS = !status || badgeClass.includes(status);
      card.style.display = (matchQ && matchS) ? '' : 'none';
    });
  }

  searchInput.addEventListener('input', filter);
  if (statusFilter) statusFilter.addEventListener('change', filter);
})();
